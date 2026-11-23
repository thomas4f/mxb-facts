"""The page: HTML for the tools list, each tool's page, the badges, the How it works and For authors views.

Everything here turns checked card data (cards.py) and the rules (rules.py) into HTML; it decides no mark or score.
"""
import json, markdown, math, re
from rules import (
    AREAK, AREAN, CONCERN, D, GCOST, GCOVER, GT, HEADER, HELD, KEYS, MDTXT, MLAB, MLEFT, PFX, PMEANS, QCELL, QIDS, QTXT, ROOT, RUBRICV, SC,
    SCHEMA, SECTIONS, STATES, ans_md, concern_span, gsym, gtext, load_yaml, maxcost, qcost, scored, state_html, state_of, tagsof, verdict)
from icons import group as icon_group
from cards import COMMIT, CORR, CORRTIP, FOLDNAME, LIMS, MM, REG, REPO, SITES, SLUG, correction_link, esc, files_table
# The hint beside every score: one text and one style (.gnote), on the line of the tools list's heading (shell.html, {{GNOTE}})
# and of each tool page's Score heading, where it keeps the score box level with Key findings beside it.
GNOTE='Scores are out of 100; higher is better.'
# The notice on the page of a tool made by the person who runs MXB Facts (a card's by_maintainer).
MAINT=('<p class="maint"><strong>Made by the maintainer of MXB Facts.</strong> thomas4f, who runs this project, makes this tool. '
       'It is analysed from the same prompt, answers the same questions and is scored by the same fixed costs as every other tool, '
       'and every line links its evidence, so you can check it yourself '
       '(<a href="https://github.com/thomas4f/mxb-facts#conflict-of-interest">conflict of interest</a>).</p>')

def post(h,anchor):
    # What every piece of a tool's page gets after its Markdown is HTML: links open in a new tab, {+} {~} {!} become marks,
    # and {lim:n} and {q:ID} (blocks() writes them) become the tool's own links.
    h=h.replace('<a href="http','<a target="_blank" rel="noopener" href="http')
    # Card text that names the "What it says vs what it does" section links it.
    h=h.replace('"What it says vs what it does"',f'<a href="#r-{anchor}-says">What it says vs what it does</a>')
    MK={'+':'good','~':'note','!':'concern'}
    h=re.sub(r'\{([+~!])\} ?', lambda m:state_html(MK[m.group(1)])+' ', h)
    h=re.sub(r'<li>\{lim:(\d+)\} ',lambda m:f'<li id="lim-{anchor}-{m.group(1)}">',h)
    return re.sub(r'\{q:([A-Z]\d+)\}',lambda m:f'<a href="#q-{anchor}-{m.group(1)}">{m.group(1)}</a>',h)
def md(t,anchor):
    # A block of card text (paragraphs, a list) from Markdown to HTML.
    return post(markdown.markdown(t),anchor)
_CELL={}
def cell(s):
    # One piece of card text (Markdown: code, bold, links) as HTML with no paragraph around it, as a table cell holds it.
    if s not in _CELL:
        h=markdown.markdown('| |\n|---|\n| '+s+' |',extensions=['tables']) if s.strip() else '<td></td>\n</tr>'
        m=re.search(r'<td>(.*)</td>\n</tr>',h,re.S)
        assert m and '</td>' not in m.group(1), 'card text that can\'t sit in one table cell (a "|" outside code, or a line break): '+s[:60]
        _CELL[s]=m.group(1)
    return _CELL[s]
def table(head,rows,cls=''):
    # A table from cells that are already HTML, laid out as Markdown's tables are.
    return (f'<div class="tw{cls}"><table>\n<thead>\n<tr>\n'+''.join(f'<th>{c}</th>\n' for c in head)+'</tr>\n</thead>\n<tbody>\n'
            +''.join('<tr>\n'+''.join(f'<td>{c}</td>\n' for c in r)+'</tr>\n' for r in rows)+'</tbody>\n</table></div>')
# "What it says vs what it does": each verdict drawn in the style of the mark it reads like (STATES in rules.py), with its own
# words and meaning, since a verdict isn't a mark and costs nothing; T2 is the answer the score counts. A verdict may add words
# after its own ("Matches, as far as checked").
SAYS={'Matches':('good','What it does matches what its docs say'),'Partly':('note','Only part of what its docs say matches what it does'),
      "Doesn't match":('concern','What it does differs from what its docs say; T2 says whether that costs points'),
      'Not checked':('nc','Not checked; the evidence says why'),'Not allowed':('na','The licence forbids checking this')}
SAYSQ='T2'  # the answer the claims back: its key question links them, with their count
SAYSW={'Matches':('matches','match'),'Partly':('partly','partly'),"Doesn't match":("doesn't match","don't match"),'Not checked':('not checked','not checked'),'Not allowed':('not allowed','not allowed')}
assert set(SAYS)==set(re.match(r'\^\((.*?)\)',SCHEMA['$defs']['block']['oneOf'][3]['properties']['rows']['items']['properties']['Verdict']['pattern']).group(1).split('|')), 'card.schema.json: the "Says vs does" verdicts changed; give each one a mark and a meaning in SAYS (site/page.py)'
def says_word(v):
    # The verdict a "Says vs does" row starts with (SAYS); it may add words after its own ("Matches, as far as checked").
    w=next((w for w in SAYS if v==w or v.startswith(w+',')),None)
    assert w, 'a "What it says vs what it does" verdict must start with '+', '.join(SAYS)+': '+v
    return w
def says_verdict(v):
    # One "Says vs does" verdict as a mark.
    return state_html(SAYS[says_word(v)][0],SAYS[says_word(v)][1],inner=esc(v))
def says_link(C,a):
    # A link to the tool's claims with their count by verdict ("7 claims: 5 match, 1 partly, 1 not checked"), or ''.
    vs=[says_word(r['Verdict']) for b in C['sections'].get('What it says vs what it does',[]) if 'Verdict' in b.get('table',[]) for r in b['rows']]
    if not vs: return ''
    n={w:vs.count(w) for w in SAYS if w in vs}
    return f'<a class="limit claims" href="#r-{a}-says" title="What its docs say, checked claim by claim">{len(vs)} claim{"s" if len(vs)>1 else ""}: '+', '.join(f'{c} {SAYSW[w][c>1]}' for w,c in n.items())+'</a>'
def blocks(C,bl,a,area=None):
    # A section's blocks (text, lists, limits, tables) as HTML. In an area section a Concern line or row shows as its
    # costliest answer does ("Concern", "Major", "Off by default", "On request"); Good and Note show as they are.
    def mark(b):
        if not b.get('mark'): return ''
        return concern_span(b['questions'],C['A'],C['SETS'],area)[1] if area and b['mark']=='concern' else state_html(b['mark'])+' '
    out=[]
    for b in bl:
        if 'table' in b:
            # A row's mark gets its own first column, as in the answer tables; a table whose rows carry no mark has no such column.
            cols=b['table']; marked=any(r.get('mark') for r in b['rows'])
            # An Evidence column is set smaller, as in the answer tables; a Verdict ("Says vs does") is drawn as a mark.
            out.append(table((['Mark'] if marked else [])+cols,[([f'<span class="mcol">{mark(r)}</span>'] if marked else [])+[f'<span class="ev">{cell(r[c])}</span>' if c=='Evidence' else
                             f'<span class="mcol">{says_verdict(r[c])}</span>' if c=='Verdict' else cell(r[c]) for c in cols] for r in b['rows']],' says' if 'Verdict' in cols else ''))
        elif 'list' in b: out.append(markdown.markdown('\n'.join('- '+i for i in b['list'])))
        elif 'limits' in b:
            # Each limit gets an anchor ({lim:n}) and links the answers it affects ({q:ID}); post() turns both into links for the tool.
            out.append(markdown.markdown('\n'.join(f'- {{lim:{n}}} **{n+1}.** '+x['text']+(' Affects '+', '.join('{q:'+q+'}' for q in x['questions'])+'.' if x['questions'] else '') for n,x in enumerate(b['limits']))))
        else: out.append(f'<p>{mark(b)}{" " if b.get("mark")=="concern" and area else ""}{cell(b["text"])}</p>')
    return post('\n'.join(out),a)
def answer_table(C,a,k):
    # One area's answers: the question, its mark with what it costs, the answer, its evidence, and the comment icon.
    f=C['f']; A=C['A']; SETS=C['SETS']; rows=[]
    for i in [q for q in QIDS if q[0]==k]:
        ans=C['rows'][i]; ev=C['d']['answers'][i]['evidence']; ch=SETS.get(i)
        # Where the mark depends on a condition ("Concern; Note if …"), the line shows that rule, so a reader sees why it is the mark it is.
        mv=re.match(r'\{.\} (Yes|No)\b',ans); rule=QCELL[i].get(mv.group(1)) if mv else None
        mrule=f' <span class="mrule">Marked by the rule: {esc(rule)}.</span>' if rule and ' if ' in rule and not rule.endswith('Note if only on request') else ''
        # Where Partly has its own meaning on a question (scoring.yaml, partly_means), a Partly answer says it.
        if re.match(r'\{.\} Partly\b',ans) and PMEANS.get(i): mrule=f' <span class="mrule">Partly here means: {esc(PMEANS[i])}.</span>'
        # Each answer the score counts shows its cost, the same number the score uses: "−N", "±0" when another answer of the
        # same behaviour counts it, and an open answer (not checked, not allowed or held back) "−N" at its highest cost.
        cost=(f' <span class="gcost" title="Counted with {ch[1]}: the same behaviour">±0</span>' if ch[1] else
              f' <span class="gcost" title="Open: it counts at its highest cost until it is answered">−{ch[0]}</span>' if ch[2] else
              f' <span class="gcost" title="What this answer takes off its area\'s 100">−{ch[0]}</span>') if ch else ''
        # A Concern whose cost another answer already counts (a waived or covered cost) shows "±0" too, like a grouped one.
        cov=next((w for w in GCOVER.get(i,()) if A[w][0]=='!' and A[w][1] in ('Yes','No','Partly')),None)
        if not ch and A[i][0]=='!' and A[i][1] in ('Yes','No','Partly') and i in GCOST: cost=(f' <span class="gcost" title="Counted with {cov}: the same behaviour">±0</span>' if cov else
              ' <span class="gcost" title="Costs nothing: the release is traced to public source">±0</span>')
        # The mark and its cost get their own column, so an area reads down one line and every answer starts at the same place.
        # A Concern reads "Concern", or "Major" when it is severe, with its cost inside the mark ("Concern −25"); one only after
        # a choice you make shows "Off by default" or "On request". An answer with no mark shows its state: Not checked (Held
        # back when a rule-9 item touches it), Not allowed, Doesn't apply (rules.py, STATES). The card keeps the mark "concern".
        if A[i][0]=='!': mk=concern_span([i],A,SETS,k,cost)[1]; st=state_of(mk); ans=ans[4:]
        elif A[i][0]: st={'+':'good','~':'note'}[A[i][0]]; mk=state_html(st)+' '+cost.lstrip(); ans=ans[4:]
        else: st={'NC':'held' if i in C['held'] else 'nc','NA':'na','DNA':'dna'}[A[i][1]]; mk=state_html(st,inner=STATES[st][0]+cost)
        # An answer with no mark doesn't repeat its state: the mark column already shows it, so the answer gives only the
        # reason. A held-back answer's evidence is published with the details.
        if st=='held' and ans.startswith('Not checked. Held back'): ev='Published with the details.'
        for w in ('Not checked. ','Not allowed. ',"Doesn't apply. "):
            if ans.startswith(w): ans=ans[len(w)].upper()+ans[len(w)+1:]
        # Likewise an answer marked Off by default or On request starts "Yes.": its mark already says which.
        if st in ('off','req'): ans=re.sub(r'^Yes, (not by default|on request)\.( |$)',r'Yes.\2',ans)
        lim=''.join(f' <a class="limit" href="#lim-{a}-{n}" title="A limit of this analysis affects this answer">limit {n+1}</a>' for n in LIMS.get(f,{}).get(i,[]))
        # The comment icon, in its own last column: a new comment on this answer (wrong, missing, or the author's context) through
        # the form with the card and the question filled in, or, while some are open, their count, linking the card's Corrections section.
        oc=CORR.get(f,{}).get(i,[])
        ci=(f'<a class="report-it has" href="#r-{a}-corr" data-n="{len(oc)}" aria-label="{len(oc)} open comment{"s" if len(oc)>1 else ""} on {i}" title="Under review: {", ".join("#"+str(n) for n in oc)}. Nothing on the card changes until it is decided."></a>' if oc else
              f'<a class="report-it" href="{esc(correction_link(C["name"]+" "+C["ver"],i,C["rows"][i]))}" target="_blank" rel="noopener" aria-label="Comment on {i}" title="Comment on this answer, Good ones included: it\'s wrong, something is missing, or context from the author"></a>')
        rows.append((st,[f'<span class="qid" id="q-{a}-{i}">{i}</span> {cell(QTXT[i])}',f'<span class="mcol" data-s="{st}">{mk}</span>',cell(ans)+mrule+lim,f'<span class="ev">{cell(ev)}</span>',ci]))
    return [st for st,_r in rows],post(table(['ID','Mark','Answer','Evidence','<span class="vh">Comment</span>'],[r for _st,r in rows]),a)
tpl=markdown.markdown(MDTXT['template.md'], extensions=['tables'])
tpl=re.sub(r'<h1>.*?</h1>','',tpl); tpl=re.sub(r'<h2>(.*?)</h2>', r'<h3>\1</h3>', tpl)
tpl=tpl.replace('<table>','<div class="tw"><table>').replace('</table>','</table></div>')
# How it works: the steps (in the page shell) and the rules stay open; every other part of the template is reference, each folded under its own name.
FOLDS={'How AI is used':'who does the work, model and effort, the prompt, why runs differ',
       'Marks and scores':'how each fact is marked and each area is scored',
       'Sections':'',
       'Wording':''}
# For card writers: what a card holds and how it is written, in one fold, after the reader's parts.
WRITERS=('Sections','Wording')
parts=re.split(r'(?=<h3>)',tpl)
# The rules are a numbered list like the steps above them (.flow).
open_=[x.replace('<ol>','<ol class="flow">',1) if x.startswith('<h3>Rules</h3>') else x for x in parts if not x.startswith('<h3>') or x.startswith('<h3>Rules</h3>')]
folded={re.match(r'<h3>(.*?)</h3>',x).group(1):x for x in parts if x.startswith('<h3>') and not x.startswith('<h3>Rules</h3>')}
assert set(folded)==set(FOLDS), 'template.md: its sections no longer match the folds in build.py: '+', '.join(sorted(set(folded)^set(FOLDS)))
# How scores are worked out (rules/scores.md) folds straight after "Marks and scores", so the costs sit beside the marks.
GRD=markdown.markdown(re.sub(r'^# .*\n','',MDTXT['scores.md']), extensions=['tables'])
GRDF=('<details class="more" id="scores"><summary>How scores are worked out <span>rubric '+SC['scores']['version']+'</span></summary><div class="report">'
      +re.sub(r'<h2>(.*?)</h2>', r'<h3>\1</h3>', GRD).replace('<table>','<div class="tw"><table>').replace('</table>','</table></div>')+'</div></details>\n')
tpl=(''.join(open_)+'<h3>In detail</h3>\n'+''.join(f'<details class="more"><summary>{k} <span>{v}</span></summary>'+folded[k].split('</h3>',1)[1]+'</details>\n'+(GRDF if k=='Marks and scores' else '') for k,v in FOLDS.items() if k not in WRITERS)
     +'<details class="more"><summary>For card writers <span>what a card holds, in order, and how it is written</span></summary>'+''.join('<h4>'+k+'</h4>'+folded[k].split('</h3>',1)[1] for k in WRITERS)+'</details>\n')
prm=open(ROOT+'prompts/analyse-tool.md').read()
assert '\n## The prompt\n' in prm, 'prompts/analyse-tool.md: no "## The prompt" section'
# The drop-in check, CLAUDE.md and the For authors page say "steps 1 to 5" (analyse and run, no card) and "skip step 6" (VirusTotal):
# renumbering the prompt must update them too.
assert re.search(r'^5\. Run it',prm,re.M) and re.search(r'^6\. Look up the hashes on VirusTotal',prm,re.M), 'prompts/analyse-tool.md: step 5 must be running the tool and step 6 the VirusTotal lookup, as SKILL.md, CLAUDE.md and the For authors page say; update them if the steps move'
prm=markdown.markdown(prm.split('\n## The prompt\n',1)[1], extensions=['fenced_code'])
prm=re.sub(r'<h2>(.*?)</h2>', r'<h3>\1</h3>', prm)
def money_html(l,href=None):
    # The Money label as the page shows it (an area heading, Compare), with what it means on hover.
    tag='a' if href else 'span'
    return f'<{tag} class="money{" na" if l in MLEFT else ""}"'+(f' href="{href}"' if href else '')+f' title="{esc(MLAB[l]["means"])}">{l}</{tag}>'
MW={'+':('good','Good'),'~':('note','Note'),'!':('bad','Concern'),None:('none','')}
def inline(s):
    # One line of card Markdown (code, bold, links) to HTML, without a wrapping paragraph.
    h=markdown.markdown(s)
    return re.sub(r'^<p>|</p>$','',h).replace('<a href="http','<a target="_blank" rel="noopener" href="http')
def short(v):
    # The header shows the first clause of a row, without asides in brackets; the full row stays in the report.
    v=re.split(r'(?<!\w\.\w)\. |; ',v)[0]
    return re.sub(r' \((?![^()]*\]\()[^()]*\)','',v).strip()
def byline(v):
    s=re.sub(r'<[^>]+>','',inline(short(v)))
    s=re.sub(r'^GitHub (user|organisation) ','',s)
    return 'Author not named' if s.startswith('Not named') else 'by '+s
TAGCAP=6  # the front page shows at most this many critical tags per tool, costliest first; the rest sit behind "+N more"
def tagrow(card,a,cap=None):
    # Every tag links to the answer it comes from, where its evidence is. Critical tags go costliest first (ties keep the
    # tag table's order); with cap, those past it start hidden behind one "+N more" button, the same for every tool.
    A=card['answers']
    crit,opt,pos=tagsof(card)
    crit=sorted(crit,key=lambda t:-(qcost(t[1],A[t[1]]['verdict']) or maxcost(t[1])))
    # A severe Concern's tag shows as Major (orange, with a triangle), like its answer's mark.
    bad=lambda q:'bad'+(' hi' if (qcost(q,A[q]['verdict']) or maxcost(q))>=GT['severe'] else '')
    def tg(cls,label,tip,q=None): return f'<a class="mark {cls}" href="#{"q-"+a+"-"+q if q else a}" title="{esc(tip)}">{esc(label)}</a>'
    # An optional tag shows which choice brings it: Off by default (a setting) or On request (you start it, each time).
    def ost(q): return 'req' if A[q]['verdict']=='Yes, on request' else 'off'
    OTIP={'off':'only after a setting or choice you make','req':'only when you start it, each time'}
    hb=card['header'].get('Held back')
    unanswered=[q for q in QIDS if A[q]['verdict'] in ('Not checked','Not allowed')]
    # "No critical findings" only when every question is answered and none is a Concern by default.
    # Open corrections come first, neutral (dashed, like everything still open); they change no tag, mark or score.
    oc=[c for c in card.get('corrections',[]) if c['status']=='open']
    cq=', '.join(dict.fromkeys(q for c in oc for q in c['questions']))
    corr=f'<a class="mark corr" href="#r-{a}-corr" title="{esc("Corrections under review about "+cq+". Nothing on the card changes until each is decided.")}">{len(oc)} under review</a>' if oc else ''
    shown,extra=(crit[:cap],crit[cap:]) if cap and len(crit)>cap+1 else (crit,[])
    h=corr+(''.join(tg(bad(q),l,f'From {q}: {QTXT[q]}',q) for l,q in shown) or ('' if hb or unanswered else tg('good','No critical findings','Every question is answered, and no answer is a Concern by default')))
    if extra: h+=f'<button type="button" class="mark bad more-x" title="{esc(", ".join(l for l,_q in extra))}">+{len(extra)} more</button>'+''.join(tg(bad(q)+' xtra',l,f'From {q}: {QTXT[q]}',q).replace('<a ','<a hidden ',1) for l,q in extra)
    # Optional tags start hidden behind one button; they are plain tags in the row, so they wrap and space like the others.
    if opt:
        kinds={ost(q) for _l,q in opt}; ow=' or '.join(STATES[k][0].lower() for k in ('off','req') if k in kinds)
        h+=(f'<button type="button" class="mark {STATES["off" if "off" in kinds else "req"][1]} more-opt" title="Behaviour that only happens {esc(" or ".join(OTIP[k] for k in ("off","req") if k in kinds))}; it costs nothing">+{len(opt)} {ow}</button>'
            +''.join(tg(STATES[ost(q)][1]+' opt',l,f'From {q}, {OTIP[ost(q)]}: {QTXT[q]}',q).replace('<a ','<a hidden ',1) for l,q in opt))
    held=set()
    if hb:
        m=re.match(HELD,hb); held=set(m.group(2).split(', '))
        h+=tg(STATES['held'][1],f'{m.group(1)} held back',f'Held back under rule 9, not published yet: {m.group(2)}',m.group(2).split(', ')[0])
    nc=[q for q in QIDS if A[q]['verdict']=='Not checked' and q not in held]
    if nc: h+=tg(STATES['nc'][1],f'{len(nc)} not checked','Not checked: '+', '.join(nc),nc[0])
    na=[q for q in QIDS if A[q]['verdict']=='Not allowed']
    if na: h+=tg(STATES['na'][1],'Licence forbids analysis','Its licence forbids analysing it, so some answers are "Not allowed": '+', '.join(na),na[0])
    h+=''.join(tg('good',l,f'From {q}: {QTXT[q]}',q) for l,q in pos)
    return f'<div class="tags">{h}</div>'
def changes(f,card):
    # What changed since the tool's previous card (registry order is oldest first), worked out from the two cards' answers.
    lst=REG[SLUG[f]]['cards']; i=lst.index(f)
    if i==0: return ''
    old=load_yaml(D+lst[i-1])
    def va(c,q):
        a=c['answers'].get(q)
        return (a['verdict'],a.get('mark')) if a else ('Not asked',None)
    W={'good':'Good','note':'Note','concern':'Concern',None:''}
    rows=[f'<li><span class="qid">{q}</span> {esc(" ".join(x for x in (W[va(old,q)[1]],va(old,q)[0]) if x))} → {esc(" ".join(x for x in (W[va(card,q)[1]],va(card,q)[0]) if x))}</li>' for q in QIDS if va(old,q)!=va(card,q)]
    A0={q:verdict(ans_md(old['answers'][q])) for q in QIDS if q in old['answers']}; A1={q:verdict(ans_md(card['answers'][q])) for q in QIDS}
    try: g0=scored(A0)['areas']
    except (KeyError,AssertionError): g0={}
    g1=scored(A1)['areas']
    for ar in g1:
        if ar in g0 and g0[ar][0]!=g1[ar][0]: rows.append(f'<li>{ar}: {g0[ar][0]} → {g1[ar][0]}</li>')
    same=len(QIDS)-sum(1 for q in QIDS if va(old,q)!=va(card,q))
    body=''.join(rows) or '<li>No answer changed.</li>'
    return f'<h3 class="sech">Changes since {esc(old["version"])}</h3><ul class="chg">{body}<li class="same">{same} answers unchanged</li></ul>'
# The header rows shown at the top of a tool's page; the report's header table holds the others.
TOPROWS=('In one line','What it is','Category','Author','Game','mxb-mods.com','gpb-mods.com','Homepage','GitHub','Version analysed','Analysed on','Earlier reports')
# The report's sections that aren't areas: their anchor key and their short label in the contents bar (kept short, so the bar fits one line).
RSECS={'What it says vs what it does':('says','Says vs does'),'Limits of this analysis':('limits','Limits')}
assert set(RSECS)=={t for t,k in SECTIONS.items() if not k}, 'card.schema.json: site/page.py (RSECS) needs an anchor and a short label for each section that isn\'t an area'
def report(C,a,gl):
    # The report (All answers and evidence), made from the card's data as folding sections (open by default, so nothing is hidden),
    # and the tool's contents bar (tool() puts it under the tool's heading, where it stays in view on the whole tool page):
    # section links, a jump to any question, a filter by mark, fold all, back to top.
    d=C['d']; h=C['h']; got=[]
    # (anchor key, heading, contents-bar label, beside the heading, body)
    secs=[('release','Release and method','Release','',post(
        table(['',''],[(k,cell(h[k])) for k in HEADER if k in h and k not in TOPROWS],' meta')+'\n<p>Files checked:</p>\n'
        +table(['File','Inside','SHA-256','VirusTotal','Note'],[[cell(c) for c in r] for r in files_table(C['f'],d)])
        +('\n'+markdown.markdown(d['files_note']) if d.get('files_note') else ''),a))]
    for title,k in SECTIONS.items():
        bl=C['sections'].get(title,[])
        if k:
            # An area section: beside its heading the area's score (or the Money label) and its one-line reason (the card's
            # `areas`); then the area's answers, its tables (what leaves your PC, ...) folded under them, and the lines no answer covers.
            ar=SC['areas'][k]['name']; states,body=answer_table(C,a,k); got+=states
            for b in bl:
                if 'table' in b: body+=f'\n<details class="sub"><summary>{FOLDNAME[tuple(b["table"])]} ({len(b["rows"])})</summary>\n{blocks(C,[b],a,k)}\n</details>'
            # The lines no answer covers sit under one "Also found" heading, so a line's own "Also found: " isn't repeated.
            rest=[dict(b,text=(lambda t:t[:1].upper()+t[1:])(b['text'][len('Also found: '):])) if b.get('text','').startswith('Also found: ') else b for b in bl if 'table' not in b]
            if rest: body+='\n<p><strong>Also found</strong></p>\n'+blocks(C,rest,a,k)
            side=(f'<span class="ascore">{gl[ar]}</span>' if ar in CONCERN else money_html(gl[ar]))+f'<span class="awhy">{post(cell(d["areas"][ar]),a)}</span>'
            secs.append((AREAK[ar],title,ar,side,body))
        elif bl: secs.append((RSECS[title][0],title,RSECS[title][1],'',blocks(C,bl,a)))
    secs.append(('corr','Corrections','Corrections','',md(C['corrections'],a)))
    secs.append(('history','Card history','History','',post(table(['Date','Change'],[(cell(r['date']),cell(r['change'])) for r in d['history']],' hist'),a)))
    links=''.join(f'<a href="#r-{a}-{k}">{l}</a>' for k,_t,l,_s,_b in secs)
    body=''.join(f'<details class="rsec" id="r-{a}-{k}" open><summary><h3>{t}</h3>{side}</summary><div class="rbody">{b}</div></details>' for k,t,_l,side,b in secs)
    opts=''.join(f'<optgroup label="{esc(ar)}">'+''.join(f'<option value="q-{a}-{q}">{q} {esc(QTXT[q])}</option>' for q in QIDS if q[0]==PFX[i])+'</optgroup>' for i,ar in enumerate(AREAN))
    # Show only the answers of one mark: the states the answers carry (STATES in rules.py), with their counts, most severe first.
    FILT=(('major',),('concern',),('off','req'),('note',),('good',),('nc','held','na','dna'))
    fopts=''.join(f'<option value="{" ".join(g)}">{esc(" or ".join(STATES[k][0] for k in g if k in got))} ({sum(got.count(k) for k in g)})</option>' for g in FILT if any(k in got for k in g))
    nav=(f'<nav class="rnav" aria-label="Contents of this tool\'s page"><div class="rlinks">{links}</div>'
         f'<div class="rtools"><select class="rjump" aria-label="Jump to a question"><option value="">Jump to a question…</option>{opts}</select>'
         f'<select class="rjump rfilt" aria-label="Show answers by mark"><option value="">All answers ({len(got)})</option>{fopts}</select>'
         f'<button type="button" class="rfold">Fold all</button><a class="rcmp" href="#compare" data-pick="{a}">Compare</a><a class="rtop" href="#{a}">Top</a></div></nav>')
    return nav,body
# The For authors check and the author's prompt point at the rules at COMMIT, the commit this page was built from.
def authorbox(a,f,name,ver,badges=''):
    # "For the tool's author": the card file to download, one prompt for every tool (no fixes of ours), how to get a re-check,
    # and the badges to embed (score_section makes them).
    prompt=(f'This is the MXB Facts card for {name} {ver} ({f}): one release of this tool, answered against the same questions as every other tool, '
            f'with evidence for each answer. Go through every answer whose mark isn\'t "Good", and those without a mark ("Not checked"). For each one, '
            f'follow its evidence to the code or file it points at in this repository and explain to me what causes that answer. Don\'t change anything yet: '
            f'we\'ll decide together what to change, if anything, because that depends on what the tool is for. The questions, the rules behind each mark and what each Concern costs '
            f'are rules/questions.md, rules/template.md and rules/scores.md in {REPO.rstrip("/")} at commit {COMMIT}.')
    # Folded under the report, in the same style, closed until opened.
    return (f'<details class="full" id="x-{a}"><summary><span class="fs">For the tool\'s author</span><span class="fn">Go through the card with your agent, get a re-check, and add the badge to your page</span></summary><div class="report authorbox">'
            f'<p>Give this card to the AI agent you build with (Claude Code, Codex, Cursor or any other). Every answer links its evidence, '
            f'so the agent can find the cause in your code. We don\'t suggest fixes: what to change, if anything, depends on what your tool is for.</p><ol class="flow">'
            f'<li><b>Download the card:</b> <a class="dl" download href="cards/{f}">{f}</a>, and put it in your tool\'s repository.</li>'
            f'<li><b>Paste this prompt</b> into your agent there:<pre><code id="xp-{a}">{esc(prompt)}</code></pre></li>'
            f'<li><b>After your next release, <a href="{REPO}issues/new?template=analyse-tool.yml">request a re-check</a>.</b> The new release gets a new card; this one stays.</li></ol>'
            f'{badges}<p>To check a release before anyone else does, see <a href="#authors">For authors</a>.</p></div></details>')
def score_html(G,a,cls=''):
    # Signs of malware and Not scored show their icon in place of a number, with the words for screen readers.
    if G['kind'] in ('malware','notscored'):
        lab,_c,ic,_m=STATES[G['kind']]
        return f'<a class="sbox g-{G["kind"]}{" "+cls if cls else ""}" href="#g-{a}" title="{esc(lab+". "+"; ".join(G["why"]))}" aria-label="{esc(lab)}"><b class="gicon" aria-hidden="true"></b><small>&nbsp;</small></a>'
    tip=f"Score (rubric {RUBRICV}): {gtext(G)}, higher is better. From the costs of its Concern answers"+(('; '+'; '.join(G['why'])) if G['why'] else '')
    return f'<a class="sbox g-{G["kind"]}{" "+cls if cls else ""}" href="#g-{a}" title="{esc(tip)}"><b>{esc(gsym(G))}</b>{"<small>/100</small>" if G["kind"]!="malware" else "<small>&nbsp;</small>"}</a>'
GCOL={'score':'#3d4a5c','notscored':'#6e7682','malware':'#cf222e'}  # as .g-* in shell.html; red is for signs of malware alone
# Badges (rules/scores.md, "Badge"): three shields in the shields.io styles (flat, flat-square, for-the-badge: same sizes,
# padding, font and text shadow), a score tile, and a card with the area scores. Text is sized from DejaVu Sans widths, the
# shields.io fallback for Verdana, and pinned with textLength so every viewer draws it the same width.
SITEURL='https://thomas4f.github.io/mxb-facts/'
def share_page(a,name,ver,G,one,card):
    # Each tool's own address (<site>/<tool>/): a small page whose title and description show in a link preview (Discord,
    # forums, chat apps read them; a #tool link only ever shows the site's own), and which then opens the tool's page.
    title=f'{name} {ver}: {gtext(G)} · MXB Facts'
    # Its critical findings costliest first, as the tools list orders them.
    crit=sorted(tagsof(card)[0],key=lambda t:-(qcost(t[1],card['answers'][t[1]]['verdict']) or maxcost(t[1])))
    found=', '.join(l for l,_q in crit[:4])+(f' and {len(crit)-4} more' if len(crit)>4 else '')
    desc=one+'. '+(f'Key findings: {found}.' if crit else 'No critical findings.')+' Every answer links its evidence.'
    url=f'{SITEURL}{a}/'
    return (f'<!doctype html>\n<html lang="en">\n<meta charset="utf-8">\n<title>{esc(title)}</title>\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<meta name="description" content="{esc(desc)}">\n<link rel="canonical" href="{url}">\n'
            f'<meta property="og:type" content="article">\n<meta property="og:site_name" content="MXB Facts">\n'
            f'<meta property="og:title" content="{esc(title)}">\n<meta property="og:description" content="{esc(desc)}">\n'
            f'<meta property="og:url" content="{url}">\n<meta name="twitter:card" content="summary">\n'
            f'<meta http-equiv="refresh" content="0; url=../#{a}">\n'
            f'<style>body{{font:16px/1.5 system-ui,sans-serif;margin:2rem;background:#f3f4f6;color:#14171c}}@media (prefers-color-scheme:dark){{body{{background:#101216;color:#e6e9ed}}a{{color:#8fa9ff}}}}</style>\n'
            f'<p><a href="../#{a}">{esc(name)} {esc(ver)} on MXB Facts</a></p>\n')
BW=json.load(open(ROOT+'site/badge-widths.json'))
def _tw(t,k):
    # As shields.io does: the text's width, rounded down, then up to an odd number of pixels.
    w=math.floor(sum(BW[k][ord(c)-32] if 32<=ord(c)<127 else BW[k][ord('m')-32] for c in t)); return w if w%2 else w+1
BFONT='Verdana,Geneva,DejaVu Sans,sans-serif'
BLABEL='MXB Facts'
def btitle(name,ver,G,date): return f'{BLABEL}, {name} {ver}: {gtext(G)} (rubric {RUBRICV}, analysed {date}). Worked out from the answers\' costs.'
def _n(x): return f'{x:g}'
def shield(style,msg,color,title,uid):
    # style: flat, flat-square or for-the-badge, drawn the way shields.io draws them (sizes, padding, fonts, shadow).
    big=style=='for-the-badge'; h=28 if big else 20
    lab,msg=(BLABEL.upper(),msg.upper()) if big else (BLABEL,msg)
    lt=_tw(lab,'10' if big else '11')+(1.25*len(lab) if big else 0); mt=_tw(msg,'10b' if big else '11')+(1.25*len(msg) if big else 0)
    pad=12 if big else 5; lw=lt+2*pad; mw=mt+2*pad; w=lw+mw
    if big:
        texts=(f'<text transform="scale(.1)" x="{_n(lw*5)}" y="175" textLength="{_n(lt*10)}">{esc(lab)}</text>'
               f'<text transform="scale(.1)" x="{_n((lw+mw/2)*10)}" y="175" textLength="{_n(mt*10)}" font-weight="bold">{esc(msg)}</text>')
    else:
        def one(t,x,tl): return (f'<g transform="scale(.1)"><g aria-hidden="true" fill="#010101"><text x="{_n(x*10)}" y="150" fill-opacity=".8" filter="url(#b{uid})" textLength="{_n(tl*10)}">{esc(t)}</text>'
                                 f'<text x="{_n(x*10)}" y="150" fill-opacity=".3" textLength="{_n(tl*10)}">{esc(t)}</text></g>'
                                 f'<text x="{_n(x*10)}" y="140" textLength="{_n(tl*10)}">{esc(t)}</text></g>')
        def flat(t,x,tl): return f'<text x="{_n(x*10)}" y="140" textLength="{_n(tl*10)}" transform="scale(.1)">{esc(t)}</text>'
        if style=='flat-square': one=flat  # no shadow
        texts=one(lab,lw/2+1,lt)+one(msg,lw+mw/2-1,mt)  # shields.io moves each text 1px toward the middle
    rects=f'<rect width="{_n(lw)}" height="{h}" fill="#555"/><rect x="{_n(lw)}" width="{_n(mw)}" height="{h}" fill="{color}"/>'
    body=(f'<filter id="b{uid}"><feGaussianBlur stdDeviation="16"/></filter><linearGradient id="s{uid}" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient>'
          f'<clipPath id="r{uid}"><rect width="{_n(w)}" height="{h}" rx="3"/></clipPath><g clip-path="url(#r{uid})">{rects}<rect width="{_n(w)}" height="{h}" fill="url(#s{uid})"/></g>'
          if style=='flat' else f'<g shape-rendering="crispEdges">{rects}</g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{_n(w)}" height="{h}" role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>{body}'
            f'<g fill="#fff" text-anchor="middle" font-family="{BFONT}" text-rendering="geometricPrecision" font-size="{100 if big else 110}">{texts}</g></svg>')
def _tile(G,x,y,s):
    # The score square, as on the site: the score (or ? / X), "/100" under it, the site's name at the foot.
    sym=gsym(G); sub='/100' if G['kind']=='score' else ''
    # Signs of malware and Not scored draw their icon (STATES in rules.py) in place of a number.
    big=(icon_group(STATES[G['kind']][2],x+s*.32,y+s*.2,s*.36,'#fff') if G['kind'] in ('malware','notscored') else
         f'<text x="{x+s/2}" y="{y+s*.5}" font-size="{s*.36:.0f}" font-weight="bold">{esc(sym)}</text>')
    return (f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="6" fill="{GCOL[G["kind"]]}"/><g fill="#fff" text-anchor="middle" font-family="{BFONT}">'
            f'{big}<text x="{x+s/2}" y="{y+s*.68}" font-size="{s*.13:.0f}" fill-opacity=".85">{sub}</text>'
            f'<text x="{x+s/2}" y="{y+s*.9}" font-size="{s*.085:.1f}" fill-opacity=".8" letter-spacing=".4">{BLABEL.upper()}</text></g>')
def badge_tile(G,title):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>{_tile(G,0,0,96)}</svg>'
def badge_areas(G,title):
    # The tile beside one bar per area, as in the Score card on the tool's page; no area numbers when there is no score.
    nn=G['kind'] in ('notscored','malware'); rows=''
    for i,ar in enumerate(x for x in AREAN if x in CONCERN):
        sc=G['areas'][ar][0]; y=13+i*20
        v='–' if nn else str(sc); fw=0 if nn else sc*.76
        rows+=(f'<text x="124" y="{y+4}" font-size="11" fill="#1d2330">{esc(ar)}</text><text x="270" y="{y+4}" font-size="11" font-weight="bold" fill="#1d2330" text-anchor="end">{v}</text>'
               f'<rect x="278" y="{y-3}" width="76" height="6" rx="3" fill="#e3e6eb"/><rect x="278" y="{y-3}" width="{fw:.1f}" height="6" rx="3" fill="#5d6878"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="366" height="108" role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>'
            f'<rect x=".5" y=".5" width="365" height="107" rx="8" fill="#fff" stroke="#d0d5dd"/>{_tile(G,6,6,96)}<g font-family="{BFONT}">{rows}</g></svg>')
BADGES=[  # (file suffix, name shown to authors, how it is drawn)
    ('','Shield',lambda G,t,u:shield('flat',gtext(G),GCOL[G['kind']],t,u)),
    ('-flat-square','Shield, square corners',lambda G,t,u:shield('flat-square',gtext(G),GCOL[G['kind']],t,u)),
    ('-for-the-badge','Large shield',lambda G,t,u:shield('for-the-badge',gtext(G),GCOL[G['kind']],t,u)),
    ('-score','Score',lambda G,t,u:badge_tile(G,t)),
    ('-areas','Score and areas',lambda G,t,u:badge_areas(G,t)),
]
def badge_json(ver,G):
    # The shields.io "endpoint" format, so shields.io can draw it in any of its styles.
    return json.dumps({'schemaVersion':1,'label':BLABEL,'message':gtext(G),'color':GCOL[G['kind']].lstrip('#')})
def score_section(a,name,ver,G,date,gl):
    # The Score card at the top of a tool page: the badge, words in place of a number where it has none, and one bar per area
    # (each links to its area's section). Also the badges authors can embed, which go under "For the tool's author".
    best=f'<em>{esc(gtext(G))}</em>' if G['kind'] in ('notscored','malware') else ''
    bars=''.join(f'<a class="abar" href="#r-{a}-{AREAK[ar]}"><span class="an">{esc(ar)}</span><span class="av">{gl[ar]}</span><span class="at"><i style="width:{gl[ar] if isinstance(gl[ar],int) else 0}%"></i></span></a>' for ar in AREAN if ar in CONCERN)
    # Open answers count at their full cost (rules/scores.md, "What we don't know"); the line under the score says how many.
    n=len(G['open'])
    gopen=(f'<p class="gopen">{n} answer{"s" if n>1 else ""} still open count{"" if n>1 else "s"} at full cost: '+', '.join(f'<a href="#q-{a}-{q}">{q}</a>' for q in G['open'])+'</p>') if n and G['kind']=='score' else '<p class="gopen">No answer still open costs points here.</p>' if G['kind']=='score' else ''
    card=(f'<div class="hcol"><h3 class="sech" id="g-{a}">Score <small class="gnote">{GNOTE}</small></h3><div class="scorecard">{score_html(G,a,"card").replace("</a>",best+"</a>",1)}<div class="abars">{bars}</div>{gopen}</div></div>')
    bpath=f'badge/{a}/{ver}'; purl=f'{SITEURL}{a}/'; t=btitle(name,ver,G,date); opts=''
    for suf,label,draw in BADGES:
        burl=f'{SITEURL}{bpath}{suf}.svg'
        opts+=(f'<div class="bopt"><h4>{label}</h4><p>{draw(G,t,a+suf)}</p><pre class="c-md"><code>[![MXB Facts score]({burl})]({purl})</code></pre>'
               f'<pre class="c-html"><code>{esc(f"<a href=\"{purl}\"><img src=\"{burl}\" alt=\"MXB Facts score\"></a>")}</code></pre></div>')
    emb=(f'<details class="sub badgebox"><summary>Add the badge to your page</summary><p class="bfmt">Code for: <label><input type="radio" name="bf-{a}" value="md" checked> Markdown</label> <label><input type="radio" name="bf-{a}" value="html"> HTML</label></p><div class="bopts">{opts}</div>'
         f'<p class="fn">Each is pinned to this version and rubric {RUBRICV}: a new release gets its own badges when it has a card. Other shields.io styles: <code>https://img.shields.io/endpoint?url={SITEURL}{bpath}.json&amp;style=plastic</code>. Every card\'s scores and badge links are also in <a href="api/cards.json"><code>api/cards.json</code></a>, for sites that list tools.</p></details>')
    return card,emb
def tool(C,a,slug,gl,extra='',tags='',gsec='',maint=False):
    # One tool's page: its header facts, score and key answers first, everything else in the report (All answers and evidence).
    h=C['h']; f=C['f']; name=C['name']; ver=C['ver']
    facts=[]
    k,ms=SITES[h['Game']]
    for label,show in (('Game','Game'),('Version analysed','Version'),('Category','Category'),('Author','Author'),(ms,ms),('Homepage','Homepage'),('GitHub','GitHub'),('Analysed on','Analysed on'),('Earlier reports','Earlier reports')):
        v=h.get(label)
        if label==ms and slug in MM[k]['tools']: v=f'[{re.sub(r"^https?://(www\.)?|/$","",MM[k]["tools"][slug]["link"])}]({MM[k]["tools"][slug]["link"]})'  # the address, never the page's own title (author text)
        if v: facts.append(f'<div><dt>{show}</dt><dd>{inline(short(v))}</dd></div>')
    nav,rep=report(C,a,gl)
    items=''
    for k,q,_s,src in KEYS:
        mk,head,ans,span=C['key'][k]
        st={'+':'good','~':'note','!':'concern'}.get(mk) or ('held' if ans.startswith('Held back') else 'nc' if ans.startswith('Not checked') else 'na')
        badge=(span or state_html(st)).replace('class="mk ','class="mark ',1)
        detail=ans[len(head):].lstrip('.;').strip(); detail=detail[:1].upper()+detail[1:]
        frm=', '.join(f'<a href="#q-{a}-{i}">{i}</a>' for i in src)
        items+=(f'<li class="key" id="k-{a}-{k.lower()}"><p class="kq">{q}</p><div class="km">{badge}</div><div class="ka">'
                f'<p class="kh">{inline(head)}</p>'+(f'<p class="kd">{post(inline(detail),a)}'+(f' {says_link(C,a)}' if SAYSQ in src else '')+f' <span class="kf">From {frm}</span></p>' if detail else f'<p class="kd"><span class="kf">From {frm}</span></p>')+
                ''.join(f'<p class="kc"><a class="mark corr" href="#r-{a}-corr" title="{CORRTIP}">Under review #{n}</a></p>' for n in dict.fromkeys(n for i in src for n in CORR.get(f,{}).get(i,[])))+
                '</div></li>')
    keys=f'<h3 class="sech" id="k-{a}">Key questions</h3><ol class="keys">{items}</ol>'
    # The contents bar lists the page's parts in the order they appear: the parts above the report, then the report's sections.
    if extra.startswith('<h3 class="sech">'): extra=extra.replace('<h3 class="sech">',f'<h3 class="sech" id="c-{a}">',1)
    top=[(f't-{a}','Key findings'),(f'k-{a}','Key questions')]+([(f'c-{a}','Changes')] if extra else [])
    nav=nav.replace('<div class="rlinks">','<div class="rlinks">'+''.join(f'<a href="#{i}">{l}</a>' for i,l in top),1)
    # "For the tool's author" comes last, after the report's sections, as on the page.
    nav=nav.replace('</div><div class="rtools">',f'<a href="#x-{a}">For the author</a></div><div class="rtools">',1)
    page=(f'<section class="view tool" id="{a}" data-view>{nav}'
            f'<header class="toolhead"><h2>{esc(name)} <span class="ver">{esc(ver)}</span></h2><div class="hcard" id="d-{a}"><p class="sum">{esc(C["d"]["summary"])}</p><dl class="hmeta">{"".join(facts)}</dl>{MAINT if maint else ""}</div>'
            f'<div class="hgrid">{gsec[0]}'
            f'<div class="hcol htags"><h3 class="sech" id="t-{a}">Key findings</h3><div class="tagcard">{tags}</div></div></div></header>{keys}{extra}'
            f'<details class="full"><summary><span class="fs">All answers and evidence</span><span class="fn">Every question, area by area, with its evidence; the limits of this analysis; corrections and the card history</span></summary><div class="report">{rep}</div></details>{authorbox(a,f,name,ver,gsec[1])}</section>')
    # The contents bar follows the page: every link's target exists, in the same order as the links.
    ids=re.findall(r'<a href="#([^"]+)">',page[page.index('class="rlinks"'):page.index('</div>',page.index('class="rlinks"'))])
    pos=[page.find(f'id="{i}"') for i in ids]
    assert -1 not in pos and pos==sorted(pos), a+': the contents bar doesn\'t follow the order of the page: '+', '.join(ids)
    return page
