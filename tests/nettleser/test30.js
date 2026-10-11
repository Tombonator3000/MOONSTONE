// Duell i Separate der verten blir stille (forbindelsen henger uten at PeerJS sier fra):
// Kari gir opp og er tilbake i sitt spill, verten faar datamaskinen til aa styre Karis ridder.
// Til slutt: en fil legges inn i kjernen og fjernes igjen.
const T = require('./felles');
const { sjekk, trykk, duell } = T;

T.kjor(async () => {
  const b = await T.nettleser();
  const { vert, kari } = await T.hverForSegPaaKartet(b, 't30');
  const ik0 = await T.ridderInfo(kari);
  console.log('kari foer', JSON.stringify(ik0.r[0]));
  // verten: fire paa kartet gir valgene, 2 = Battle with (ridderen til Kari)
  await T.angrip(vert, 't30');
  await vert.waitForFunction(() => { const d = window.moonDebug.duell(); return d && d.status === 'aktiv'; }, null, { timeout: 30000 }).catch(() => {});
  console.log('vert duell', JSON.stringify(await duell(vert)), 'kari duell', JSON.stringify(await duell(kari)));
  sjekk((await duell(vert) || {}).status === 'aktiv', 'vert: duellen er i gang');
  sjekk((await duell(kari) || {}).rolle === 'b', 'kari: er med i duellen');
  await kari.waitForTimeout(2000);
  await T.skjerm(vert, 't30-vert-kamp.png');
  await T.skjerm(kari, 't30-kari-kamp.png');
  // verten blir stille: Kari gir opp og er tilbake i sitt spill
  await vert.waitForTimeout(3000);
  await vert.evaluate(() => window.moonDebug.duellStille());
  const t0 = Date.now();
  await kari.waitForFunction(() => !window.moonDebug.duell(), null, { timeout: 40000 }).catch(() => {});
  console.log('kari ga opp etter', Math.round((Date.now() - t0) / 1000), 's');
  sjekk(!(await duell(kari)), 'kari: ga opp duellen');
  const ik2 = await T.ridderInfo(kari);
  sjekk(ik2.blob0 === ik0.blob0, 'kari: eget spill tilbake, ridderen uendret');
  sjekk(await kari.evaluate(() => window.moonDebug.modus()) === 'hver', 'kari: fortsatt i rommet');
  await vert.waitForFunction(() => !window.moonDebug.duell(), null, { timeout: 20000 }).catch(() => {});
  sjekk(!(await duell(vert)), 'vert: duellen er over (forbindelsen lukket)');
  const ctl = await vert.evaluate(() => { const K = window.moonDebug.Kjerne; return [K.les8(0x8d638 + 0xb), K.les8(0x8d638 + 0x39)]; });
  sjekk(ctl[0] === 4 && ctl[1] === 4, 'vert: datamaskinen styrer ridderen til Kari (' + ctl + ')');
  // filene: en fil som legges inn og fjernes igjen
  const fil = await kari.evaluate(() => { const K = window.moonDebug.Kjerne; const f = 'data/duelltest.bin';
    const a = K.hentFil(f); K.leggInnFil(f, new Uint8Array([1, 2, 3])); const b = K.hentFil(f); K.fjernFil(f); const c = K.hentFil(f);
    return [a === null, b && b.length === 3, c === null]; });
  sjekk(fil.every(Boolean), 'kjernen: fil inn og ut igjen (' + fil + ')');
});
