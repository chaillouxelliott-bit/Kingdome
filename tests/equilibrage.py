import asyncio,sys,json
from playwright.async_api import async_playwright
N=int(sys.argv[1]) if len(sys.argv)>1 else 24; R=int(sys.argv[2]) if len(sys.argv)>2 else 2; OUT=sys.argv[3] if len(sys.argv)>3 else 'bal'
JS="""async(sc,f,N)=>{VIEW.scen=sc;VIEW.faction=f;newGameUI(f);await new Promise(r=>setTimeout(r,700));S.pend=[];
 let won=-1,err='';const fn=()=>{try{return objFn50()&&objFn50()()}catch(e){return false}};
 for(let i=1;i<=N;i++){S.pend=[];VIEW.busy=false;for(const L of (S.letters||[]).slice()){if(L.acts&&L.acts.length){try{letterAct(L.id,L.acts[0][1])}catch(e){}}}
  try{aiTick(S.player)}catch(e){} try{endSeason()}catch(e){err=e.message;break} if(won<0&&(fn()||S.flags.obj50))won=i; if(!S.realms[S.player]||!S.realms[S.player].alive){err='mort';break}}
 return {won,err,prov:realmProvs(S.player).length}}"""
async def main():
    roles={}
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(); await pg.goto('file:///home/claude/kingdome/index.html'); await pg.wait_for_timeout(1300)
        roles = await pg.evaluate("Object.fromEntries(Object.entries(PLAY50).map(([k,v])=>[k,v.map(f=>f.id)]))"); await pg.close()
        res={}
        for sc,fs in roles.items():
            for f in fs:
                rr=[]
                for r in range(R):
                    pg = await b.new_page(viewport={'width':900,'height':700})
                    await pg.goto('file:///home/claude/kingdome/index.html'); await pg.wait_for_timeout(1200)
                    try: rr.append(await pg.evaluate(f"({JS})('{sc}','{f}',{N})"))
                    except Exception as e: rr.append({'won':-1,'err':str(e)[:80],'prov':0})
                    await pg.close()
                res[sc+':'+f]=rr; w=sum(1 for x in rr if x['won']>0)
                print(f"{sc:11s} {f:4s} gagné {w}/{R}  saisons={[x['won'] for x in rr]} prov={[x['prov'] for x in rr]} {[x['err'] for x in rr if x['err']]}", flush=True)
        await b.close(); json.dump(res,open(f'/tmp/{OUT}.json','w'))
asyncio.run(main())
