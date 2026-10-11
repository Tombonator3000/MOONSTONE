// Fullt rom (Separate): verten og tre gjester, saa proever en femte. Han skal faa beskjed om at
// rommet er fullt og bli staaende i tittelmenyen, uten at spillet hans startes paa nytt.
const T = require('./felles');
const { sjekk, U, trykk } = T;

T.kjor(async () => {
  const b = await T.nettleser();
  const side = (navn) => T.side(b, { navn, innst: { navn }, ctx: { viewport: { width: 640, height: 480 } } });
  const tilTittel = (p) => T.tilTittel(p, { alene: true, tid: 90000 });
  const vert = await side('Tom');
  await vert.goto(U);
  await tilTittel(vert);
  for (let i = 0; i < 4; i++) await trykk(vert, 'ArrowDown');
  await trykk(vert, 'ControlLeft');     // Options
  await trykk(vert, 'ControlLeft');     // Online Game
  await trykk(vert, 'ControlLeft');     // Host Game
  await vert.waitForFunction(() => window.moonDebug.modus() === 'hver', null, { timeout: 30000 });
  const kode = (await vert.evaluate(() => window.moonDebug.Nett.invitasjon())).match(/rom=([A-Z0-9]{6})/)[1];
  console.log('rom', kode);
  for (const n of ['G1', 'G2', 'G3']) {
    const g = await side(n);
    await g.goto(U + '&rom=' + kode);
    await tilTittel(g);
    await g.waitForTimeout(1500);
    await trykk(g, 'ControlLeft');
    await g.waitForFunction(() => window.moonDebug.modus() === 'hver', null, { timeout: 30000 }).catch(() => {});
    sjekk(await g.evaluate(() => window.moonDebug.modus()) === 'hver', n + ' er med i rommet');
  }
  const n4 = await vert.evaluate(() => window.moonDebug.Nett.spillere().length);
  sjekk(n4 === 4, 'fire spillere hos verten (' + n4 + ')');
  const g4 = await side('G4');
  await g4.goto(U + '&rom=' + kode);
  await tilTittel(g4);
  await g4.waitForTimeout(1500);
  const info = async () => ({ modus: await g4.evaluate(() => window.moonDebug.modus()), intro: await g4.evaluate(() => window.moonDebug.Kjerne.iIntro()),
    bilde: await g4.evaluate(() => window.moonDebug.Kjerne.bildeNr()), status: await T.statusTekst(g4) });
  const foer = await info();
  console.log('G4 foer:', JSON.stringify(foer));
  await trykk(g4, 'ControlLeft');
  let etter = null;
  for (let i = 0; i < 8; i++) {
    await g4.waitForTimeout(500);
    etter = await info();
    console.log('G4 +' + (i + 1) * 0.5 + 's:', JSON.stringify(etter));
  }
  sjekk(/fullt/.test(etter.status), 'G4 faar beskjed om at rommet er fullt');
  sjekk(etter.modus === 'alene' && !etter.intro && etter.bilde > foer.bilde, 'spillet til G4 er ikke startet paa nytt');
  const n5 = await vert.evaluate(() => window.moonDebug.Nett.spillere().length);
  sjekk(n5 === 4, 'fortsatt fire spillere hos verten (' + n5 + ')');
});
