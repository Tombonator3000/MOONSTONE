// Duell i Separate motsatt vei: Kari angriper verten, verten styrer sin ridder over nettet,
// Kari slaar til kampen er over, og verten tar med seg ridderen tilbake i sitt eget spill.
const T = require('./felles');
const { sjekk, trykk, duell } = T;

T.kjor(async () => {
  const b = await T.nettleser();
  const { vert, kari } = await T.hverForSegPaaKartet(b, 't29');
  const iv0 = await T.ridderInfo(vert);
  console.log('vert foer', JSON.stringify(iv0.r[0]));
  // Kari: fire paa kartet gir valgene, 2 = Battle with (ridderen til verten)
  await T.angrip(kari, 't29');
  await kari.waitForFunction(() => { const d = window.moonDebug.duell(); return d && d.status === 'aktiv'; }, null, { timeout: 30000 }).catch(() => {});
  console.log('kari duell', JSON.stringify(await duell(kari)), 'vert duell', JSON.stringify(await duell(vert)));
  sjekk((await duell(kari) || {}).status === 'aktiv', 'kari: duellen er i gang');
  sjekk((await duell(vert) || {}).rolle === 'b', 'vert: er med i duellen');
  await vert.waitForTimeout(2000);
  await T.skjerm(kari, 't29-kari-kamp.png');
  await T.skjerm(vert, 't29-vert-kamp.png');
  // verten styrer sin ridder over nettet: til hoyre et sekund, naar kampen er i gang
  await kari.waitForFunction(() => { const K = window.moonDebug.Kjerne; return (K.les8(0x8d638 + 4) << 8 | K.les8(0x8d638 + 5)) > 0; }, null, { timeout: 30000 }).catch(() => {});
  await kari.waitForTimeout(10000);              /* kampen laster grafikken (om lag 8 s i spillet) */
  await T.skjerm(kari, 't29-kari-klar.png');
  const kx0 = await T.kampX1(kari);
  await vert.keyboard.down('ArrowRight'); await vert.waitForTimeout(1000); await vert.keyboard.up('ArrowRight'); await vert.waitForTimeout(500);
  const kx1 = await T.kampX1(kari);
  sjekk(kx1 > kx0, 'vert: styrer ridderen sin i Karis spill (x ' + kx0 + ' til ' + kx1 + ')');
  const hk0 = await kari.evaluate(() => window.moonDebug.Kjerne.hverBlob(0));
  // Kari gaar mot verten og slaar til kampen er over (verten staar stille)
  await T.slaaTilKampenErOver(kari, vert, 't29-vert');
  sjekk(!(await duell(kari)), 'kari: kampen er over');
  await vert.waitForFunction(() => !window.moonDebug.duell(), null, { timeout: 20000 }).catch(() => {});
  sjekk(!(await duell(vert)), 'vert: kampen er over');
  await vert.waitForTimeout(2000);
  const iv1 = await T.ridderInfo(vert);
  console.log('vert etter', JSON.stringify(iv1.r[0]));
  sjekk(await vert.evaluate(() => window.moonDebug.modus()) === 'hver' && await vert.evaluate(() => window.moonDebug.Kjerne.hverKart()), 'vert: tilbake paa kartet i sitt eget spill');
  sjekk(iv1.blob0 !== iv0.blob0, 'vert: ridderen er endret av kampen');
  sjekk(iv1.r[0][0] === iv0.r[0][0] && iv1.r[0][1] === iv0.r[0][1], 'vert: staar der han stod i sitt eget spill');
  await kari.waitForTimeout(3000);
  const ik1 = await T.ridderInfo(kari);
  console.log('kari ser vert', JSON.stringify(ik1.r[1]));
  sjekk(ik1.r[1][2] === iv1.r[0][2], 'kari: verten har samme liv som i sitt eget spill (' + ik1.r[1][2] + ')');
  const st = await vert.evaluate(() => window.moonDebug.statistikk);
  console.log('statistikk vert', JSON.stringify(st));
  sjekk(st.duellSjekket > 5 && !st.duellAvvik, 'vert: sjekksummene i kampen stemmer (' + st.duellSjekket + ')');
  const hk1 = await kari.evaluate(() => window.moonDebug.Kjerne.hverBlob(0));
  console.log('Karis ridder endret:', T.blobForskjell(hk0, hk1));
  console.log('vertens ridder endret:', T.blobForskjell(iv0.blob0, iv1.blob0));
  await T.skjerm(kari, 't29-kari-etter.png');
  await T.skjerm(vert, 't29-vert-etter.png');
});
