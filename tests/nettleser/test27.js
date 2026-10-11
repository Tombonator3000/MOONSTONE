// Duell i Separate: verten angriper Kari (Battle with), Kari styrer sin ridder over nettet,
// verten slaar til kampen er over, og Kari tar med seg ridderen tilbake i sitt eget spill.
const T = require('./felles');
const { sjekk, trykk, duell } = T;

T.kjor(async () => {
  const b = await T.nettleser();
  const { vert, kari } = await T.hverForSegPaaKartet(b, 't27');
  const ik0 = await T.ridderInfo(kari);
  console.log('kari foer', JSON.stringify(ik0.r[0]));
  // verten: fire paa kartet gir valgene, 2 = Battle with (ridderen til Kari)
  await T.angrip(vert, 't27');
  await vert.waitForFunction(() => { const d = window.moonDebug.duell(); return d && d.status === 'aktiv'; }, null, { timeout: 30000 }).catch(() => {});
  console.log('vert duell', JSON.stringify(await duell(vert)), 'kari duell', JSON.stringify(await duell(kari)));
  sjekk((await duell(vert) || {}).status === 'aktiv', 'vert: duellen er i gang');
  sjekk((await duell(kari) || {}).rolle === 'b', 'kari: er med i duellen');
  // laste midt i kampen skal ikke gaa
  await vert.keyboard.press('PageDown');
  await vert.waitForTimeout(800);
  sjekk((await duell(vert) || {}).status === 'aktiv' && await T.statusTekst(vert) === 'Ikke under en duell', 'vert: kan ikke laste under duellen');
  await kari.waitForTimeout(2000);
  await T.skjerm(vert, 't27-vert-kamp.png');
  await T.skjerm(kari, 't27-kari-kamp.png');
  // Kari styrer sin ridder over nettet: til hoyre et sekund, naar kampen er i gang
  await vert.waitForFunction(() => { const K = window.moonDebug.Kjerne; return (K.les8(0x8d638 + 4) << 8 | K.les8(0x8d638 + 5)) > 0; }, null, { timeout: 30000 }).catch(() => {});
  await vert.waitForTimeout(10000);              /* kampen laster grafikken (om lag 8 s i spillet) */
  await T.skjerm(vert, 't27-vert-klar.png');
  const kx0 = await T.kampX1(vert);
  await kari.keyboard.down('ArrowRight'); await kari.waitForTimeout(1000); await kari.keyboard.up('ArrowRight'); await kari.waitForTimeout(500);
  const kx1 = await T.kampX1(vert);
  sjekk(kx1 > kx0, 'kari: styrer ridderen sin i vertens spill (x ' + kx0 + ' til ' + kx1 + ')');
  const hv0 = await vert.evaluate(() => window.moonDebug.Kjerne.hverBlob(0));
  // verten gaar mot Kari og slaar til kampen er over (Kari staar stille)
  await T.slaaTilKampenErOver(vert, kari, 't27-kari');
  sjekk(!(await duell(vert)), 'vert: kampen er over');
  await kari.waitForFunction(() => !window.moonDebug.duell(), null, { timeout: 20000 }).catch(() => {});
  sjekk(!(await duell(kari)), 'kari: kampen er over');
  await kari.waitForTimeout(2000);
  const ik1 = await T.ridderInfo(kari);
  console.log('kari etter', JSON.stringify(ik1.r[0]));
  sjekk(await kari.evaluate(() => window.moonDebug.modus()) === 'hver' && await kari.evaluate(() => window.moonDebug.Kjerne.hverKart()), 'kari: tilbake paa kartet i sitt eget spill');
  sjekk(ik1.blob0 !== ik0.blob0, 'kari: ridderen er endret av kampen');
  sjekk(ik1.r[0][0] === ik0.r[0][0] && ik1.r[0][1] === ik0.r[0][1], 'kari: staar der hun stod i sitt eget spill');
  await vert.waitForTimeout(3000);
  const iv1 = await T.ridderInfo(vert);
  console.log('vert ser kari', JSON.stringify(iv1.r[1]));
  sjekk(iv1.r[1][2] === ik1.r[0][2], 'vert: Kari har samme liv som i sitt eget spill (' + iv1.r[1][2] + ')');
  const st = await kari.evaluate(() => window.moonDebug.statistikk);
  console.log('statistikk kari', JSON.stringify(st));
  sjekk(st.duellSjekket > 5 && !st.duellAvvik, 'kari: sjekksummene i kampen stemmer (' + st.duellSjekket + ')');
  const hv1 = await vert.evaluate(() => window.moonDebug.Kjerne.hverBlob(0));
  console.log('vertens ridder endret:', T.blobForskjell(hv0, hv1));
  console.log('Karis ridder endret:', T.blobForskjell(ik0.blob0, ik1.blob0));
  await T.skjerm(vert, 't27-vert-etter.png');
  await T.skjerm(kari, 't27-kari-etter.png');
});
