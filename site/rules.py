"""The rules: every question, mark, cost, tag, threshold and Money label (rules/scoring.yaml) and the card format
(rules/card.schema.json), checked when loaded, and how an answer's verdict, mark, cost and tags follow from them.

Loading this module also writes the generated tables in rules/*.md (in CI it fails while one is out of date instead).
Nothing here reads a card file: tests/test_build.py checks these functions with made-up answers.
"""
import json, os, re
import yaml
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/'
D=ROOT+'cards/'
RULESDIR=ROOT+'rules/'
OUT=os.environ.get('OUT',ROOT+'_site/index.html')
# YAML lets a second entry with the same name silently replace the first (a copy-paste not renamed); this loader refuses it.
class _Strict(yaml.SafeLoader): pass
def _nodup(loader,node,deep=False):
    keys=[loader.construct_object(k,deep=deep) for k,_v in node.value]
    dup=sorted({str(k) for k in keys if keys.count(k)>1})
    if dup: raise yaml.constructor.ConstructorError(None,None,'the name '+', '.join(dup)+' is used twice in one place',node.start_mark)
    return yaml.SafeLoader.construct_mapping(loader,node,deep)
_Strict.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,lambda l,n:_nodup(l,n,True))
def load_yaml(path): return yaml.load(open(path),Loader=_Strict)
# Every question, mark, cost, tag, threshold and Money label comes from one file, rules/scoring.yaml.
SC=load_yaml(RULESDIR+'scoring.yaml')
assert set(SC)=={'areas','virustotal','keys','questions','money','tags','scores'}, 'rules/scoring.yaml: unknown or missing sections'
_share=SC['virustotal']['flagged_share']
assert 0<_share<1 and abs(1/_share-round(1/_share))<1e-9, 'rules/scoring.yaml: flagged_share must be 1 in a whole number (0.1 is 1 in 10, 0.05 is 1 in 20), so the rules can say it exactly'
assert all(set(x)=={'name','anchor'} for x in SC['areas'].values()), 'rules/scoring.yaml: each area has a name and an anchor'
def cond(w,what):
    # One condition ("T1 no", "M2 yes"): the question and the verdict it names, checked against rules/scoring.yaml.
    q,_,v=w.partition(' ')
    assert q in SC['questions'] and v in ('yes','no','partly'), 'rules/scoring.yaml: '+what+' "'+w+'" must be a question and yes, no or partly'
    return q,v.capitalize()
# Money isn't scored: its label comes from M1 and M2 (rules/scoring.yaml, "money"), the first label whose answers all hold.
MONEY=SC['money']; MLAB=MONEY['labels']; MLEFT=('Not allowed','Not checked')
assert MONEY['area'] in SC['areas'] and set(MONEY)=={'area','labels'}, 'rules/scoring.yaml: money names its area and its labels'
assert tuple(MLAB)[-2:]==MLEFT and all(set(MLAB[l])=={'means'} for l in MLEFT) and all(set(x)=={'when','means'} and x['when'] for l,x in MLAB.items() if l not in MLEFT), 'rules/scoring.yaml: each money label lists when it applies and what it means; "Not allowed" and "Not checked" come last, with only what they mean'
MWHEN={l:[cond(w,'a money label\'s when') for w in x['when']] for l,x in MLAB.items() if l not in MLEFT}
MQS=sorted({q for c in MWHEN.values() for q,_v in c})
assert all(q[0]==MONEY['area'] for q in MQS), 'rules/scoring.yaml: money labels are set by Money questions only'
def money_when(l):
    # The "Shown when" column of the Money table in rules/template.md.
    if l=='Not allowed': return 'No label above applies, because the licence forbids answering '+' or '.join(MQS)
    if l=='Not checked': return 'No label above applies, and '+' or '.join(MQS)+' is not checked or held back'
    return ' and '.join(f'{q} is {v}' for q,v in MWHEN[l])
# The card format comes from one file too, rules/card.schema.json: the header rows, the report sections, the categories, the verdicts.
SCHEMA=json.load(open(RULESDIR+'card.schema.json'))
_HP=SCHEMA['properties']['header']['properties']
# The header rows in order. "Files checked" isn't written in the header: the build shows the card's files list as a table under it.
HEADER=list(_HP); HEADER.insert(HEADER.index('Analysed on'),'Files checked')
CATS=_HP['Category']['enum']
# The report sections in order; an area section ("P" for Your PC and files, ...) is named after its area and also holds that area's answers.
SECTIONS={t:None for t in SCHEMA['properties']['sections']['items']['properties']['title']['enum']}
for _p,_x in SC['areas'].items():
    assert _x['name'] in SECTIONS, 'card.schema.json: no report section is named after the area '+_x['name']
    SECTIONS[_x['name']]=_p
assert list(v for v in SECTIONS.values() if v)==list(SC['areas']), 'card.schema.json: the area sections must come first, in the order of the areas in rules/scoring.yaml'
# Two sections the build treats on their own (the page puts one under the summary; the other holds the limits blocks).
assert {'What it says vs what it does','Limits of this analysis'}<=set(SECTIONS), 'card.schema.json: site/build.py needs the sections "What it says vs what it does" and "Limits of this analysis"'
# The tables in rules/questions.md and rules/template.md are written from these two files, between their markers, so they read well on
# GitHub and on the site but are never edited by hand. Locally the build rewrites them; in CI (CI is set) it fails while one is out of date.
PARTLYW={None:'Note','concern':'Concern','never':'None'}
# The Partly cell: its mark, and what Partly means on that question where scoring.yaml says (partly_means).
def partly_cell(x): return PARTLYW[x.get('partly')]+(': '+x['partly_means'] if x.get('partly_means') else '')
def yes_cell(x): return x['yes_mark']+('; Note if only on request' if x.get('note_on_request') else '')+('; a second check must confirm it' if x.get('second_check') else '')
def cell(t): return str(t).replace('|','\\|').replace('<','&lt;')
def row(*cells): return '| '+' | '.join(cell(c) for c in cells)+' |'
def gen_tables():
    q=SC['questions']; ar=SC['areas']; n=round(1/SC['virustotal']['flagged_share'])
    def hrow(k):
        x=_HP[k] if k!='Files checked' else SCHEMA['properties']['files']
        return row(k,(f'One of: {"; ".join(x["enum"])}. ' if 'enum' in x else '')+x['description'])
    return {'questions.md':{
        'keys':['| Key | Key question | Short | From | Mark |','|---|---|---|---|---|']+[row(k,x['question'],x['short'],', '.join(x['from']),x['mark'].capitalize()) for k,x in SC['keys'].items()],
        'p1':['| P1 | When |','|---|---|','| No | no engine flagged any release file |',f'| Partly | fewer than 1 in {n} engines flagged a file |',f'| Yes | 1 in {n} or more flagged a file |'],
        'questions':['| ID | Area | Question | Yes | No | Partly |','|---|---|---|---|---|---|']+[row(i,ar[i[0]]['name'],x['text'],yes_cell(x),x['no_mark'],partly_cell(x)) for i,x in q.items()],
        'tags':['| From | Answer | Tag | Kind |','|---|---|---|---|']+[row(x['from'],x['answer'],x['tag']+(f' (not when {" or ".join(w.replace(" yes"," is Yes").replace(" no"," is No") for w in x["unless"])})' if 'unless' in x else ''),x['kind']) for x in SC['tags']]},
      'template.md':{
        'header':['| | |','|---|---|']+[hrow(k) for k in HEADER],
        'money':['| Label | Shown when | What it means |','|---|---|---|']+[row(l,money_when(l),x['means']) for l,x in MLAB.items()]},
      'scores.md':score_tables()}
def score_tables():
    g=SC['scores']; t=g['tiers']
    def costs(q):
        c=g['costs'][q]
        return ', '.join(f'{v}: {t[x]}' for v,x in c.items()) if isinstance(c,dict) else str(t[c])
    return {'score_tiers':['| Tier | Cost |','|---|---|']+[row(k,str(v)) for k,v in t.items()],
            'score_costs':['| ID | Area | Concern by default | Cost |','|---|---|---|---|']+[row(q,SC['areas'][q[0]]['name'],SC['questions'][q]['text'],costs(q)) for q in g['costs']],
            'score_groups':['| Behaviour | Questions |','|---|---|']+[row(x['name'],', '.join(x['questions'])) for x in g['groups']]}
GENRE=r'(<!-- (rules/scoring\.yaml|card\.schema\.json): (\w+)\. [^\n]*-->\n)(.*?)(<!-- /\2 -->\n)'
MDTXT={}
for _name,_blocks in gen_tables().items():
    _old=open(RULESDIR+_name).read(); _seen=[]
    def _fill(m,_blocks=_blocks,_seen=_seen): _seen.append(m.group(3)); return m.group(1)+'\n'.join(_blocks[m.group(3)])+'\n'+m.group(5)
    _new=re.sub(GENRE,_fill,_old,flags=re.S)
    assert sorted(_seen)==sorted(_blocks), 'rules/'+_name+': it needs one marked table for each of '+', '.join(_blocks)+' (the "<!-- rules/scoring.yaml: ... -->" and "<!-- card.schema.json: ... -->" lines)'
    if _new!=_old:
        assert not os.environ.get('CI'), 'rules/'+_name+': its tables differ from rules/scoring.yaml or rules/card.schema.json; run python3 -I site/build.py and commit the result'
        open(RULESDIR+_name,'w').write(_new); print('wrote the tables in rules/'+_name)
    # What the site shows: the file as written, without the markers.
    MDTXT[_name]=re.sub(r'<!-- /?(rules/scoring\.yaml|card\.schema\.json)[^\n]*-->\n','',_new)
# One rule list: the rules in rules/template.md (shown on the site) carry the same numbers and titles as those in CLAUDE.md,
# so "rule 9" means the same thing wherever it is said.
def _rules(path,head):
    sec=open(path).read().split('\n## '+head+'\n',1)[1].split('\n## ',1)[0]
    return [(int(n),t.rstrip('.')) for n,t in re.findall(r'^(\d+)\. \*\*(.+?)\*\*',sec,re.M)]
assert _rules(ROOT+'CLAUDE.md',"The rules that don't bend")==_rules(RULESDIR+'template.md','Rules'), 'CLAUDE.md and rules/template.md must list the same rules, with the same numbers and titles: '+str(_rules(ROOT+'CLAUDE.md',"The rules that don't bend"))+' vs '+str(_rules(RULESDIR+'template.md','Rules'))
# The areas in card order, by the prefix of their question IDs. Each area's row in a card's "Areas" table gets an anchor: #ar-<tool>-<key>
PFX=''.join(SC['areas'])
AREAN=[x['name'] for x in SC['areas'].values()]
SC_KEY={x['name']:k for k,x in SC['areas'].items()}
AREAK={x['name']:x['anchor'] for x in SC['areas'].values()}
CONCERN=[x['name'] for k,x in SC['areas'].items() if k!=MONEY['area']]
def verdict(ans):
    # The mark and the verdict of one answer. "Opt" is "Yes, not by default", "Req" is "Yes, on request"; neither costs points.
    for w,v in (('Not checked','NC'),('Not allowed','NA'),("Doesn't apply",'DNA')):
        if ans.startswith(w): return None,v
    m=re.match(r'\{(.)\} (Yes, not by default|Yes, on request|Yes|No|Partly)\b',ans)
    return m.group(1),{'Yes, not by default':'Opt','Yes, on request':'Req'}.get(m.group(2),m.group(2))
QS=[];QMARK={};QCELL={};ONREQ=set();MK={'Good':'+','Note':'~','Concern':'!'}
for _i,_x in SC['questions'].items():
    assert re.fullmatch(r'[A-Z]\d+',_i) and _i[0] in SC['areas'] and set(_x)<={'text','yes_mark','no_mark','partly','partly_means','doesnt_apply','note_on_request','second_check'} and _x.get('partly') in (None,'concern','never'), 'rules/scoring.yaml: question '+_i+' is malformed'
    QS.append((_i,SC['areas'][_i[0]]['name'],_x['text']))
    QCELL[_i]={'Yes':yes_cell(_x),'No':_x['no_mark']}
    QMARK[_i]={v:{MK[w] for w in re.findall(r'Good|Note|Concern',c)} for v,c in QCELL[_i].items()}
    # Partly is a Note, except where the file says "partly: concern": there Partly is a Concern and costs points.
    QMARK[_i]['Partly']={'~'}
    # note_on_request: the mark follows the verdict ("Yes, on request" a Note, every other Yes a Concern), so the build checks it.
    ONREQ.update({_i} if _x.get('note_on_request') else ())
    assert all(QMARK[_i].values()), 'rules/scoring.yaml: '+_i+' has a mark cell with no mark'
PARTLYC={i for i,x in SC['questions'].items() if x.get('partly')=='concern'}
# What Partly means on a question, where scoring.yaml gives it: shown beside every Partly answer on that question.
PMEANS={i:x['partly_means'] for i,x in SC['questions'].items() if x.get('partly_means')}
# second_check: a Yes needs a second check with another method, named with its evidence on the answer.
SECOND={i for i,x in SC['questions'].items() if x.get('second_check')}
for q in PARTLYC: QMARK[q]['Partly']={'!'}
# For authors: the verdict that earns a Good answer on each question, from its mark cells in rules/scoring.yaml ("Good" alone,
# or "Good; Note if ..." with the condition that makes it a Note).
def goodwhen(q):
    g=[(v,c) for v,c in QCELL[q].items() if c.startswith('Good')]
    assert len(g)==1, 'rules/scoring.yaml: '+q+' needs exactly one mark cell that starts with Good, for the For authors page'
    v,c=g[0]; rest=c[len('Good'):].lstrip('; ')
    return v+(' ('+rest+')' if rest else '')
def unless(ws):
    # A tag's "unless" (["T1 no", "T4 yes"]): any of these answers leaves the tag out.
    cs=[cond(w,'a tag\'s unless') for w in ws]
    return lambda A:any(A[q][1]==v for q,v in cs)
def money(A,held=()):
    # The Money label: the first label whose answers all hold. When none does: "Not allowed" if the licence forbids answering
    # one of its questions, else "Not checked" (one is not checked or held back).
    for l,cs in MWHEN.items():
        if all(A[q][1]==v and q not in held for q,v in cs): return l
    if any(A[q][1]=='NA' for q in MQS): return 'Not allowed'
    assert any(A[q][1]=='NC' or q in held for q in MQS), 'Money: no label fits '+', '.join(q+' '+str(A[q][1]) for q in MQS)+' (see money in rules/scoring.yaml)'
    return 'Not checked'
KEYS=[(k,x['question'],x['short'],x['from']) for k,x in SC['keys'].items()]
KMODE={k:x['mark'].capitalize() for k,x in SC['keys'].items()}
# names: a source question whose Concern the key answer must name, with the words it must hold.
KNAMES={k:x.get('names',{}) for k,x in SC['keys'].items()}
assert all(q in x['from'] and isinstance(w,str) and w for k,x in SC['keys'].items() for q,w in x.get('names',{}).items()), 'rules/scoring.yaml: a key question names a question it isn\'t built from'
assert all(m in ('Strongest','Best') for m in KMODE.values()) and all(q in QCELL for k in KEYS for q in k[3]), 'rules/scoring.yaml: a key question has an unknown mark or source'
assert len(KEYS)==10, 'rules/scoring.yaml: ten key questions (the site and the rules say "ten")'
# The schema lists the key questions and the areas a card writes a one-line reason for; they follow rules/scoring.yaml.
assert list(SCHEMA['properties']['key']['properties'])==list(SC['keys']) and SCHEMA['properties']['key'].get('required')==list(SC['keys']), 'card.schema.json: "key" must list the key questions of rules/scoring.yaml, in order'
assert list(SCHEMA['properties']['areas']['properties'])==[x['name'] for x in SC['areas'].values()], 'card.schema.json: "areas" must list the areas of rules/scoring.yaml, in order'
QIDS=[q[0] for q in QS]; QTXT={q[0]:q[2] for q in QS}
NOPARTLY={i for i,x in SC['questions'].items() if x.get('partly')=='never'}; DNA={i for i,x in SC['questions'].items() if x.get('doesnt_apply')}
QAREA={q:AREAN[PFX.index(q[0])] for q in QIDS}
assert len(QIDS)==len(set(QIDS)) and QIDS, 'rules/scoring.yaml: no questions, or a question listed twice'
ANS=re.compile(r'^(\{[+~!]\} (Yes, not by default\. |Yes, on request\. |Yes\b|No\b|Partly\b)|(Not checked|Not allowed|Doesn\'t apply)\. \S)')
RANK={'!':3,'~':2,'+':1}
# Cards are data (cards/*.yaml, checked against rules/card.schema.json). The page is made from Markdown rendered
# from that data, so every check below reads one format. Scores, the Money label and key-question marks are worked out here, never written by hand.
SYM={'good':'+','note':'~','concern':'!'}
def mark_md(d): return '{'+SYM[d['mark']]+'} ' if d.get('mark') else ''
def ans_md(a):
    v=a['verdict']
    if v in ('Not checked','Not allowed',"Doesn't apply"): return f'{v}. {a["text"]}'
    return mark_md(a)+v+('. '+a['text'] if a.get('text') else '')+(' Second check: '+a['second_check'] if a.get('second_check') else '')
# Front-page tags: each from one answer, by the tags in rules/scoring.yaml, never picked by hand.
TAGS=[(x['from'],x['answer'],x['tag'],x['kind']) for x in SC['tags']]
assert all({'from','answer','tag','kind'}<=set(x)<={'from','answer','tag','kind','unless'} and x['answer'] in ('Yes','No','Partly') and x['kind'] in ('Critical','Positive','None') for x in SC['tags']), 'rules/scoring.yaml: a tag is malformed (answer is Yes, No or Partly, kind is Critical, Positive or None, and maybe unless)'
assert TAGS and all(q in QIDS for q,v,_l,k in TAGS), 'rules/scoring.yaml: a tag names an unknown question'
UNLESS={(x['from'],x['answer']):unless(x['unless']) for x in SC['tags'] if 'unless' in x}
# No gap between marks and tags: every answer the mark table can make a Concern has a tag row (or a row saying why it has none).
_gap=[q+' '+v for q in QIDS for v in ('Yes','No','Partly') if '!' in QMARK[q][v] and not any(t[0]==q and t[1]==v for t in TAGS)]
assert not _gap, 'rules/scoring.yaml: no tag for these Concern answers: '+', '.join(_gap)
def tagsof(card):
    # The tags of one card: (label, question) lists for critical, optional and positive. "unless" leaves a tag out when another says it.
    A=card['answers']; crit=[]; opt=[]; pos=[]
    AV={q:verdict(ans_md(x)) for q,x in A.items()}
    for q,v,label,kind in TAGS:
        if kind=='None' or ((q,v) in UNLESS and UNLESS[(q,v)](AV)): continue
        mk=A[q].get('mark'); verd=A[q]['verdict']
        if kind=='Critical' and verd==v and (mk=='concern' or v=='Partly'): crit.append((label,q))
        elif kind=='Critical' and mk=='concern' and v=='Yes' and verd in ('Yes, not by default','Yes, on request'): opt.append((label,q))
        if kind=='Positive' and mk=='good' and verd==v: pos.append((label,q))
    def uniq(xs): return [x for i,x in enumerate(xs) if x[0] not in [y[0] for y in xs[:i]]]
    # Every Concern by default shows: its own critical tag, or one its "None" row names as covering it.
    shown={l for l,_q in crit}
    for q,v,label,kind in TAGS:
        if kind=='None' and A[q].get('mark')=='concern' and A[q]['verdict']==v:
            assert shown&set(re.findall(r'"([^"]+)"',label)), q+' '+v+' is a Concern, but none of the tags its row names ('+label+') shows'
    return uniq(crit),uniq(opt),uniq(pos)
HELD=r'(\d+) items? \(rule 9\): ([A-Z]\d+(?:, [A-Z]\d+)*)$'  # "<n> item(s) (rule 9): <question IDs>"; the dates are kept privately, not in the repository
def heldq(hb):
    # The questions a "Held back" row names (rule 9), or none.
    m=re.match(HELD,hb) if hb else None
    return set(m.group(2).split(', ')) if m else set()
# How each mark, state and result is shown, the same on every view: its label, its CSS classes, its Lucide icon (site/icons.py)
# and what it means. Major is how a Concern that costs the severe tier or more is shown, not a mark of its own: the card keeps
# "concern", and the cost decides. The grey states cost nothing (Off by default, On request, Doesn't apply) or are still open
# (Not checked, Held back, Not allowed: an open answer counts at its highest cost until it is answered). Signs of malware and
# Not scored are results in place of a score.
STATES={
    'good':('Good','good','circle-check','A finding in your favour; costs nothing'),
    'note':('Note','note','info','Worth knowing; costs nothing'),
    'concern':('Concern','bad','circle-alert','In the default setup; costs points'),
    'major':('Major','bad hi','triangle-alert','A major concern: in the default setup, at the severe cost or more'),
    'off':('Off by default','off','toggle-left','Only after a setting or choice you make; costs nothing (rule 5)'),
    'req':('On request','off req','mouse-pointer-click','Only when you start it, each time; costs nothing (rule 5)'),
    'nc':('Not checked','none nc','circle-help','Not checked or not settled yet; counts at its highest cost until it is'),
    'held':('Held back','none held','eye-off','Withheld for now under rule 9; counts at its highest cost until it is published'),
    'na':('Not allowed','none na','ban','The licence forbids analysing this, so the tool gets no score'),
    'dna':("Doesn't apply",'none dna','circle-minus',"The question doesn't apply to this tool; costs nothing"),
    'malware':('Signs of malware','malware','shield-alert','A confirmed P9 finding, with a second check; replaces the score'),
    'notscored':('Not scored','notscored','circle-slash','No number is given: the licence forbids the analysis, or the malware check (P9) wasn\'t done'),
}
SCLS={cls:k for k,(_l,cls,_i,_m) in STATES.items()}
def state_of(html):
    # The state a mark's HTML shows, from its classes.
    m=re.search(r'class="(?:mk|mark) ([^"]*)"',html); return SCLS.get(m.group(1)) if m else None
def state_html(key,tip='',tag='span',inner=None,attrs=''):
    # One state as a mark: its icon (from its classes in the CSS), its label (or inner), and its meaning on hover.
    lab,cls,_i,means=STATES[key]
    return f'<{tag} class="mk {cls}"{attrs} title="{tip or means}">{inner if inner is not None else lab}</{tag}>'
def concern_span(qs,A,SETS,k,extra=''):
    # How a Concern shows (rules/template.md, "How a Concern answer is shown"): "Concern", or "Major" when it costs the
    # severe tier or more; "Off by default" or "On request" (grey) when only a choice you make brings it. A line or table row outside the answers names the
    # answers it backs (qs) and shows the costliest of theirs. extra is HTML put inside the mark after its label (an answer's
    # cost). Returns (rank, html), or None when no named answer is a Concern.
    best=None
    for q in qs:
        mk,v=A[q]
        if mk!='!': continue
        if v in ('Opt','Req'):
            st,rank='off' if v=='Opt' else 'req',-1
            tip=('Only after a setting or choice you make' if v=='Opt' else 'Only when you start it, each time')+', so it costs nothing (rule 5). The behaviour is a Concern when it happens'
        else:
            c,top,o=SETS.get(q,(0,None,False)); rank=c
            tip=f'Counted with {top}: the same behaviour' if top else (f'Held back, so it counts at its highest cost ({c}) until it is published' if o else f'Costs {c} in its area\'s score') if c else 'Costs nothing: the release is traced to public source'
            # Signs of malware keep their own result, never an ordinary Major (rules/scores.md: it replaces the score).
            st='malware' if q==GSC['malware'] and not o else 'major' if c>=GT['severe'] else 'concern'
        if best and best[0]>=rank: continue
        lv=STATES[st][0]; name='Major concern' if st=='major' else lv
        best=(rank,state_html(st,f'{name}{" from "+q if len(qs)>1 or q[0]!=k else ""}. {tip}',inner=lv+extra))
    return best
# Hand-written text names questions (P4, K1); every name must still be in rules/scoring.yaml, so a renamed or removed one can't
# linger in the docs, the prompt or a card.
REFID=re.compile(r'\b[PDGCTMK]\d{1,2}\b')
def stale_refs(text):
    return sorted({m for m in REFID.findall(text) if m not in QCELL and m not in SC['keys']})
# Scores (rules/scores.md; every number in rules/scoring.yaml, "scores"): each area starts at 100, every Concern by default takes off its cost.
GSC=SC['scores']; RUBRICV=GSC['version']; GT=GSC['tiers']
GCOST={q:({v:GT[x] for v,x in c.items()} if isinstance(c,dict) else GT[c]) for q,c in GSC['costs'].items()}
assert all(isinstance(v,str) for c in GCOST.values() if isinstance(c,dict) for v in c), 'rules/scoring.yaml: a scores cost names a verdict YAML read as true/false: quote "Yes" and "No"'
GGROUP={q:x['name'] for x in GSC['groups'] for q in x['questions']}
assert all(q in QIDS for q in list(GCOST)+list(GGROUP)) and GSC['malware'] in GCOST, 'rules/scoring.yaml: scores names an unknown question'
assert len(GGROUP)==sum(len(x['questions']) for x in GSC['groups']) and all(len({q[0] for q in x['questions']})==1 for x in GSC['groups']), 'rules/scoring.yaml: a group under scores repeats a question or spans two areas'
_canc={q for q in QIDS if any('!' in QMARK[q][v] for v in QMARK[q])}
assert _canc==set(GCOST), 'rules/scoring.yaml: every question that can be a Concern needs a cost under scores, and only those: '+', '.join(sorted(_canc^set(GCOST)))
def qcost(q,v):
    c=GCOST.get(q,0); return c.get(v,0) if isinstance(c,dict) else c
# A cost given by verdict names exactly the verdicts that can be Concerns, so none silently costs 0.
for _q,_c in GCOST.items():
    if isinstance(_c,dict): assert set(_c)=={v for v in ('Yes','No','Partly') if '!' in QMARK[_q][v]}, 'rules/scoring.yaml: scores, costs, '+_q+' must name each verdict that can be a Concern'
assert 0<=GSC['lowest_weight']<=1, 'rules/scoring.yaml: scores, lowest_weight is between 0 and 1'
assert [q for q,c in GSC['costs'].items() if c=='malware']==[GSC['malware']], 'rules/scoring.yaml: scores, only the malware question costs the malware tier'
GWAIVE=GSC.get('waived',{}); GCOVER=GSC.get('covered',{})
assert all(q in GCOST and all(w in GCOST for w in ws) for q,ws in GCOVER.items()), 'rules/scoring.yaml: scores, covered, names an unknown question'
assert all(q in GCOST and all(w in QIDS for w in ws) for q,ws in GWAIVE.items()), 'rules/scoring.yaml: scores, waived, names an unknown question'
def maxcost(q):
    c=GCOST.get(q,0); return max(c.values()) if isinstance(c,dict) else c
def charges(A,held=(),open_=True):
    # What each answer costs as the score counts it (rules/scores.md): {question: (cost, the question it is counted with or None, open)}.
    # Each Concern by default with its cost; an answer not checked or held back with its highest cost (when open_); a waived
    # cost isn't charged. In a group, only the highest cost counts and the others say where they're counted.
    out={}
    for q,(m,v) in A.items():
        if q not in GCOST or any(A[w][1]=='Yes' and A[w][0]=='+' for w in GWAIVE.get(q,())) or any(A[w][0]=='!' and A[w][1] in ('Yes','No','Partly') for w in GCOVER.get(q,())): continue
        if m=='!' and v in ('Yes','No','Partly') and q not in held: out[q]=[qcost(q,v),None,False]
        elif open_ and (v in ('NC','NA') or q in held): out[q]=[maxcost(q),None,True]
    for x in GSC['groups']:
        hit=[q for q in x['questions'] if q in out]
        if len(hit)>1:
            top=max(hit,key=lambda q:(out[q][0],-hit.index(q)))
            for q in hit:
                if q!=top: out[q][1]=top
    return {q:tuple(x) for q,x in out.items()}
def _areas(ch):
    areas={}
    for ar in CONCERN:
        k=SC_KEY[ar]; items=sorted(((q,c,top,o) for q,(c,top,o) in ch.items() if q[0]==k),key=lambda x:int(x[0][1:]))
        areas[ar]=(max(0,100-sum(c for _q,c,top,_o in items if not top)),items)
    return areas
def _score(areas):
    lw=GSC['lowest_weight']; avg=sum(x[0] for x in areas.values())/len(areas); low=min(x[0] for x in areas.values())
    return round((1-lw)*avg+lw*low,1),round(avg,1),low
# The key questions run from the highest cost among their sources down, and by area where two are equal (rules/questions.md).
_kord=[(-max(maxcost(q) if q in GCOST else 0 for q in src),PFX.index(src[0][0])) for _k,_q,_s,src in KEYS]
assert _kord==sorted(_kord), 'rules/scoring.yaml: order the key questions by the highest cost among their sources, then by area'
def scored(A,held=()):
    # Area scores from the costs (open answers at their highest cost), then the score: the average and the lowest area,
    # weighted by lowest_weight. An open answer (not checked, not allowed or held back) counts at its highest cost and is
    # shown as open on its line, in the tags and in a line under the score.
    held=set(held); ch=charges(A,held)
    areas=_areas(ch); score,avg,low=_score(areas)
    openq=sorted((q for q,(_c,_t,o) in ch.items() if o),key=lambda q:(PFX.index(q[0]),int(q[1:])))
    kind='score'
    why=['Answers not checked or held back count at their highest cost ('+', '.join(openq)+')'] if openq else []
    nna=sum(v=='NA' for _m,v in A.values()); mq=GSC['malware']
    if nna: kind='notscored'; why=[f'Its licence forbids analysing it ({nna} of {len(A)} answers not allowed), so it gets no score: what couldn\'t be checked can\'t count for it or against it']
    elif A.get(mq,(None,''))[1]=='NC': kind='notscored'; why=[f'The malware check ({mq}) wasn\'t done, so it gets no score: a number would read as a finding']
    if any(q==mq and not o for q,(_c,_t,o) in ch.items()): kind='malware'; why=[f'The analysis found signs of malware ({mq}), so it gets no score']
    return {'kind':kind,'score':score,'avg':avg,'low':low,'areas':areas,'open':openq,'why':why}
def sround(x): return int(x+0.5)
def gtext(G):
    # The result in words where a number would mislead.
    return {'malware':'Signs of malware','notscored':'Not scored'}.get(G['kind'],f'{sround(G["score"])} / 100')
def gsym(G):
    # The square badge's big text: the score; ? when not scored; X for signs of malware (the site and the badges draw their icons
    # in place of these; the text stays for where no icon can go).
    return {'malware':'X','notscored':'?'}.get(G['kind'],str(sround(G['score'])))
