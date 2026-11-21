import asyncio, json, sys, random
import os; HERE = os.path.dirname(os.path.abspath(__file__))
from playwright.async_api import async_playwright
sys.path.insert(0, HERE); import presets
N=int(sys.argv[1]); OUT=open(sys.argv[2],'a'); SEED=int(sys.argv[3])
KEYS=open(HERE+'/keys.txt').read().strip().split(',')
def stage(name):
    P=presets.P
    if name=='fresh': d={'fresh':1}; star,lv=0,0
    elif name=='early': d=dict(P['early']); star,lv=0,1
    elif name=='mid': d=dict(P['mid']); star,lv=3,5
    else: d=dict(P['late']); star,lv=10,9
    d=dict(d); d['tw']={k:star for k in KEYS}; d['twL']={k:lv for k in KEYS}; d.pop('deck',None); return d
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
        pg=await b.new_page(viewport={'width':1280,'height':720}, locale='ko-KR')
        await pg.add_init_script("localStorage.setItem('roomdef_tut','done'); localStorage.setItem('roomdef_set', JSON.stringify({fx:0, dmgNum:false, bgm:0, sfx:0}))")
        await pg.route(lambda u: 'firestore' in u or 'identitytoolkit' in u or 'gstatic' in u or 'googleapis' in u, lambda r: r.abort())
        await pg.goto(''+__import__('os').environ.get('URL','http://localhost:8766/index.html')+''); await pg.wait_for_timeout(1500)
        await pg.evaluate(open(HERE+'/h.js').read())
        await pg.evaluate("Math.random = (() => { let s = %d; return () => (s = (s * 16807) %% 2147483647) / 2147483647; })()" % SEED)
        await pg.evaluate("SIM.setPerk(o => o[(R() * o.length) | 0].id)")
        st=['fresh','early','mid','late']
        for i in range(N):
            sg=st[i%4]; s=stage(sg)
            await pg.evaluate("s => { s.deck = SIM.randDeck(); SIM.setup(s); }", s)
            r=await pg.evaluate('SIM.runAuto(250)' if os.environ.get('MODE')=='auto' else 'SIM.runMix(250)'); r['stage']=sg; r['i']=i
            OUT.write(json.dumps(r)+'\n'); OUT.flush()
            if i%20==0: print(i, sg, r['wave'], flush=True)
        await b.close()
asyncio.run(main())
