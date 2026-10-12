// Forsinket foerstegangs-HD: portrettene tegnes foer grafikkpakken kommer.
const T = require('./felles');
const portretter = () => [...new Set(moonDebug.Visning.hdFigurer()
  .filter(d => d.fil.toLowerCase() === 'sel.cel' && d.bilde >= 2 && d.bilde <= 5)
  .map(d => d.bilde))].length === 4;

T.kjor(async () => {
  const b = await T.nettleser(), p = await T.side(b);
  const feil = []; p.on('pageerror', e => feil.push(e.message));
  let slipp;
  const vent = new Promise(resolve => { slipp = resolve; });
  await p.route('**/hd/**', async route => { await vent; await route.continue(); });
  try {
    await p.goto(T.BASE);
    await p.waitForFunction(() => window.moonDebug && moonDebug.modus() === 'alene' && moonDebug.Kjerne.bildeNr() > 0);
    await p.keyboard.press('Escape');
    await p.waitForFunction(() => moonDebug.Kjerne.menyKlar(), null, {timeout:60000});
    await T.velg(p, 3);
    await p.waitForFunction(() => moonDebug.Kjerne.velgerRidder() && !moonDebug.Kjerne.navnAktiv());
    await p.waitForTimeout(1000);
    T.sjekk(await p.evaluate(() => moonDebug.Visning.hdPaa() && !moonDebug.StandardHd.info().klar),
      'riddervalget kan aapnes mens HD-nedlastingen venter');
    const k = await T.les16(p, 0x8f51e);
    await T.skjerm(p, 'hdstart1-venter.png');
    slipp();
    await p.waitForFunction(() => moonDebug.StandardHd.info().klar || moonDebug.StandardHd.info().feil, null, {timeout:180000});
    T.sjekk(await p.evaluate(() => moonDebug.StandardHd.info().klar && !moonDebug.StandardHd.info().feil), 'forsinket HD-pakke lastes uten feil');
    await p.waitForFunction(portretter, null, {timeout:30000});
    T.sjekk(true, 'alle fire engangstegnede portretter vises faktisk med HD etter sen lasting');
    T.sjekk(await T.les16(p, 0x8f51e) === k && !(await p.evaluate(() => moonDebug.Kjerne.navnAktiv())),
      'HD-lastingen endrer ikke riddervalget');
    await T.skjerm(p, 'hdstart1-klar.png');
    await p.keyboard.press('Enter');
    await p.waitForFunction(() => moonDebug.Kjerne.navnKlar(), null, {timeout:15000});
    T.sjekk((await p.evaluate(() => moonDebug.Kjerne.navn())).includes('GODBER'), 'Enter velger riktig ridder etter sen HD-lasting');
    T.sjekk(feil.length === 0, 'ingen JavaScript-feil: ' + JSON.stringify(feil));
  } finally { slipp(); }
});
