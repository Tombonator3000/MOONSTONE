// Faktisk oppstart, ett trykk over introen, HD-standard og alle fire riddervalg.
const T = require('./felles');
const { sjekk } = T;
const klar = p => p.waitForFunction(() => window.moonDebug && moonDebug.modus() === 'alene' && moonDebug.Kjerne.bildeNr() > 0);
const tittel = p => p.waitForFunction(() => moonDebug.Kjerne.menyKlar(), null, { timeout: 60000 });
const portrett = p => p.waitForFunction(() => moonDebug.Kjerne.velgerRidder() && !moonDebug.Kjerne.navnAktiv(), null, { timeout: 30000 });
const navn = p => p.waitForFunction(() => moonDebug.Kjerne.navnKlar(), null, { timeout: 15000 });
async function punkt(p, x, y) {
  return p.evaluate(({x,y}) => {
    const r = document.querySelector('#lerret').getBoundingClientRect(), c = moonDebug.Visning.utsnitt(), v = moonDebug.Kjerne.vindu();
    return { x: r.left + (v[0] + x * 2 - c[0]) / (c[2] - c[0]) * r.width,
      y: r.top + (v[1] + y - c[1]) / (c[3] - c[1]) * r.height };
  }, {x,y});
}
async function klikk(p, x, y) { const q = await punkt(p,x,y); await p.mouse.click(q.x,q.y); }
async function velgRidder(p, k) {
  const x = await p.evaluate(k => { const K = moonDebug.Kjerne, a = 0x8f516 + 2*k; return (K.les8(a)<<8 | K.les8(a+1)) + 32; }, k);
  await klikk(p,x,118);
}
T.kjor(async () => {
  const b = await T.nettleser(), p = await T.side(b);
  const feil = []; p.on('pageerror', e => feil.push(e.message));
  await p.goto(T.BASE); await klar(p);
  sjekk(await p.evaluate(() => moonDebug.Visning.hdPaa() && moonDebug.innst.hd === 'hd'), 'HD er standard uten lagret grafikkvalg');
  await klikk(p,160,100); await tittel(p);
  sjekk(true, 'ett kort klikk hopper over introen og starter lyden');
  await p.waitForFunction(() => moonDebug.StandardHd.info().klar || moonDebug.StandardHd.info().feil, null, { timeout: 180000 });
  console.log('HD:', await p.evaluate(() => moonDebug.StandardHd.info()));
  sjekk(await p.evaluate(() => moonDebug.Visning.hdAntall() > 0), 'standardpakken lastes automatisk');
  await T.velg(p,3); await portrett(p); await p.waitForTimeout(900);
  await T.skjerm(p,'start1-riddervalg-hd.png');
  await p.keyboard.press('Pause');
  await p.evaluate(() => { window.ridderStart = moonDebug.Kjerne.lagreTilstand(); });
  await p.keyboard.press('Pause');
  await klikk(p,5,30); await p.waitForTimeout(500);
  sjekk(await p.evaluate(() => !moonDebug.Kjerne.navnAktiv()), 'klikk utenfor portrettene velger ingen ridder');
  for (let k=0;k<4;k++) {
    if (k) { await p.keyboard.press('Pause'); await p.evaluate(() => moonDebug.Kjerne.lastTilstand(window.ridderStart)); await p.keyboard.press('Pause'); await portrett(p); await p.waitForTimeout(600); }
    await velgRidder(p,k); await navn(p);
    const forventet = ['GODBER','RICHARD','JEFFREY','EDWARD'][k];
    sjekk((await p.evaluate(() => moonDebug.Kjerne.navn())).includes(forventet), 'klikk velger riktig portrett: '+forventet);
    await p.waitForTimeout(500);
    sjekk(await p.evaluate(() => moonDebug.Kjerne.navnAktiv()), 'portrettklikk godtar ikke navnet automatisk: '+forventet);
    await T.trykk(p,'Enter',120,1500);
    await p.waitForFunction(() => !moonDebug.Kjerne.velgerRidder() && !moonDebug.Kjerne.navnAktiv(), null, {timeout:30000});
    sjekk(await p.evaluate(k => { const K=moonDebug.Kjerne, a=0x8d5b4+0x36; return K.les8(a+3)===k; },k), 'valgt figur blir med inn i spillet: '+forventet);
  }
  await p.keyboard.press('Pause'); await p.evaluate(() => moonDebug.Kjerne.lastTilstand(window.ridderStart)); await p.keyboard.press('Pause'); await portrett(p);
  await T.trykk(p,'ArrowRight',120,900); await p.keyboard.press('Enter'); await navn(p);
  sjekk((await p.evaluate(() => moonDebug.Kjerne.navn())).includes('RICHARD'), 'hoyrepil og Enter velger ridder');
  await p.keyboard.press('Pause'); await p.evaluate(() => moonDebug.Kjerne.lastTilstand(window.ridderStart)); await p.keyboard.press('Pause'); await portrett(p);
  await p.keyboard.press('Space'); await navn(p);
  sjekk((await p.evaluate(() => moonDebug.Kjerne.navn())).includes('GODBER'), 'mellomrom bekrefter riddervalget');
  await p.keyboard.press('Home'); await p.locator('#hd-bryter').selectOption('original'); await p.reload(); await klar(p);
  sjekk(await p.evaluate(() => !moonDebug.Visning.hdPaa() && moonDebug.innst.hdValgt), 'uttrykkelig Original-valg huskes ved omlasting');
  for (const key of ['Escape','Enter','Space','ControlLeft']) {
    if (key!=='Escape') { await p.reload(); await klar(p); }
    await p.keyboard.press(key); await tittel(p);
    sjekk(true,'ett kort '+key+'-trykk hopper over introen');
  }
  const m = await T.side(b,{ctx:{viewport:{width:412,height:892},isMobile:true,hasTouch:true},innst:{hd:'original',hdValgt:true}});
  m.on('pageerror',e=>feil.push(e.message)); await m.goto(T.BASE); await klar(m);
  let q=await punkt(m,160,100); await m.touchscreen.tap(q.x,q.y); await tittel(m);
  sjekk(true,'ett mobiltrykk hopper over introen');
  await T.velg(m,3); await portrett(m); await m.waitForTimeout(700);
  const x=await m.evaluate(()=>{const K=moonDebug.Kjerne;return (K.les8(0x8f51a)<<8|K.les8(0x8f51b))+32;});
  q=await punkt(m,x,118); await m.touchscreen.tap(q.x,q.y); await navn(m);
  sjekk((await m.evaluate(()=>moonDebug.Kjerne.navn())).includes('JEFFREY'),'mobiltrykk velger det tredje portrettet');
  sjekk(feil.length===0,'ingen JavaScript-feil: '+JSON.stringify(feil));
});
