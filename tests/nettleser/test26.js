// Separate: verten lager rom, Kari blir med, begge starter sitt eget spill og ser hverandre paa kartet.
// Kari gaar, verten ser det, fargene er ulike, og naar verten lukker fanen spiller Kari videre alene.
const T = require('./felles');
const { sjekk } = T;

T.kjor(async () => {
  const b = await T.nettleser();
  const { vert, kari } = await T.hverForSegPaaKartet(b, 't26');
  const iv = await T.ridderInfo(vert), ik = await T.ridderInfo(kari);
  console.log('vert', JSON.stringify(iv.r));
  console.log('kari', JSON.stringify(ik.r));
  sjekk(iv.r[1][0] === ik.r[0][0] && iv.r[1][1] === ik.r[0][1], 'vert ser Kari der hun er');
  sjekk(ik.r[1][0] === iv.r[0][0] && ik.r[1][1] === iv.r[0][1], 'Kari ser verten der han er');
  sjekk(iv.r[1][4] === ik.r[0][4], 'navnet til Kari hos verten: ' + iv.r[1][4]);
  sjekk(ik.r[1][4] === iv.r[0][4], 'navnet til verten hos Kari: ' + ik.r[1][4]);
  // Kari gaar til hoyre et stykke; verten skal se henne flytte seg mens han har turen
  await kari.keyboard.down('ArrowRight'); await kari.waitForTimeout(1500); await kari.keyboard.up('ArrowRight');
  await kari.keyboard.down('ArrowDown'); await kari.waitForTimeout(800); await kari.keyboard.up('ArrowDown');
  await kari.waitForTimeout(1500);
  const iv2 = await T.ridderInfo(vert), ik2 = await T.ridderInfo(kari);
  console.log('etter gange: vert', JSON.stringify(iv2.r[1]), 'kari', JSON.stringify(ik2.r[0]));
  sjekk(ik2.r[0][0] !== ik.r[0][0] || ik2.r[0][1] !== ik.r[0][1], 'Kari flyttet seg');
  sjekk(iv2.r[1][0] === ik2.r[0][0] && iv2.r[1][1] === ik2.r[0][1], 'verten ser Kari der hun er naa');
  sjekk(iv2.r[1][3] !== iv2.r[0][3], 'Kari har en annen farge enn verten hos verten (' + iv2.r[1][3] + ' og ' + iv2.r[0][3] + ')');
  await T.skjerm(vert, 't26-vert-kart.png');
  await T.skjerm(kari, 't26-kari-kart.png');
  // verten lukker fanen: Kari fortsetter alene, plassen faar datamaskinens ridder tilbake
  await vert.close({ runBeforeUnload: true });
  await kari.waitForFunction(() => window.moonDebug.modus() === 'alene', null, { timeout: 30000 }).catch(() => {});
  await kari.waitForTimeout(500);
  const ik3 = await T.ridderInfo(kari);
  sjekk(await kari.evaluate(() => window.moonDebug.modus()) === 'alene', 'kari: alene etter at verten forsvant');
  sjekk(await kari.evaluate(() => window.moonDebug.Kjerne.hverKart()), 'kari: fortsatt paa kartet i sitt eget spill');
  sjekk(ik3.r[1][3] === 4 && ik3.r[1][4] === 'SIR DWAIN', 'kari: plass 2 er datamaskinens SIR DWAIN igjen (' + ik3.r[1][3] + ' ' + ik3.r[1][4] + ')');
});
