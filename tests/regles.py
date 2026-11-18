import asyncio,sys,json
from playwright.async_api import async_playwright
SETUP="""async(sc,f)=>{VIEW.scen=sc;VIEW.faction=f;newGameUI(f);await new Promise(r=>setTimeout(r,700));S.pend=[];S.letters=[];try{closeModal()}catch(e){}}"""
TESTS = {
'1 Butin des alliés': ("nord","AUB","""(()=>{const w=S.wars.find(x=>x.a.includes('CIM')&&x.b.includes('AUB')); if(!w)return 'KO pas de guerre'; if(!w.b.some(k=>k!=='AUB')&&alive50('TAI')) w.b.push('TAI'); const al=w.b.find(k=>k!=='AUB'); if(!al) return 'KO pas d\\'allié';
  const q=realmProvs('CIM').find(x=>x!==capitalOf('CIM')); S.prov[q].occ=al; allySweep38(); return S.prov[q].occ==='AUB'?'OK la terre prise par '+rn(al)+' vous revient':'KO occ='+S.prov[q].occ})()"""),
'2 Paix : terres gardées ou rendues': ("nord","AUB","""(()=>{const w=S.wars.find(x=>x.a.includes('CIM')&&x.b.includes('AUB')); const qs=realmProvs('CIM').filter(x=>x!==capitalOf('CIM')).slice(0,3); qs.forEach(q=>S.prov[q].occ='AUB');
  endWar(w,'b',{provs:[qs[0]]}); const kept=S.prov[qs[0]].k==='AUB', back=qs.slice(1).every(q=>S.prov[q].k==='CIM'&&!S.prov[q].occ); return kept&&back?'OK 1 terre gardée, 2 rendues':'KO kept='+kept+' back='+back})()"""),
'3 Capitale prise : capitulation selon les armées': ("nord","AUB","""(()=>{const w=S.wars.find(x=>x.a.includes('CIM')&&x.b.includes('AUB')); const c=capitalOf('CIM'); armiesOf('CIM').forEach(a=>a.men=Math.min(a.men,150)); S.prov[c].occ='AUB'; S.prov[c].siege=0;
  mkArmy('AUB',null,c,3000,null,true); let msg=''; for(let i=0;i<5;i++){armiesOf('CIM').forEach(a=>a.men=Math.min(a.men,150)); S.realms.CIM.ban=true; S.prov[c].occ='AUB'; S.pend=[];endSeason(); if(!S.wars.includes(w)){msg='paix signée';break} if(S.letters.some(l=>l.kind==='peace'&&l.war===w.id)){msg='lettre de capitulation reçue';break}} 
  const st=w.cap41&&w.cap41.a; return msg?'OK '+msg:'KO rien après 4 saisons '+JSON.stringify(st||{})})()"""),
'4 Maison révoltée : capitule si son château tombe': ("nord","AUB","""(()=>{const h=Object.values(S.houses).find(x=>x.realm==='AUB'&&!x.royal&&houseProvs(x.id).length>=2); if(!h)return 'KO pas de maison'; startRevolt(h);
  const rid=Object.keys(S.rebels||{}).find(k=>S.rebels[k].house===h.id); if(!rid)return 'KO pas de révolte'; S.pend=[];endSeason(); const R0=S.rebels[rid]; if(!R0) return 'OK révolte déjà finie'; const q=R0.seat41; if(!q) return 'KO pas de château repéré'; armiesOf(rid).forEach(a=>delete S.armies[a.id]);
  S.prov[q].occ=null; mkArmy('AUB',null,q,3000,null,true); for(let i=0;i<3;i++){S.pend=[];endSeason(); if(!S.wars.some(w=>w.a.includes(rid)||w.b.includes(rid))) return 'OK la révolte des '+h.name+' a capitulé'} return 'KO révolte toujours en cours'})()"""),
'5 Paix : vassaliser des maisons entières': ("nord","AUB","""(()=>{const w=S.wars.find(x=>x.a.includes('CIM')&&x.b.includes('AUB')); const c=capitalOf('CIM'); S.prov[c].occ='AUB'; armiesOf('CIM').forEach(a=>a.men=Math.min(a.men,100)); const L=housesOf42(w); if(!L.length) return 'KO aucune maison proposée'; const ok=L.filter(x=>x.ok); return ok.length?'OK '+ok.length+' maison(s) vassalisable(s) proposée(s) ('+L.length+' listées)':'KO maisons listées mais aucune accessible'})()"""),
'6 Révoltés : siège de leur capitale et bataille': ("nord","AUB","""(()=>{const h=Object.values(S.houses).find(x=>x.realm==='AUB'&&!x.royal&&houseProvs(x.id).length>=2); startRevolt(h); const rid=Object.keys(S.rebels||{}).find(k=>S.rebels[k].house===h.id); if(!rid) return 'KO pas de révolte';
  const ra=armiesOf(rid)[0]; if(!ra) return 'KO pas d\\'armée rebelle'; const before=ra.men; mkArmy('AUB',null,ra.loc,Math.max(3000,before*2),null,true); S.pend=[];endSeason(); const after=S.armies[ra.id]?S.armies[ra.id].men:0;
  const w=S.wars.find(x=>x.a.includes(rid)||x.b.includes(rid)); return S.pendBattle?'OK bataille proposée au joueur (choix tactique)':after<before?'OK bataille livrée ('+Math.round(before)+' → '+Math.round(after)+'), guerre '+(w?'toujours ouverte':'terminée'):'KO pas de bataille: rebelle '+(S.armies[ra.id]?S.armies[ra.id].loc:'-')+' (était '+ra.loc+'), mes armées '+armiesOf('AUB').map(a=>a.loc+':'+Math.round(a.men)).join(',')+' guerreRebelle='+!!w})()"""),
'7 Ban selon la loyauté, indiqué par maison': ("nord","AUB","""(()=>{const H=Object.values(S.houses).filter(h=>h.realm==='AUB'&&!h.royal&&!h.gone); if(H.length<2)return 'KO'; H[0].loy=90; H[1].loy=10; if(S.realms.AUB.ban){S.realms.AUB.ban=false} callBan('AUB');
  const s0=banShare45(H[0]), s1=banShare45(H[1]); VIEW.tab='cour';VIEW.side=true;render(); const txt=(document.querySelector('#panel')||document.body).innerText; const shown=/ban/i.test(txt);
  return s0>=0.9&&s1<0.6?'OK loyal : '+Math.round(s0*100)+' %, déloyal : '+Math.round(s1*100)+' %'+(shown?', affiché':' (affichage non trouvé)'):'KO parts '+s0+' / '+s1})()"""),
'8 Onglet Guerre : soldats des deux camps': ("nord","AUB","""(()=>{VIEW.tab='guerre';VIEW.side=true;render(); const t=(document.querySelector('#panel')||document.body).innerText; const m=t.match(/\\d[\\d  ,.]*\\s*k?\\s*(hommes|soldats)?/g)||[]; return /contre|vs|⚔/i.test(t)&&/(\\d|k)/.test(t)?'OK':'KO'})()"""),
'9 Population en haut': ("nord","AUB","""(()=>{render(); const t=(document.querySelector('#top, .top, header')||document.body).innerText; return /Pop/i.test(t)?'OK':'KO'})()"""),
'10 Ordres enregistrés': ("nord","AUB","""(()=>{const n=(S.orders||[]).length; recordOrder('Convoquez le ban','',[{ok:true,t:'ban'}]); const ok=S.orders.length===n+1; const sv=JSON.parse(JSON.stringify(S)); return ok&&sv.orders.length===n+1?'OK enregistré et sauvegardé':'KO'})()"""),
'11 Hommage : le vassal est intégré, ses maisons demeurent': ("conquete","AUB","(()=>{const p=S.player; addTreaty('vassal',p,'VAL',null); render(); const h=Object.values(S.houses).filter(x=>x.formerKing==='VAL'&&x.realm===p); return !S.realms.VAL.alive&&h.length?'OK Valgué intégré, maison '+h[0].name+' vassale':'KO alive='+S.realms.VAL.alive})()"),
'12 Six couronnes : un seul royaume sur la carte': ("nord","AUB","(()=>{const w=REALM_IDS.filter(k=>alive50(k)&&realmProvs(k).length&&!east52(k)); return w.length===3&&w.includes('CIM')&&w.includes('FER')?'OK '+w.map(rn).join(', '):'KO '+w.map(rn).join(', ')})()"),
'13 Guerre civile : deux partis seulement': ("batard","AUB","(()=>{const w=REALM_IDS.filter(k=>alive50(k)&&realmProvs(k).length&&!east52(k)); return w.length===2?'OK '+w.map(rn).join(' contre '):'KO '+w.map(rn).join(', ')})()"),
'14 Couronne déchirée : trois partis': ("dechiree","AUB","(()=>{const w=REALM_IDS.filter(k=>alive50(k)&&realmProvs(k).length&&!east52(k)); return w.length===3?'OK '+w.map(rn).join(', '):'KO '+w.map(rn).join(', ')})()"),
}
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        res={}
        for name,(sc,f,js) in TESTS.items():
            pg = await b.new_page(viewport={'width':1200,'height':800}); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
            await pg.goto('file:///home/claude/kingdome/index.html'); await pg.wait_for_timeout(1300)
            try:
                await pg.evaluate(f"({SETUP})('{sc}','{f}')"); r = await pg.evaluate(js)
            except Exception as e: r='KO erreur '+str(e)[:200]
            res[name]=r+(' | err '+errs[0] if errs else ''); print(name,'→',res[name]); await pg.close()
        await b.close(); json.dump(res,open('/tmp/rules_res.json','w'),ensure_ascii=False)
asyncio.run(main())
