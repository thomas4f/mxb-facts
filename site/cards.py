"""The cards: checking one card file (cards/*.yaml) against the rules and working out what the rules set on it (its answers
as lines, their costs, its key answers, its corrections). No page is made here: feed.py makes the data feed from the result,
and render.py the pages from the feed. Also the data beside the cards: the registry (registry/*.json) and the VirusTotal
lookups (vt/results.json).
"""
import datetime, json, jsonschema, os, re, subprocess, urllib.parse
from rules import (
    ANS, AREAN, DNA, HEADER, HELD, KEYS, KMODE, KNAMES, NOPARTLY, ONREQ, QIDS, QMARK, QTXT, RANK, ROOT, SECOND,
    SCHEMA, SECTIONS, SYM, WITHHELD_EV, WITHHELD_LIM, ans_md, charges, concern_span, heldq, money, verdict, withheld_error)
def glance(A,G,held=()):
    # What each area shows: a scored area's score (rules/scores.md), and the Money label from M1 and M2. A tool that isn't
    # scored, or shows signs of malware, gets no numbers at all, its areas included.
    return {ar:(('–' if G['kind'] in ('notscored','malware') else G['areas'][ar][0]) if ar in G['areas'] else money(A,held)) for ar in AREAN}
def key_answers(f,d,rows,A,SETS,held):
    # The ten key answers: (mark, short answer, whole answer, how a Concern shows). The card writes the answer; its mark comes
    # from the answers it is built from (rules/questions.md), never from the card.
    out={}
    for k,_q,_s,src in KEYS:
        ans=d['key'][k]
        assert not ans.startswith('{'), f+': '+k+': leave out the mark, the build sets it from '+', '.join(src)
        marks=[rows[i][1] for i in src if rows[i].startswith('{')]
        # Rule 9: a key question with a held-back source that is unanswered, or that would come out Good, shows "Held back" and nothing more, with no mark,
        # so the other sources can't make it look Good. A held source that is already a Concern keeps the key answer's mark.
        best=(max if KMODE[k]=='Strongest' else min)(marks,key=RANK.get) if marks else None
        if held & set(src) and (best in (None,'+') or any(not rows[i].startswith('{') for i in held & set(src))):
            assert ans=='Held back (rule 9)', f+': '+k+': a source is held back, so it reads only "Held back (rule 9)"'
            mk=None
        elif marks: mk=best
        else:
            assert re.match(r'Not (checked|allowed)\. ',ans), f+': '+k+': its sources carry no mark, so it starts "Not checked." or "Not allowed."'
            mk=None
        # A source the key question must name (scoring.yaml, names): while it is a Concern by default, the answer says so in those words.
        for q,w in KNAMES[k].items():
            assert not (A[q][0]=='!' and A[q][1] in ('Yes','No','Partly')) or w in ans.lower(), f+': '+k+': '+q+' is a Concern, so the answer must say "'+w+'"'
        head=re.match(r'[^.;]+',ans).group(0)
        assert len(head)<=24, f+': '+k+': the first part, before "." or ";", is the short answer and must fit 24 characters'
        # A Concern key answer shows the costliest of its Concern sources, like the answers, lines and rows do.
        out[k]=(mk,head,ans,concern_span([i for i in src if A[i][0]=='!'],A,SETS,None)[1] if mk=='!' else None)
    return out
def answer_rows(f,d,held):
    # Every answer as one line: its mark, verdict and text ({question: line}), in the order the areas show them, checked
    # against the rules.
    rows={}
    missing=[q for q in QIDS if q not in d['answers']]; extra=[q for q in d['answers'] if q not in QTXT]
    assert not missing, f+': unanswered '+', '.join(missing)
    assert not extra, f+': unknown question '+', '.join(extra)
    for i in [q for k in SECTIONS.values() if k for q in QIDS if q[0]==k]:
        x=d['answers'][i]; ev=x['evidence']
        e=withheld_error(i,x); assert not e, f+': '+e
        # Rule 9: an answer the "Held back" row names says so on its own line too, so its verdict isn't read as the whole story.
        ans=ans_md(x)+('' if i not in held or x['text'].startswith('Held back') else ' An item on this question is held back (rule 9); it counts at its highest cost until it is published.')
        assert ANS.match(ans), f+': '+i+' answer must start with a mark and Yes, "Yes, not by default.", "Yes, on request.", No or Partly, or with "Not checked.", "Not allowed." or "Doesn\'t apply." and the reason'
        assert not (i in NOPARTLY and ans[4:].startswith('Partly')), f+': '+i+' has no Partly (see questions.md)'
        assert not (ans.startswith("Doesn't apply") and i not in DNA), f+': '+i+' can\'t be answered "Doesn\'t apply"'
        assert ev.strip() and (ev.strip()!='-' or ans.startswith('Not ')), f+': '+i+' has no evidence'
        mv=re.match(r'\{(.)\} (Yes|No|Partly)\b',ans)
        if mv: assert mv.group(1) in QMARK[i][mv.group(2)], f+': '+i+' '+mv.group(2)+' can\'t be marked {'+mv.group(1)+'} (see the Yes and No columns in questions.md)'
        if i in ONREQ and ans[4:].startswith('Yes'): assert (ans[1]=='~')==ans[4:].startswith('Yes, on request'), f+': '+i+' is a Note when the answer is "Yes, on request", and a Concern for any other Yes'
        assert not re.fullmatch(r'`?(strings|objdump|file|source|readme|manual|changelog)`?\.?',ev.strip(),re.I), f+': '+i+' evidence names only a tool or a file kind; say which file and what it finds, so anyone can repeat it'
        # Rule 1: every answer links its evidence (a pinned link, or a file in this repository: a run's evidence, or the
        # output of the commands it names, from lab/evidence/<card>/run.sh), and a line that names a command links its output.
        if not ans.startswith(('Not ',"Doesn't")) and ev.strip()!=WITHHELD_EV:
            assert re.search(r'https://|lab/',ev), f+': '+i+' links no evidence; link the code, or the output of the command it names (lab/evidence/)'
            assert not re.search(CMDS,ev) or 'lab/' in ev, f+': '+i+' names a command; link its output (lab/evidence/<card>/run.sh)'
        rows[i]=ans
    return rows
# A line that names one of these commands links the command's output.
CMDS=r'objdump|`strings|strings -el|`file`|git log|git grep|[Ss]earch|`diff`|7-Zip'
# The verdicts an answer can have: the schema's list, each of which verdict() and the checks below know.
assert SCHEMA['$defs']['answer']['properties']['verdict']['enum']==['Yes','Yes, not by default','Yes, on request','No','Partly','Not checked','Not allowed',"Doesn't apply"] and SCHEMA['$defs']['answer']['properties']['mark']['enum']==list(SYM), 'card.schema.json: the verdicts or marks changed; teach site/build.py (verdict(), ANS) the new ones'
def check_files(d):
    top=[x for x in d['files'] if 'inside' not in x]
    assert all(any(k.get('inside')==x['name'] for x in top) for k in d['files'] if 'inside' in k), 'files: "inside" must name a file listed without "inside"'
def files_table(f,d):
    # Files checked as table rows (File, Inside, SHA-256, VirusTotal, Note; each cell card Markdown): one row per file, files inside a download right after it, with the latest VirusTotal lookup (vt/results.json).
    vt=VT.get(f,{})
    def cell(h):
        r=vt.get(h)
        if not r: return 'Not looked up'
        if r.get('error'): return 'Lookup failed'
        if not r.get('found'): return 'Not on VirusTotal'+(f' (uploaded {r["uploaded"]}, scan pending)' if r.get('uploaded') else '')
        return f'[{r["flagged"]} of {r["engines"]}]({r["permalink"]})'
    rows=[]
    for x in [x for x in d['files'] if 'inside' not in x]:
        for y in [x]+[k for k in d['files'] if k.get('inside')==x['name']]:
            name=f'`{y["name"]}`' if y['name']!='Zip' else 'Zip'
            rows.append((name,f'`{y["inside"]}`' if y.get('inside') else '-',f'`{y["sha256"]}`',cell(y["sha256"]),y.get("note","")))
    return rows
# The name a table in an area section is folded under, by its columns.
FOLDNAME={('What','Where to','When','Switch'):'Connections found',('What','Where in the game','When'):'Changes to the game found'}
LIMS={}
REPO='https://github.com/thomas4f/mxb-facts/'
try: COMMIT=subprocess.run(['git','-C',ROOT,'rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
except (OSError,subprocess.CalledProcessError): COMMIT=''
assert re.fullmatch(r'[0-9a-f]{40}',COMMIT), 'site/build.py needs the repository\'s git history, for the commit that test-host evidence and the For authors check point at'
CORRFORM=REPO+'issues/new?template=correction.yml'
REQFORM=REPO+'issues/new?template=analyse-tool.yml'  # a request to analyse a tool, or to re-check a new release
SITEURL='https://thomas4f.github.io/mxb-facts/'
# Open corrections per card: question -> issue numbers. While one is open, each answer it names shows a neutral marker; nothing else moves.
CORR={}
def correction_link(card,q,ans=''):
    # The comment form (.github/ISSUE_TEMPLATE/correction.yml) filled in from the link: its "card" field, the title, and the
    # "answer" field with the question and the answer as the card gives it now (mark in words, links as "text (url)"),
    # cut at 1500 characters so the link stays well inside what GitHub accepts.
    a=re.sub(r'^\{([+~!])\} ',lambda m:{'+':'Good','~':'Note','!':'Concern'}[m.group(1)]+': ',ans)
    a=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'\1 (\2)',a).replace('`','')
    if len(a)>1500: a=a[:1497].rsplit(' ',1)[0]+'…'
    return CORRFORM+'&'+urllib.parse.urlencode({'title':f'Comment: {card} {q}','card':card,'line':f'{q}: {QTXT[q]}'+(f'\n\nThe answer now: {a}' if a else '')})
CORRTIP='A comment about this answer is under review. Nothing on the card changes until it is decided.'
CKIND={'correction':'Correction','missing':'Something missing','context':'Author\'s context'}
def corrections_md(f,d):
    # The card's Corrections section (rules/template.md, "Sections"): every correction sent about it, and how to send one.
    cs=d.get('corrections',[]); CORR[f]={}
    day=lambda x: datetime.datetime.strptime(x,'%d %b %Y').date()
    assert len({c['issue'] for c in cs})==len(cs), f+': a correction is listed twice'
    out=[]
    for c in cs:
        n=c['issue']; qs=', '.join('{q:'+q+'}' for q in c['questions'])
        assert all(q in QIDS for q in c['questions']), f+': correction #'+str(n)+' names an unknown question'
        link=f'{CKIND[c.get("kind","correction")]} [#{n}]({REPO}issues/{n})'
        if c['status']=='open':
            assert 'closed' not in c and 'reason' not in c, f+': correction #'+str(n)+' is open, so it has no "closed" date or "reason" yet'
            for q in c['questions']: CORR[f].setdefault(q,[]).append(n)
            out.append(f'- <span class="mark corr">Under review</span> {link}, sent {c["opened"]}, about {qs}. Nothing on the card changes until it is decided.')
        else:
            assert c.get('closed') and c.get('reason'), f+': correction #'+str(n)+' is '+c['status']+', so it needs the "closed" date and a "reason"'
            assert day(c['closed'])>=day(c['opened']), f+': correction #'+str(n)+' is closed before it was sent'
            # A comment that changes the card ("fixed") has its history row, linking the issue; "noted" changes nothing.
            if c['status']=='fixed': assert any(f'issues/{n})' in r['change'] for r in d['history']), f+': correction #'+str(n)+' is fixed, so a Card history row links its issue'
            out.append(f'- {link}, about {qs}: {c["status"]} on {c["closed"]}. {c["reason"]}')
    out.append(('' if out else 'No correction has been sent about this card. ')+f'Something wrong, missing, or context to add? [Comment on an answer]({CORRFORM}), with its evidence; it shows here, and on the answer it names, until it is decided. If you made this tool, see [For authors](#authors).')
    return '\n'.join(out[:-1])+('\n\n' if len(out)>1 else '')+out[-1]
def no_html(f,d,p='card'):
    # Card text is Markdown without HTML, and its links go to https addresses: it comes partly from releases and authors'
    # pages, and a tag or a javascript: link in it would reach the page as it stands. Inside `code`, < is shown as text.
    if isinstance(d,dict): [no_html(f,v,p+'.'+str(k)) for k,v in d.items()]
    elif isinstance(d,list): [no_html(f,v,f'{p}[{i}]') for i,v in enumerate(d)]
    elif isinstance(d,str):
        t=re.sub(r'`[^`]*`','',d); m=re.search(r'<[A-Za-z/!?]',t)
        # An image would load from another site on every visit; card text has none.
        assert '![' not in t, f+': '+p+' holds a Markdown image ("'+t[t.index('!['):t.index('![')+30]+'"); cards link, they don\'t embed'
        assert not m, f+': '+p+' holds HTML ("'+t[m.start():m.start()+30]+'"); put it in `code`, or write &lt;'
        bad=[u for u in re.findall(r'\]\(([^)\s]*)',t) if not u.startswith('https://')]
        # A reference-style link ([text][ref] with "[ref]: address" on its own line) would slip past the check above.
        bad+=re.findall(r'(?m)^\s{0,3}\[[^\]]+\]:\s*\S+',t)
        assert not bad, f+': '+p+' links somewhere other than an https address: '+', '.join(bad)
def linked(f,d):
    # The card with every path into lab/ turned into a link (lablinks), for everything that is shown.
    if isinstance(d,dict): return {k:linked(f,v) for k,v in d.items()}
    if isinstance(d,list): return [linked(f,v) for v in d]
    return lablinks(f,d) if isinstance(d,str) else d
def strings(d):
    # Every piece of text a card holds.
    if isinstance(d,dict): return [s for v in d.values() for s in strings(v)]
    if isinstance(d,list): return [s for v in d for s in strings(v)]
    return [d] if isinstance(d,str) else []
def check_card(f,raw):
    # One card, checked against the schema and the rules, with what the rules work out from it: its answers as lines
    # ("rows"), their verdicts ("A") and costs ("SETS"), the held-back questions and the key answers. Nothing here is HTML:
    # feed.py makes the feed from this.
    jsonschema.validate(raw,SCHEMA); no_html(f,raw)
    check_files(raw)
    assert not set(raw['header'])-set(HEADER), f+': unknown header rows '+', '.join(set(raw['header'])-set(HEADER))
    # A Yes on a question with second_check (rules/scoring.yaml) is confirmed by a second check with another method, named
    # with its evidence; only such an answer has one.
    for q,x in raw['answers'].items():
        assert ('second_check' in x)==(q in SECOND and x['verdict'].startswith('Yes')), f+': '+q+(' has a second check, which only a Yes on '+', '.join(sorted(SECOND))+' takes' if 'second_check' in x else ' Yes needs its second check (another method, with its evidence)')
        if 'second_check' in x:
            # The second check links its own evidence, like any answer, and not only what the first one linked.
            sc=x['second_check']; links=set(re.findall(r'https://\S+|lab/[^\s`;,)]+',sc))
            assert links, f+': '+q+' second check links no evidence; link the code, the run or the command output (lab/evidence/) it rests on'
            assert links-set(re.findall(r'https://\S+|lab/[^\s`;,)]+',x.get('evidence',''))), f+': '+q+' second check links only the first check\'s evidence; a second check uses another method, with its own evidence'
            assert not re.search(CMDS,sc) or 'lab/' in sc, f+': '+q+' second check names a command; link its output (lab/evidence/<card>/run.sh)'
    d=linked(f,raw); h=d['header']
    # Rule 9: an item held back from the card names its questions. Its dates (author told, 30 days at most) are kept
    # privately by the maintainer, not in the repository, so the build doesn't read them.
    assert not h.get('Held back') or re.match(HELD,h['Held back']), f+': "Held back" must read "<n> item(s) (rule 9): <question IDs>"'
    held=heldq(h.get('Held back'))
    rows=answer_rows(f,d,held)
    for q in held: assert q in rows and not rows[q].startswith('{+}'), f+': '+q+' is touched by a held-back item, so it can\'t be Good'
    A={q:verdict(rows[q]) for q in rows}; SETS=charges(A,held)
    sec={s['title']:s['blocks'] for s in d['sections']}
    assert not set(sec)-set(SECTIONS), f+': unknown sections '+', '.join(set(sec)-set(SECTIONS))
    # Limits of this analysis: only "limits" blocks there, and only there; each names real questions, and each answer it names links back to it.
    assert all(('limits' in b)==(s['title']=='Limits of this analysis') for s in d['sections'] for b in s['blocks']), f+': "Limits of this analysis" holds only limits blocks, and limits blocks go only there'
    LIMS[f]={}
    assert len(sec.get('Limits of this analysis',[]))<=1, f+': "Limits of this analysis" is one limits block'
    for b in sec.get('Limits of this analysis',[]):
        for n,x in enumerate(b['limits']):
            assert len(set(x['questions']))==len(x['questions']), f+': limit '+str(n+1)+' names a question twice'
            for q in x['questions']:
                assert q in QIDS, f+': a limit names the unknown question '+q
                # Rule 9: a limit doesn't point at a held-back question; the "Held back" row says all there is to say.
                assert q not in held, f+': limit '+str(n+1)+' names '+q+', which is held back (rule 9)'
                LIMS[f].setdefault(q,[]).append(n)
    # Rule 9, protected content: a card that withholds how a tool gets at it says so once under Limits, naming no question.
    wq=[q for q,x in d['answers'].items() if x['evidence'].strip()==WITHHELD_EV]
    wl=[x for b in sec.get('Limits of this analysis',[]) for x in b['limits'] if x['text'].rstrip().endswith(WITHHELD_LIM)]
    assert bool(wq)==bool(wl), f+(': '+', '.join(wq)+' withholds the how, so one limit ends "'+WITHHELD_LIM+'"' if wq else ': a limit says something is withheld, but no answer withholds it')
    assert len(wl)<=1 and not any(x['questions'] for x in wl), f+': the "withheld" limit is one line and names no question'
    for title,k in SECTIONS.items():
        for b in sec.get(title,[]):
            if 'table' in b:
                assert all(set(r)-{'mark','questions'}==set(b['table']) for r in b['rows']), f+': a table row has other columns than '+', '.join(b['table'])
                assert not k or tuple(b['table']) in FOLDNAME, f+': no fold name for a table with columns '+', '.join(b['table'])+' (add one to FOLDNAME)'
            # A Concern line or table row sits in an area section and names the answers it backs; it shows the costliest of them.
            for x in b.get('rows',[b]):
                if x.get('mark')!='concern':
                    assert 'questions' not in x, f+': only a Concern line names questions'
                    continue
                assert k, f+': a Concern line goes in an area section'
                qs=x.get('questions',[])
                assert qs, f+': a Concern line or row names the questions it backs ('+(x.get('text') or x.get('What',''))[:50]+')'
                assert all(q in QIDS for q in qs) and len(set(qs))==len(qs), f+': a Concern line names an unknown question, or one twice: '+', '.join(qs)
                assert concern_span(qs,A,SETS,k), f+': a Concern line backs only answers that aren\'t Concerns: '+', '.join(qs)
    return {'f':f,'raw':raw,'d':d,'h':h,'name':d['tool'],'ver':d['version'],'rows':rows,'A':A,'SETS':SETS,'held':held,'sections':sec,
            'key':key_answers(f,d,rows,A,SETS,held),'corrections':corrections_md(f,d)}
def lablinks(f,t):
    # Evidence from the test host is named by its path in this repository; the build checks it exists and links it at
    # the commit the site is built from, so the link keeps showing that file as it was.
    def one(m):
        p=m.group(1)
        assert os.path.exists(ROOT+p), f+': evidence '+p+' is not in the repository'
        return f'[`{p}`]({REPO}{"tree" if os.path.isdir(ROOT+p) else "blob"}/{COMMIT}/{p.rstrip("/")})'
    return re.sub(r'(?<!\[)`(lab/[^`\s]+)`',one,t)
REG=json.load(open(ROOT+'registry/tools.json'))
VT=json.load(open(ROOT+'vt/results.json'))['cards']
JUDGE=r'\b(safe|unsafe|spyware|malicious|shady|sketchy|trustworthy|untrustworthy|dangerous|harmful|scam|scammy|legit|sneaky|dodgy|creepy|invasive)\b'
# Each game's mods site: the registry key, its snapshot and the card's header row.
SITES={'MX Bikes':('mxb-mods','mxb-mods.com'),'GP Bikes':('gpb-mods','gpb-mods.com')}
MM={k:json.load(open(ROOT+'registry/'+k+'.json')) for k,_ in SITES.values()}
def games(h): return h['Game'].split('; ')  # the games a card's Game row names, MX Bikes first
SLUG={c:s for s,e in REG.items() for c in e['cards']}
def esc(s): return s.replace('&','&amp;').replace('"','&quot;').replace('<','&lt;')
