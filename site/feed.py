"""The public data feed: api/v1/ (index.json, cards/<card>.json, match.json), made from the checked card data, never from the
raw YAML, so a reader shows exactly what the site shows and works out no mark, cost or score itself. Its contract is
docs/FEED.md; its shape is rules/feed.schema.json, which every file is checked against here.

Usage: from build.py, write_feed(SITE, CARDS, shell) after the cards are checked.
"""
import datetime, json, jsonschema, os, re, subprocess
from rules import AREAK, AREAN, CONCERN, HELD, KEYS, QS, RUBRICV, SC, STATES, load_yaml, money, scored, sround, state_of, tagsof, ROOT, D
from cards import MM, REG, SITES, check_card, site
from page import BADGES, COMMIT, SITEURL, answer_cost, answer_state

FEED_VERSION='1.0'
SCHEMA=json.load(open(ROOT+'rules/feed.schema.json'))
AREA_ID={ar:AREAK[ar] for ar in AREAN}
QAREA={i:AREA_ID[a] for i,a,_t in QS}
VWORD={'Opt':'Yes, not by default','Req':'Yes, on request','NC':'Not checked','NA':'Not allowed','DNA':"Doesn't apply"}

def plain(md):
    # Markdown to plain text for lists and apps: links keep their words, code its text, bold goes.
    t=re.sub(r'\[([^\]]+)\]\([^)]+\)',r'\1',md or '')
    t=re.sub(r'`([^`]*)`',r'\1',t)
    return re.sub(r'\*\*|__','',t).strip()

def iso(day): return datetime.datetime.strptime(day,'%d %b %Y').date().isoformat()

def ai_note(shell):
    # Rule 8's words, from the one place the site keeps them (site/shell.html, the "ai" paragraph): its first two sentences, as plain text.
    m=re.search(r'<p class="ai">(.*?)</p>',shell,re.S); assert m, 'site/shell.html: no <p class="ai"> for the feed\'s AI note'
    t=re.sub(r'<[^>]+>','',m.group(1)); return ' '.join(s.strip() for s in re.findall(r'[^.]+\.',t)[:2])

def check(obj,kind):
    jsonschema.validate(obj,{**SCHEMA,'$ref':'#/$defs/'+kind})
    # Markdown with https links only: no link a consumer would resolve against its own site.
    assert not re.search(r'\]\((?!https://)',json.dumps(obj,ensure_ascii=False)), kind+': a link in the feed is not https://'

def key_state(k):
    # A key answer's state: its mark, a Concern as the site draws it (Major, Off by default, On request, Signs of malware), or a grey state.
    mk,_h,ans,span=k
    if mk=='!': return state_of(span)
    if mk: return {'+':'good','~':'note'}[mk]
    return 'held' if ans.startswith('Held back') else 'na' if ans.startswith('Not allowed') else 'nc'

def result(G,A,held,hb):
    # The score block: kind, number, every area by id, the Money label, open answers and what is held back (rule 9: the number
    # of items and the questions, as the card's "Held back" row gives them, nothing more).
    num=G['kind']=='score'; m=re.match(HELD,hb) if hb else None
    return {'kind':G['kind'],'score':sround(G['score']) if num else None,
            'label':{'malware':'Signs of malware','notscored':'Not scored'}.get(G['kind'],f'{sround(G["score"])} / 100'),
            'areas':{AREA_ID[ar]:(G['areas'][ar][0] if num else None) for ar in CONCERN},
            'money':money(A,held),'open_questions':G['open'],'why':G['why'],
            'held_back':{'items':int(m.group(1)) if m else 0,'questions':sorted(held)}}

def add(d,k,v):
    if v not in d.setdefault(k,[]): d[k].append(v)

def write_feed(SITE,CARDS,shell):
    # The commit's date, not the clock, so the same commit always writes the same files.
    when=subprocess.run(['git','-C',ROOT,'log','-1','--format=%cI'],capture_output=True,text=True).stdout.strip() or '1970-01-01T00:00:00+00:00'
    base={'feed_version':FEED_VERSION,'built_at':when,'commit':COMMIT,'rubric':RUBRICV}
    note=ai_note(shell)
    out=SITE+'api/v1/'; os.makedirs(out+'cards',exist_ok=True)
    tools={}; match={'github':{},'mods_post':{},'sha256':{}}
    for f,slug in CARDS:
        raw=load_yaml(D+f); C=check_card(f,raw); d=C['d']; h=C['h']; A=C['A']; held=C['held']; SETS=C['SETS']
        G=scored(A,held); crit,opt,pos=tagsof(raw)
        cid=f[:-len('.yaml')]; order=REG[slug]['cards']; latest=order[-1]==f
        # The newest card's page is the tool's own address (with its link preview); an earlier card's is its anchor.
        page=f'{SITEURL}{slug}/' if latest else f'{SITEURL}#{cid}'
        res=result(G,A,held,h.get('Held back'))
        ans=[]
        for i,_a,qt in QS:
            v=A[i][1]; x=d['answers'][i]; cost,cw,op=answer_cost(i,A,SETS)
            ans.append({'id':i,'area':QAREA[i],'question':qt,'verdict':VWORD.get(v,v),'state':answer_state(i,A,SETS,held),
                        'cost':cost,'counted_with':cw,'open':op,'text':x['text'],'text_plain':plain(x['text']),'evidence':x['evidence'],
                        **({'second_check':x['second_check']} if 'second_check' in x else {})})
        key=[{'id':k,'question':q,'short':s,'from':src,'state':key_state(C['key'][k]),'text':C['key'][k][2],'text_plain':plain(C['key'][k][2])} for k,q,s,src in KEYS]
        tags=([{'label':l,'kind':'concern','question':q} for l,q in crit]+[{'label':l,'kind':'off_by_default','question':q} for l,q in opt]
              +[{'label':l,'kind':'positive','question':q} for l,q in pos])
        reg=REG[slug]; mk=site(reg); post=reg[mk]['post']
        mods={'site':SITES[h['Game']][1],'post':post,'url':MM[mk]['tools'].get(slug,{}).get('link')} if post else None
        badges={(suf or '-flat').lstrip('-'):f'{SITEURL}badge/{slug}/{C["ver"]}{suf}.svg' for suf,_x,_y in BADGES}
        files=[{'name':x['name'],'sha256':x['sha256'],'note':x.get('note',''),'inside':x.get('inside')} for x in raw['files']]
        hist=[{'date':x['date'],'date_iso':iso(x['date']),'change':x['change']} for x in raw.get('history',[])]
        card={**base,'ai_note':note,'card':cid,'tool':slug,'name':C['name'],'version':C['ver'],'latest':latest,'game':h['Game'],'category':h['Category'],
              'summary':plain(h['In one line']),'author':plain(h['Author']),'analysed':h['Analysed on'],'analysed_iso':iso(h['Analysed on']),'method':h['Method'],
              'page':page,'yaml':f'{SITEURL}cards/{f}','badges':badges,'result':res,'tags':tags,'files':files,
              'key_answers':key,'answers':ans,'sections':d['sections'],'history':hist,'corrections':raw.get('corrections',[])}
        check(card,'card')
        json.dump(card,open(out+f'cards/{cid}.json','w'),indent=1,ensure_ascii=False)
        rel={'version':C['ver'],'card':cid,'analysed':h['Analysed on'],'analysed_iso':iso(h['Analysed on']),'kind':res['kind'],'score':res['score'],
             'page':page,'json':f'{SITEURL}api/v1/cards/{cid}.json'}
        t=tools.setdefault(slug,{'id':slug,'name':C['name'],'author':reg['author'],'game':h['Game'],'github':reg['github'],'homepage':reg['homepage'],
                                 'mods_site':mods,'releases':[None]*len(order)})
        # Newest release first, in the registry's order (rule 2: every card stays).
        t['releases'][len(order)-1-order.index(f)]=rel
        if latest: t.update({'category':h['Category'],'summary':plain(h['In one line']),'page':page,'latest':{**rel,'result':res,'tags':tags,'badges':badges}})
        if reg['github']: add(match['github'],reg['github'].lower(),slug)
        if post: add(match['mods_post'],f'{mk}:{post}',slug)
        for x in files: add(match['sha256'],x['sha256'],{'tool':slug,'card':cid,'version':C['ver'],'latest':latest,'file':x['name'],'inside':x['inside'],'note':x['note']})
    index={**base,'site':SITEURL,'ai_note':note,'licence':{'data':None,'note':'Not chosen yet; see docs/FEED.md, "Using the data".'},
           'areas':[{'id':AREA_ID[ar],'name':ar,'scored':ar in CONCERN} for ar in AREAN],
           'states':[{'id':k,'label':l,'meaning':m} for k,(l,_c,_i,m) in STATES.items()],
           'tags':[{'label':x['tag'],'question':x['from'],'answer':x['answer'],'kind':x['kind'].lower(),'icon':x.get('icon')} for x in SC['tags'] if x['kind']!='None'],
           'tools':sorted(tools.values(),key=lambda t:t['name'].lower())}
    check(index,'index')
    json.dump(index,open(out+'index.json','w'),indent=1,ensure_ascii=False)
    m={**base,**match}; check(m,'match')
    json.dump(m,open(out+'match.json','w'),indent=1,ensure_ascii=False)
    os.makedirs(out+'schema',exist_ok=True); json.dump(SCHEMA,open(out+'schema/feed.schema.json','w'),indent=1)
    return index
