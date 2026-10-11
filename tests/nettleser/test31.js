// Duell i Separate der Kari blir stille: verten gir opp, datamaskinen tar over Karis ridder,
// og Kari er tilbake i sitt spill med ridderen uendret.
const T = require('./felles');
const { sjekk, trykk, duell } = T;

T.kjor(async () => {
  const b = await T.nettleser();
  const { vert, kari } = await T.hverForSegPaaKartet(b, 't31');
  const ik0 = await T.ridderInfo(kari);
  console.log('kari foer', JSON.stringify(ik0.r[0]));
  // verten: fire paa kartet gir valgene, 2 = Battle with (ridderen til Kari)
  await T.angrip(vert, 't31');
  await vert.waitForFunction(() => { const d = window.moonDebug.duell(); return d && d.status === 'aktiv'; }, null, { timeout: 30000 }).catch(() => {});
  console.log('vert duell', JSON.stringify(await duell(vert)), 'kari duell', JSON.stringify(await duell(kari)));
  sjekk((await duell(vert) || {}).status === 'aktiv', 'vert: duellen er i gang');
  sjekk((await duell(kari) || {}).rolle === 'b', 'kari: er med i duellen');
  await kari.waitForTimeout(2000);
  await T.skjerm(vert, 't31-vert-kamp.png');
  await T.skjerm(kari, 't31-kari-kamp.png');
  // Kari blir stille: verten gir opp, datamaskinen tar over, og Kari er tilbake i sitt spill
  await vert.waitForTimeout(3000);
  await kari.evaluate(() => window.moonDebug.duellStille());
  const t0 = Date.now();
  await vert.waitForFunction(() => !window.moonDebug.duell(), null, { timeout: 30000 }).catch(() => {});
  console.log('verten ga opp etter', Math.round((Date.now() - t0) / 1000), 's');
  sjekk(!(await duell(vert)), 'vert: ga opp duellen');
  const ctl = await vert.evaluate(() => { const K = window.moonDebug.Kjerne; return [K.les8(0x8d638 + 0xb), K.les8(0x8d638 + 0x39)]; });
  sjekk(ctl[0] === 4 && ctl[1] === 4, 'vert: datamaskinen styrer ridderen til Kari (' + ctl + ')');
  await kari.waitForFunction(() => !window.moonDebug.duell(), null, { timeout: 30000 }).catch(() => {});
  sjekk(!(await duell(kari)), 'kari: duellen er over');
  const ik2 = await T.ridderInfo(kari);
  sjekk(ik2.blob0 === ik0.blob0, 'kari: eget spill tilbake, ridderen uendret');
});
