"""Tests for how site/build.py sets scores, marks and tags.

Usage: python3 -I tests/test_build.py   (exit 1 on any failure)

They load the rules (site/rules.py) and the card functions (site/cards.py), which read the
registry but no card file, then check made-up answers. Each case is a mistake a review found, kept here so
it can't come back. Add a case when you change how scores, marks or tags are set.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'site'))
import rules  # noqa: E402
import cards  # noqa: E402
B = {**vars(rules), **vars(cards)}

SYM = {'+': 'good', '~': 'note', '!': 'concern'}
FAILED = []


def check(name, ok, detail=''):
    print(('ok    ' if ok else 'FAIL  ') + name + ('' if ok else '  ' + str(detail)))
    if not ok:
        FAILED.append(name)


def benign():
    """Every question answered with the verdict its table marks Good."""
    A = {}
    for q in B['QIDS']:
        v = 'Yes' if '+' in B['QMARK'][q]['Yes'] else 'No'
        A[q] = ('+', v)
    return A


def answers(A):
    """The same answers in a card's own form, for the tag functions."""
    back = {'Opt': 'Yes, not by default', 'Req': 'Yes, on request', 'NC': 'Not checked', 'NA': 'Not allowed'}
    return {'answers': {q: dict({'verdict': back.get(v, v), 'text': ''}, **({'mark': SYM[m]} if m else {})) for q, (m, v) in A.items()}}


def with_(**ch):
    A = benign()
    A.update(ch)
    return A


# Every question that can be a Concern by default costs points in its own area, and shows a critical tag.
for q in B['GCOST']:
    v = next(v for v in ('Yes', 'No', 'Partly') if '!' in B['QMARK'][q][v])
    A = with_(**{q: ('!', v)})
    if q in ('P5', 'T3', 'T4'): A.update(T3=('!', 'No'), T4=('!', 'No'))  # a traced release waives these
    g = B['scored'](A)
    check(q + ' ' + v + ' costs points in its own area', g['areas'][B['QAREA'][q]][0] < 100, g['areas'][B['QAREA'][q]])
    crit, _opt, _pos = B['tagsof'](answers(A))
    check(q + ' ' + v + ' shows a critical tag', crit, crit)

# A tool with nothing to report shows no critical tag.
A = benign()
crit, opt, _ = B['tagsof'](answers(A))
check('all-Good answers show no critical or optional tag', not crit and not opt, (crit, opt))

# A closed-source tool answers T3, T4 and T7 "No" only because it has no public source; it gets one tag for that, not four
# (no "Rebuild doesn't match" tag on a tool nobody can rebuild).
A = with_(T1=('!', 'No'), T3=('!', 'No'), T4=('!', 'No'), T7=('!', 'No'), T6=(None, 'NC'))
crit, _, _ = B['tagsof'](answers(A))
check('a closed-source tool shows "Closed source" and no rebuild, CI or licence tag', [l for l, q in crit if q[0] in 'TC'] == ['Closed source'], crit)
A = with_(T3=('!', 'No'), T4=('!', 'No'), T7=('!', 'No'))
crit, _, _ = B['tagsof'](answers(A))
check('an open, untraced, unlicensed tool shows both tags', {'Not traced to source', 'No open-source licence'} <= {l for l, _q in crit}, crit)
# Either check traces the release (the T3 cost is waived when T4 is Yes), so the tag says nothing a matching rebuild disproves.
A = with_(T3=('~', 'No'), T4=('+', 'Yes'))
crit, _, _ = B['tagsof'](answers(A))
check('a release a matching rebuild traces isn\'t tagged "Not traced to source"', 'Not traced to source' not in {l for l, _q in crit}, crit)

# What each Concern costs, as answers show it.
L = B['charges'](with_(P2=('!', 'Yes')))
check('a P2 Concern costs 15', L.get('P2') == (15, None, False), L)
check('an optional P2 Concern costs nothing (rule 5)', 'P2' not in B['charges'](with_(P2=('!', 'Opt'))))
L = B['charges'](with_(D2=('!', 'Yes'), D3=('!', 'Yes')))
check('of two Concerns in one group, the cheaper says where it is counted', L['D3'] == (40, None, False) and L['D2'][1] == 'D3', L)

# A Concern line or table row shows the costliest of the answers it names; only optional answers show "Off by default";
# no Concern among them shows nothing; a severe one is filled.
A = with_(D2=('!', 'Yes'), G2=('!', 'Opt'))
S = B['charges'](A)
sp = B['concern_span'](['G2', 'D2'], A, S, 'T')
check('a row naming a Concern and an optional answer shows "Concern"', sp and '>Concern<' in sp[1] and 'hi' not in sp[1], sp)
sp = B['concern_span'](['G2'], A, S, 'G')
check('a row naming only an optional answer shows "Off by default"', sp and '>Off by default<' in sp[1], sp)
check('a row naming no Concern answer shows nothing', B['concern_span'](['D1'], A, S, 'D') is None)
A = with_(D3=('!', 'Yes'))
sp = B['concern_span'](['D3'], A, B['charges'](A), 'D')
check('a severe Concern is filled', sp and 'bad hi' in sp[1], sp)

# Partly on P3 and G3 is a Concern; other Partly answers are Notes.
check('P3 and G3 Partly can only be a Concern', B['QMARK']['P3']['Partly'] == {'!'} and B['QMARK']['G3']['Partly'] == {'!'})
check('other Partly answers are Notes', all(B['QMARK'][q]['Partly'] == {'~'} for q in B['QIDS'] if q not in ('P3', 'G3')))

# A choice you make never costs points (rule 5), but shows as an optional tag.
A = with_(G2=('!', 'Opt'), P4=('~', 'Req'))
check('"Yes, not by default" costs nothing', B['scored'](A)['score'] == 100)
crit, opt, _ = B['tagsof'](answers(A))
check('"Yes, not by default" shows as an optional tag', any(q == 'G2' for _l, q in opt) and not crit, (crit, opt))

# Rule 9, protected content: only a C1-C3 Yes withholds the how, and then fully.
W = B['withheld_error']
WOK = {'verdict': 'Yes', 'text': 'For its previews, in memory only. ' + B['WITHHELD_TEXT'], 'evidence': B['WITHHELD_EV']}
check('a C1 Yes can withhold the how (rule 9)', W('C1', WOK) is None, W('C1', WOK))
check('only C1 to C3 can withhold the how', W('P4', WOK) is not None)
check('a No never withholds its evidence', W('C1', {**WOK, 'verdict': 'No'}) is not None)
check('a withheld answer links no evidence', W('C1', {**WOK, 'evidence': 'Withheld (rule 9). https://example.com'}) is not None)
check('a withheld answer says so in its text', W('C1', {**WOK, 'text': 'For its previews.'}) is not None)
check('an answer with its evidence is not withheld', W('C1', {'verdict': 'Yes', 'text': 'It decrypts.', 'evidence': 'https://x'}) is None)

# Money: its label comes from M1 and M2, the first whose answers all hold; else "Not allowed" when the licence leaves them
# unsettled, or "Not checked" when one is not checked or held back.
check('Money is Free with no price', B['money'](benign()) == 'Free')
check('Money is Free when only donations are asked for', B['money'](with_(M3=('~', 'Yes'))) == 'Free')
check('Money is Paid when M1 is Yes', B['money'](with_(M1=('~', 'Yes'))) == 'Paid')
check('Money is Paid when M1 and M2 are Yes', B['money'](with_(M1=('~', 'Yes'), M2=('~', 'Yes'))) == 'Paid')
check('Money is Paid extras when M2 is Yes and M1 No', B['money'](with_(M2=('~', 'Yes'))) == 'Paid extras')
check('Money is never Free or Paid extras while M1 is unsettled', B['money'](with_(M1=(None, 'NA'), M2=('~', 'Yes'))) == 'Not allowed' and B['money'](with_(M1=(None, 'NC'))) == 'Not checked')
check('Money is never Free while M2 is unsettled', B['money'](with_(M2=(None, 'NA'))) == 'Not allowed' and B['money'](with_(M2=(None, 'NC'))) == 'Not checked')
check('Money is "Not checked" while M2 is held back', B['money'](benign(), {'M2'}) == 'Not checked')
check('Money is "Not allowed" when the licence leaves M1 unsettled', B['money'](with_(M1=(None, 'NA'))) == 'Not allowed')
check('the Money table says when each label shows', [B['money_when'](l) for l in B['MLAB']] == ['M1 is Yes', 'M1 is No and M2 is Yes', 'M1 is No and M2 is No', 'No label above applies, because the licence forbids answering M1 or M2', 'No label above applies, and M1 or M2 is not checked or held back'], [B['money_when'](l) for l in B['MLAB']])

# The "Held back" row (rule 9).
H = re.compile(B['HELD'])
check('held-back row', bool(H.match('3 items (rule 9): P3, P4')) and bool(H.match('1 item (rule 9): D3, D9')))
check('held-back row carries no dates (they are kept privately)', not H.match('1 item until 1 Jan 2030 (rule 9): D3, D9'))
check('held-back row needs question IDs', not H.match('1 item (rule 9)'))

# No word that judges slips through (rule 7).
check('the judging-word list catches "safe"', bool(re.search(r'\b(safe|spyware|shady)\b', 'this tool is safe')))

# Issue labels: the forms' own examples find their tool.
import issue_label
reg = json.load(open(os.path.join(ROOT, 'registry', 'tools.json')))
check('correction for "HoleShot 0.24.0" is labelled holeshot', issue_label.find('### Card\n\nHoleShot 0.24.0\n\n### The line\n\nD3', reg) == ('correction', 'holeshot'))
check('request for "MXB App" is labelled mxb-app', issue_label.find('### Tool name\n\nMXB App\n\n### Version\n\n1', reg) == ('analyse', 'mxb-app'))
check('an unknown tool gets no tool label', issue_label.find('### Tool name\n\nSomething New\n', reg) == ('analyse', '-'))

# A web page's release files are the ones on its own site; a runtime it links to elsewhere is not the tool's release (issue #27).
import releases_fetch
page = ('<a href="https://aka.ms/vs/16/release/vc_redist.x64.exe">VC++</a> <a href="/files/Tool-1.2.zip">zip</a> '
        '<a href="https://mega.nz/file/abc#key">mirror</a> <a href="https://mega.nz/folder/xyz#key">folder</a>')
check('a web page keeps only its own files and file-host links', releases_fetch.page_links('https://forum.example/topic?t=1', page)
      == (['https://forum.example/files/Tool-1.2.zip'], ['https://mega.nz/file/abc#key']), releases_fetch.page_links('https://forum.example/topic?t=1', page))
check('a page linking only to a runtime elsewhere has no release files', releases_fetch.page_links('https://forum.example/t', page.split(' <a href="/files')[0]) == ([], []))

# A tag's "unless" leaves it out only for the answer it names, and a mistyped one stops the build.
check('"unless" holds for its answer only', B['unless'](['T1 no'])(with_(T1=('!', 'No'))) and not B['unless'](['T1 no'])(with_(T1=('+', 'Yes'))))
check('"unless" holds for any of its answers', B['unless'](['T1 no', 'T4 yes'])(with_(T4=('+', 'Yes'))) and not B['unless'](['T1 no', 'T4 yes'])(with_(T4=('!', 'No'))))
try:
    B['unless'](['T1 maybe'])
    check('an unknown answer in "unless" stops the build', False)
except AssertionError:
    check('an unknown answer in "unless" stops the build', True)
# Text that names a removed question is caught.
check('a removed question named in text is caught', B['stale_refs']('P4 and K1 stay; G13 and K11 are gone') == ['G13', 'K11'], B['stale_refs']('P4 and K1 stay; G13 and K11 are gone'))
# Mistakes in rules/scoring.yaml stop the build.
import tempfile
def loads(text):
    with tempfile.NamedTemporaryFile('w', suffix='.yaml', delete=False) as t:
        t.write(text)
    try:
        B['load_yaml'](t.name)
        return True
    except Exception:
        return False
    finally:
        os.unlink(t.name)
check('a name used twice in one place stops the build', not loads('money:\n  Free: {means: a}\n  Free: {means: b}\n') and loads('money:\n  Free: {means: a}\n'))
check('a Partly that is a Concern needs a tag too', all(any(t[0] == q and t[1] == 'Partly' for t in B['TAGS']) for q in B['PARTLYC']))
check('"Note if only on request" comes from its field', B['ONREQ'] == {q for q, x in B['SC']['questions'].items() if x.get('note_on_request')} and B['ONREQ'])

# The card format comes from rules/card.schema.json: the header rows in its order with "Files checked" made by the build,
# and each area's answers in the report section named after it (one name per area, wherever a reader sees it).
check('"Files checked" comes right before "Analysed on"', B['HEADER'][B['HEADER'].index('Analysed on') - 1] == 'Files checked', B['HEADER'])
check('each area section holds that area\'s answers', [k for k in B['SECTIONS'].values() if k] == list(B['SC']['areas']), B['SECTIONS'])
check('each area has one name: its report section is named after it', all(B['SECTIONS'][x['name']] == k for k, x in B['SC']['areas'].items()), B['SECTIONS'])

# For authors: the "Good when" column comes from the mark table, with the condition that makes a Good answer a Note.
check('Good when P3 is "Yes"', B['goodwhen']('P3') == 'Yes')
check('Good when P1 keeps its Note condition', B['goodwhen']('P1') == "No (Note if a file players download isn't on VirusTotal)", B['goodwhen']('P1'))
check('every question has a Good answer for authors', all(B['goodwhen'](q) for q in B['QIDS']))


# Card text reaches the page as Markdown without HTML, and links only to https addresses.
def html_refused(d):
    try:
        B['no_html']('t.yaml', d)
        return False
    except AssertionError:
        return True


check('a tag in the summary is refused', html_refused({'summary': 'A plugin <img src=x onerror=alert(1)>'}))
check('a tag in an answer is refused', html_refused({'answers': {'P2': {'text': 'Sends <script>x</script>', 'evidence': 'e'}}}))
check('a tag in the tool name is refused', html_refused({'tool': '<b>Tool</b>'}))
check('a link that isn\'t https is refused', html_refused({'answers': {'P2': {'text': 'See [this](javascript:alert(1))'}}}))
check('a Markdown image is refused', html_refused({'answers': {'P2': {'text': 'Counter ![x](https://example.com/pixel.png)'}}}))
check('< inside code, a lone < and an https link pass', not html_refused({'summary': 'Prints `#<n>`, 1 < 2, [VT](https://www.virustotal.com/gui/file/0)'}))


# A made-up card whose every answer is Good, built from the rules, so these tests need no real card.
def made_up_card():
    answers = {}
    for q in B['QIDS']:
        v = next(v for v, c in B['QCELL'][q].items() if c.startswith('Good'))
        answers[q] = {'verdict': v, 'mark': 'good', 'text': 'Made up.', 'evidence': 'https://example.com/evidence'}
    return {'tool': 'Example', 'version': '1.0', 'summary': 'A made-up tool for the tests.',
            'header': {'What it is': 'A made-up tool.', 'In one line': 'A made-up tool', 'Category': B['CATS'][0], 'Author': 'Nobody (made up)',
                       'Game': 'MX Bikes', 'mxb-mods.com': 'None found', 'Homepage': 'None found', 'GitHub': 'None found',
                       'Version analysed': '1.0', 'Analysed on': '1 Jan 2026', 'Method': 'Made up: `claude-example`, medium effort.'},
            'files': [{'name': 'example.zip', 'sha256': '0' * 64}],
            'key': {k: 'No. Made up' for k, _q, _s, _src in B['KEYS']}, 'areas': {ar: 'Made up.' for ar in B['AREAN']},
            'sections': [], 'answers': answers, 'history': [{'date': '1 Jan 2026', 'change': 'Made-up card.'}]}


check('a made-up card with every answer Good passes the card checks', bool(B['check_card']('t.yaml', made_up_card())))

# A Yes on P9 (signs of malware) is confirmed by a second check, and only such an answer has one.
def second_refused(p9):
    d = made_up_card()
    d['answers']['P9'] = p9
    try:
        B['check_card']('t.yaml', d)
        return ''
    except AssertionError as e:
        return str(e)


_p9 = {'verdict': 'Yes', 'mark': 'concern', 'text': 'Hidden code.', 'evidence': 'e'}
check('P9 Yes without a second check is refused', 'needs its second check' in second_refused(_p9), second_refused(_p9))
_sc = 'Ran it in the test host: it wrote to the game\'s memory, `lab/results/x/host.log`.'
check('P9 Yes with a linked second check passes that check', 'second check' not in second_refused({**_p9, 'second_check': _sc}), second_refused({**_p9, 'second_check': _sc}))
check('a second check with no evidence is refused', 'links no evidence' in second_refused({**_p9, 'second_check': 'Checked again.'}))
check('a second check that repeats the first check\'s evidence is refused', 'only the first' in second_refused({**_p9, 'evidence': 'https://example.com/a', 'second_check': 'Read it again: https://example.com/a'}))
check('a second check on P9 No is refused', 'only a Yes' in second_refused({'verdict': 'No', 'mark': 'good', 'evidence': 'e', 'second_check': 'x'}))


# Every answer links its evidence, and a line that names a command links its output.
def evidence_refused(ev):
    d = made_up_card()
    d['answers']['P2']['evidence'] = ev
    try:
        B['check_card']('t.yaml', d)
        return ''
    except AssertionError as e:
        return str(e)


check('evidence without a link is refused', 'links no evidence' in evidence_refused('Its forum post'), evidence_refused('Its forum post'))
check('a command without its output is refused', 'link its output' in evidence_refused('`objdump -p` on `x.dlo` [(here)](https://example.com/)'), evidence_refused('`objdump -p` on `x.dlo` [(here)](https://example.com/)'))
check('a command with its output passes', evidence_refused('`objdump -p` on `x.dlo`; output: `lab/evidence/README.md`') == '')


# Corrections: an open one marks the answers it names and nothing else; a decided one needs its date and reason,
# and a fixed one its history row.
def corr(cs, history=('first card',)):
    return {'corrections': cs, 'history': [{'date': '19 Nov 2026', 'change': h} for h in history]}


def refused(d):
    try:
        B['corrections_md']('t.yaml', d)
        return False
    except AssertionError:
        return True


B['corrections_md']('t.yaml', corr([{'issue': 12, 'questions': ['D3', 'D8'], 'opened': '21 Nov 2026', 'status': 'open'}]))
check('an open correction marks the answers it names', B['CORR']['t.yaml'] == {'D3': [12], 'D8': [12]}, B['CORR'].get('t.yaml'))
B['corrections_md']('t.yaml', corr([{'issue': 9, 'questions': ['D2'], 'opened': '20 Nov 2026', 'status': 'declined', 'closed': '21 Nov 2026', 'reason': 'The evidence is for another release.'}]))
check('a declined correction marks nothing', B['CORR']['t.yaml'] == {})
check('an open correction has no reason yet', refused(corr([{'issue': 1, 'questions': ['D2'], 'opened': '20 Nov 2026', 'status': 'open', 'reason': 'x'}])))
check('a decided correction needs its date and reason', refused(corr([{'issue': 1, 'questions': ['D2'], 'opened': '20 Nov 2026', 'status': 'declined'}])))
check('a fixed correction needs a history row linking its issue', refused(corr([{'issue': 1, 'questions': ['D2'], 'opened': '20 Nov 2026', 'status': 'fixed', 'closed': '21 Nov 2026', 'reason': 'D2 fixed.'}])))
check('a correction names known questions', refused(corr([{'issue': 1, 'questions': ['Z9'], 'opened': '20 Nov 2026', 'status': 'open'}])))

# The comment icon fills in the comment form's card and line fields.
_l = B['correction_link']('HoleShot 0.24.0', 'D3')
check('the correction link fills in the card and the question', 'template=correction.yml' in _l and 'card=HoleShot+0.24.0' in _l and 'line=D3%3A+' in _l, _l)

# The corrections check: open correction issues and the cards' open corrections agree.
import check_corrections
REG = {'hs': {'cards': ['hs-1.yaml']}}
open12 = {'hs-1.yaml': {'corrections': [{'issue': 12, 'questions': ['D3'], 'opened': '21 Nov 2026', 'status': 'open'}]}}
check('an open issue on its card passes', check_corrections.check({12: 'hs'}, REG, open12) == ([], []))
check('an open issue missing from its card fails', bool(check_corrections.check({13: 'hs'}, REG, {'hs-1.yaml': {}})[0]))
check('a card listing a closed issue as open fails', bool(check_corrections.check({}, REG, open12)[0]))
check('an issue without a tool label only warns', check_corrections.check({14: None}, REG, {'hs-1.yaml': {}})[0] == [])

# Scores (rules/scores.md; numbers in rules/scoring.yaml), from made-up answers only: never tuned on a real card.
def G(**ch): return B['scored'](with_(**ch))
g = G()
check('a clean, open, traced tool scores 100', g['kind'] == 'score' and g['score'] == 100 and B['gtext'](g) == '100 / 100', g)
check('Good, Notes and behaviour behind a choice never cost points (rule 5)', G(G2=('!', 'Opt'), P4=('~', 'Req'), D1=('~', 'Yes'))['score'] == 100)
g = G(D3=('!', 'Yes'))
check('one severe finding: area 60, score 76', g['score'] == 76 and B['gtext'](g) == '76 / 100', g)
check('questions in one group count once (D2 with D3)', G(D2=('!', 'Yes'), D3=('!', 'Yes'))['score'] == 76)
check('the others in a group show where they are counted', dict((q, top) for q, _c, top, _o in G(G2=('!', 'Yes'), G3=('!', 'Yes'))['areas']['Your game'][1])['G2'] == 'G3')
check('changing only what you see online (G3 Partly) costs 10, a Yes 40, each counted with G2', G(G3=('!', 'Partly'))['areas']['Your game'][0] == 90 and G(G3=('!', 'Yes'))['areas']['Your game'][0] == 60 and G(G2=('!', 'Yes'), G3=('!', 'Partly'))['areas']['Your game'][0] == 75)
check('two severe findings in one area cost more than one in each of two areas', G(D3=('!', 'Yes'), D4=('!', 'Yes'))['score'] < G(D3=('!', 'Yes'), G3=('!', 'Yes'))['score'])
check('an area stops at 0', G(D3=('!', 'Yes'), D4=('!', 'Yes'), D5=('!', 'Yes'), D7=('!', 'Yes'))['areas']['Your data'][0] == 0)
check('a release traced by either check costs nothing for the other (T3 No, T4 Yes)', G(T3=('!', 'No'), T4=('+', 'Yes'))['score'] == 100)
check('not signed costs nothing when the release is traced', G(P5=('!', 'No'))['score'] == 100 and G(P5=('!', 'No'), T3=('!', 'No'), T4=('!', 'No'))['score'] < 100)
g = G(D3=(None, 'NC'))
check('an unchecked answer is charged its highest cost and shows a plain score, never read as Good', g['kind'] == 'score' and g['score'] == 76 and g['open'] == ['D3'] and B['gtext'](g) == '76 / 100', g)
g = G(P9=(None, 'NC'))
check('a malware check not done gives "Not scored", never a number that reads as a finding', g['kind'] == 'notscored' and B['gtext'](g) == 'Not scored' and 'malware check' in g['why'][0], g)
check('closed source costs 25, and covers the CI build and the licence it can\'t have', G(T1=('!', 'No'))['areas']['Transparency'][0] == 75 and G(T1=('!', 'No'), T6=('!', 'No'), T7=('!', 'No'))['areas']['Transparency'][0] == 75)
check('an open tool still pays for no CI build and no licence', G(T6=('!', 'No'), T7=('!', 'No'))['areas']['Transparency'][0] == 90)
check('a covered answer left open costs nothing', G(T1=('!', 'No'), T6=(None, 'NC'))['score'] == G(T1=('!', 'No'))['score'])
g = B['scored'](with_(), held={'D3'})
check('a held-back answer is charged like an open one', g['score'] == 76 and g['open'] == ['D3'], g)
check('signs of malware give words in place of a score', B['gtext'](G(P9=('!', 'Yes'))) == 'Signs of malware')
g = G(D2=(None, 'NA'))
check('a licence that forbids analysis gives "Not scored" and no number', B['gtext'](g) == 'Not scored', g)
check('an answer not allowed is charged like an open one, never read as Good', g['score'] < 100, g)
check('Money never changes the score', G(M1=('~', 'Yes'), M2=('~', 'Yes'))['score'] == 100)
g = B['scored'](with_(D3=('!', 'Yes')), held={'D3'})
check('a held-back Concern is charged once', g['kind'] == 'score' and g['score'] == 76 and g['open'] == ['D3'], g)
# A tool with no score shows no area numbers either.
for _g in (G(D2=(None, 'NA')), G(P9=('!', 'Yes'))):
    _out = B['glance'](with_(), _g)
    check(f'"{B["gtext"](_g)}" shows no area numbers', all(_out[ar] == '–' for ar in _g['areas']), _out)

# Boundary cases: random mixes of every verdict (Yes, No, Partly, optional, not checked, not allowed) on every question.
# Seeded, so a failure repeats. Whatever the mix, Money gets the label M1 and M2 give, and the scores stay in range and add up.
import random
_rng = random.Random(20261121)
def _valid(q):
    # Every answer a card could give: each verdict with a mark its cell allows; "not by default" and "on request" only where
    # Yes is a Concern (a behaviour that can be switched); not checked and not allowed anywhere but Money (plain Yes or No).
    out = [(m, v) for v in ('Yes', 'No') + (() if q in B['NOPARTLY'] else ('Partly',)) for m in B['QMARK'][q][v]]
    if '!' in B['QMARK'][q]['Yes']: out += [('!', 'Opt'), ('~', 'Req')]
    if q[0] != 'M': out += [(None, 'NC'), (None, 'NA')]
    return out
_VALID = {q: _valid(q) for q in B['QIDS']}
_bad = []
for _n in range(3000):
    A = {q: _rng.choice(_VALID[q]) if _rng.random() < 0.3 else v for q, v in benign().items()}
    _m = B['money'](A)
    _want = 'Paid' if A['M1'][1] == 'Yes' else {'Yes': 'Paid extras', 'No': 'Free'}[A['M2'][1]]
    if _m != _want: _bad.append(('Money', _m, _want, A['M1'], A['M2']))
    g = B['scored'](A)
    if g['kind'] not in ('score', 'notscored', 'malware') or not all(0 <= x[0] <= 100 for x in g['areas'].values()): _bad.append(('score', g['kind'], g['score']))
    # One more Concern by default never raises the score.
    _q = _rng.choice([q for q in B['GCOST'] if A[q][0] == '+' and '!' in B['QMARK'][q]['Yes']] or [None])
    if _q and B['scored']({**A, _q: ('!', 'Yes')})['score'] > g['score']: _bad.append(('more concerns scored higher', _q))
    # Less evidence never scores better: an answer set to "not checked" never raises the score.
    _q = _rng.choice([q for q in B['GCOST'] if A[q][1] not in ('NC', 'NA')] or [None])
    if _q and B['scored']({**A, _q: (None, 'NC')})['score'] > g['score']: _bad.append(('less evidence scored higher', _q))
    # The costs an area shows add up to what it lost (unless it stopped at 0).
    for ar, (sc, items) in g['areas'].items():
        if sc > 0 and 100 - sc != sum(c for _q2, c, top, _o in items if not top): _bad.append(('shown costs do not add up', ar, sc, items))
    if len(_bad) > 5: break
check('3000 random mixes of verdicts give a consistent Money label and scores, and scores that add up', not _bad, _bad[:5])

# How marks and states are shown (STATES in rules.py): a presentation of the scoring, never a change to it.
sys.path.insert(0, os.path.join(ROOT, 'site'))
import icons  # noqa: E402
ST = B['STATES']
check('every mark, state and result has a label, classes, a Lucide icon and a meaning, and no two share classes or icons',
      all(len(x) == 4 and all(x) and x[2] in icons.LUCIDE for x in ST.values())
      and len({x[1] for x in ST.values()}) == len(ST) and len({x[2] for x in ST.values()}) == len(ST))
check('the grey states are never shown as a Concern', all('bad' not in ST[k][1].split() for k in ('off', 'req', 'nc', 'held', 'na', 'dna')))


def shown(q, mk, v, A=None):
    A = {**(A or benign()), q: (mk, v)}
    return B['state_of'](B['concern_span']([q], A, B['charges'](A), q[0])[1])


_sev = [q for q, c in B['GCOST'].items() if q != B['GSC']['malware'] and not isinstance(c, dict) and c >= B['GT']['severe']]
_low = [q for q, c in B['GCOST'].items() if not isinstance(c, dict) and c < B['GT']['severe'] and q not in B['GCOVER']]
check('a Concern at the severe cost shows as Major, a cheaper one as Concern', all(shown(q, '!', 'Yes') == 'major' for q in _sev) and _low
      and all(shown(q, '!', 'Yes' if '!' in B['QMARK'][q]['Yes'] else 'No') == 'concern' for q in _low), (_sev, _low))
check('P3 Partly costs its own, lower cost and shows as Concern', B['qcost']('P3', 'Partly') < B['GT']['severe'] and shown('P3', '!', 'Partly') == 'concern')
check('"Yes, not by default" shows Off by default and "Yes, on request" On request, both costing nothing',
      shown(_sev[0], '!', 'Opt') == 'off' and shown(_sev[0], '!', 'Req') == 'req'
      and B['scored']({**benign(), _sev[0]: ('!', 'Opt')})['score'] == 100 == B['scored']({**benign(), _sev[0]: ('!', 'Req')})['score'])
_A = {**benign(), 'T1': ('!', 'No'), 'T6': ('!', 'No')}
check('a covered Concern keeps its Concern mark at no cost', shown('T6', '!', 'No', _A) in ('concern', 'major') and B['scored'](_A)['areas']['Transparency'][0] == 75)
check('signs of malware is its own result, never an ordinary Major', B['scored']({**benign(), 'P9': ('!', 'Yes')})['kind'] == 'malware' and shown('P9', '!', 'Yes') == 'malware')

# partly_means: the question table's Partly cell gives the meaning, and so does every Partly answer on a card (site/feed.py).
_pm = {q: x['partly_means'] for q, x in B['SC']['questions'].items() if x.get('partly_means')}
check('partly_means shows in the Partly cell of the question table', _pm and all(B['partly_cell'](B['SC']['questions'][q]).endswith(': ' + m) for q, m in _pm.items()), _pm)
check('no question text holds its own Partly definition', not any('(Partly' in x['text'] for x in B['SC']['questions'].values()))
# names: K5 must say "gets around" while G12 is a Concern, so getting around a game check isn't hidden behind a memory change.
def _key5(text, **ch):
    A = with_(**ch)
    rows = {q: '{' + (A[q][0] or ' ') + '} ' + {'Opt': 'Yes, not by default', 'Req': 'Yes, on request'}.get(A[q][1], A[q][1]) + '. x' for q in A}
    d = {'key': {k: 'No. x' for k, *_r in B['KEYS']}}
    d['key']['K5'] = text
    try:
        B['key_answers']('test', d, rows, A, B['charges'](A), set())
        return True
    except AssertionError:
        return False
check('K5 must name G12 while it is a Concern', not _key5('Yes; it patches memory.', G2=('!', 'Yes'), G12=('!', 'Yes'))
      and _key5('Yes; it patches memory and gets around a check.', G2=('!', 'Yes'), G12=('!', 'Yes'))
      and _key5('Yes; it patches memory.', G2=('!', 'Yes')))
# v3: changing the game's own files is counted under P4 only, so P7 never repeats it.
check('P7 is a Concern only for content you did not pick', 'changes the game' not in B['SC']['questions']['P7']['yes_mark'])

# Every page shows an answer's state and cost as the feed gives them (site/feed.py: answer_state, answer_cost),
# so the branches no card reaches yet can't drift apart: signs of malware, a held-back Note, an open answer, a grouped answer.
import feed  # noqa: E402
_A = with_(P9=('!', 'Yes'))
check('a confirmed P9 Yes shows as Signs of malware', feed.answer_state('P9', _A, B['charges'](_A), set()) == 'malware', feed.answer_state('P9', _A, B['charges'](_A), set()))
_A = with_(D2=('~', 'Yes'))
check('a held-back answer marked Note stays a Note', feed.answer_state('D2', _A, B['charges'](_A, {'D2'}), {'D2'}) == 'note')
_A = with_(P2=(None, 'NC'))
check('an open answer costs its highest cost', feed.answer_cost('P2', _A, B['charges'](_A)) == (B['maxcost']('P2'), None, True), feed.answer_cost('P2', _A, B['charges'](_A)))
_A = with_(D2=('!', 'Yes'), D3=('!', 'Yes'))
check('a grouped answer costs nothing and names where it is counted', feed.answer_cost('D2', _A, B['charges'](_A)) == (0, 'D3', False), feed.answer_cost('D2', _A, B['charges'](_A)))
check('the feed\'s AI note is rule 8\'s words from site/content.yaml, in plain text', feed.ai_note().startswith('Claude, an AI, does the analysis from a public prompt'))
_says = feed.sections_out([{'title': 'What it says vs what it does', 'blocks': [{'table': ['Claim', 'Verdict', 'Evidence'], 'rows': [
    {'Claim': 'a', 'Verdict': 'Matches', 'Evidence': '-'}, {'Claim': 'b', 'Verdict': 'Partly, as far as checked', 'Evidence': '-'}, {'Claim': 'c', 'Verdict': "Doesn't match", 'Evidence': '-'}]}]}])
check('the feed gives each "Says vs does" verdict the state the page draws it as', [r['verdict_state'] for r in _says[0]['blocks'][0]['rows']] == ['good', 'note', 'concern'])
check('the feed accepts a malware state', 'malware' in feed.SCHEMA['$defs']['state']['enum'])

# Every page shows what its card holds: render.complete refuses a page where an answer or a "Says vs does" claim lost its mark,
# the bug that once left the claims grey (site/render.py).
import render  # noqa: E402
_c = {'card': 't-1', 'answers': [{'id': 'P1'}], 'key_answers': [], 'areas': [], 'files': [], 'history': [],
      'sections': [{'title': 'What it says vs what it does', 'blocks': [{'table': ['Claim', 'Verdict', 'Evidence'], 'rows': [{}]}]}]}
_row = lambda i, mark: (f'<div class="row" id="{i}"><span class="id">{i}</span><div class="rb"><div class="q">Q</div>'
                       f'<div class="v">{'<span class="st good">Good</span>' if mark else 'Good'}</div></div></div>')
def _refused(html):
    try: render.complete(_c, html)
    except AssertionError: return True
    return False
check('a page with every mark passes the completeness check', not _refused(_row('q-P1', 1) + _row('claim-1', 1)))
check('a claim drawn without its mark fails the completeness check', _refused(_row('q-P1', 1) + _row('claim-1', 0)))
check('an answer left off the page fails the completeness check', _refused(_row('claim-1', 1)))
check('a row without a mark can\'t borrow the next row\'s', _refused(_row('claim-1', 0) + _row('q-P1', 1)))

# "Marked by the rule" shows only where the rule's condition set the mark, not on every answer whose rule has one.
_q = next(q for q, cells in feed.QCELL.items() for v, r in cells.items() if r and r.startswith('Good; Note if'))
_v = next(v for v, r in feed.QCELL[_q].items() if r and r.startswith('Good; Note if'))
check('a Good answer under a "Good; Note if" rule gets no rule note', feed.rule_note(_q, '{x} ' + _v, 'good') is None)
check('a Note under a "Good; Note if" rule names the rule', (feed.rule_note(_q, '{x} ' + _v, 'note') or '').startswith('Marked by the rule: Good; Note if'))

print(f'{len(FAILED)} failed' if FAILED else 'all passed')
sys.exit(1 if FAILED else 0)
