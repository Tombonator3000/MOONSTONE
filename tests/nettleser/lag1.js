// Lagringene paa nettsiden: automatisk lagring naar fanen skjules, Fortsett etter omlasting,
// nedlasting (som PC-versjonen kan laste), henting av en PC-lagring og meldinger ved feil.
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const T = require('./felles');
const { sjekk } = T;

T.kjor(async () => {
  const kart = T.tilstand('kart_ny.sav'), ny = T.tilstand('ny.sav');
  const b = await T.nettleser();
  const p = await T.side(b, { ctx: { acceptDownloads: true } });
  const status = () => p.evaluate(() => document.getElementById('status') ? document.getElementById('status').textContent : '');
  const bilde = () => p.evaluate(() => window.moonDebug.Kjerne.bildeNr());
  const tilMenyen = async () => {
    await p.waitForFunction(() => window.moonDebug && window.moonDebug.Kjerne.iIntro(), null, { timeout: 30000 });
    await p.waitForTimeout(1500);
    for (let i = 0; ; i++) {
      await p.mouse.click(400, 280);
      try { await p.waitForFunction(() => window.moonDebug.Kjerne.menyKlar(), null, { timeout: 10000 }); break; }
      catch (e) { if (i >= 2) throw e; }
    }
  };
  const skjul = async () => {
    await p.evaluate(() => { Object.defineProperty(document, 'hidden', { value: true, configurable: true }); document.dispatchEvent(new Event('visibilitychange')); });
    await p.waitForTimeout(1500);
    await p.evaluate(() => { Object.defineProperty(document, 'hidden', { value: false, configurable: true }); });
  };
  await p.goto(T.BASE);
  await p.mouse.click(400, 280);
  await tilMenyen();
  await p.waitForTimeout(1500);

  // i tittelmenyen er ingen spill begynt: ingen automatisk lagring
  await skjul();
  const info0 = await p.evaluate(() => document.getElementById('auto-info').textContent);
  console.log('i tittelmenyen:', info0);
  sjekk(/Ingen automatisk lagring/.test(info0), 'tittelmenyen lagres ikke automatisk (ville skrevet over et ekte spill)');
  // et spill paa kartet (lagring laget headless), saa skjules fanen
  await p.setInputFiles('#importer', kart);
  await p.waitForTimeout(3000);
  const bildeLagret = await bilde();
  await skjul();
  const info = await p.evaluate(() => document.getElementById('auto-info').textContent);
  console.log('auto-info:', info, 'bilde', bildeLagret);
  sjekk(/Sist lagret automatisk kl\. \d\d:\d\d/.test(info), 'et spill paa kartet lagres automatisk naar fanen skjules');

  // last ned
  const [dl] = await Promise.all([p.waitForEvent('download'), p.evaluate(() => document.getElementById('eksport').click())]);
  const fil = path.join(T.UT, 'fra_nett.sav');
  await dl.saveAs(fil);
  const head = fs.readFileSync(fil).subarray(0, 8).toString();
  console.log('nedlastet', dl.suggestedFilename(), fs.statSync(fil).size, 'bytes', head);
  sjekk(head === 'MOONSAV2' && /^moonstone-\d{8}-\d{4}\.sav$/.test(dl.suggestedFilename()), 'lagringen lastes ned som fil');
  let pc = '';
  try { pc = execFileSync(T.HEADLESS, ['--headless', '--load-state', fil, '--frames', '50', '--log', '0'], { encoding: 'utf8' }); } catch (e) { pc = String(e.stderr || e); }
  console.log('PC:', pc.trim().split('\n')[0]);
  sjekk(/Tilstand lastet/.test(pc), 'PC-versjonen laster lagringen fra nettet');

  // omlasting: beskjed og Fortsett
  await p.reload();
  await p.mouse.click(400, 280);
  await tilMenyen();
  await p.waitForTimeout(1000);
  const st = await status();
  console.log('status etter omlasting:', st);
  sjekk(/er lagret\. Velg Fortsett/.test(st), 'etter omlasting sier siden at spillet er lagret');
  const foer = await bilde();
  await p.evaluate(() => document.getElementById('last-auto').click());
  await p.waitForTimeout(800);
  const etter = await bilde();
  console.log('Fortsett: bilde', foer, '->', etter, 'status', await status());
  sjekk(/Lastet den automatiske lagringen/.test(await status()) && etter >= bildeLagret && etter - bildeLagret < 400, 'Fortsett laster den automatiske lagringen');

  // hent en lagring laget paa PC
  await p.setInputFiles('#importer', ny);
  await p.waitForTimeout(800);
  console.log('PC-lagring:', await status());
  sjekk(/Lastet ny\.sav/.test(await status()) && await bilde() < 1700, 'en lagring fra PC kan hentes inn paa nettet');

  // feil
  await p.setInputFiles('#importer', { name: 'tull.sav', mimeType: 'application/octet-stream', buffer: Buffer.from('hei paa deg') });
  await p.waitForTimeout(500);
  console.log('tull:', await status());
  sjekk(/ikke en lagring fra Moonstone/.test(await status()), 'en fil som ikke er en lagring gir en forklaring');
  const kamp6 = T.gammelLagring('kamp6.sav');
  if (kamp6) {
    await p.setInputFiles('#importer', kamp6);
    await p.waitForTimeout(500);
    console.log('gammel:', await status());
    sjekk(/eldre utgave \(versjon 4\)/.test(await status()), 'en gammel lagring sier hvilken versjon den er');
  }
  const gml = T.gammelLagring('gml.sav');
  if (gml) {
    await p.setInputFiles('#importer', gml);
    await p.waitForTimeout(500);
    console.log('gammel PC:', await status());
    sjekk(/annen maskintype/.test(await status()), 'en gammel PC-lagring (versjon 13, 64 bit) gir forklaring');
  }
});
