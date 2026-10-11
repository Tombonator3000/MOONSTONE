// Duell i Separate der Kari ikke kan ta imot (sidemenyen er aapen): ingen duell,
// datamaskinen styrer ridderen hennes i vertens kamp, og Kari blir i rommet.
const T = require('./felles');
const { sjekk, trykk, duell } = T;

T.kjor(async () => {
  const b = await T.nettleser();
  const { vert, kari } = await T.hverForSegPaaKartet(b, 't28');
  const ik0 = await T.ridderInfo(kari);
  console.log('kari foer', JSON.stringify(ik0.r[0]));
  // Kari har sidemenyen aapen: hun kan ikke ta imot, saa datamaskinen styrer ridderen hennes
  await kari.keyboard.press('Home');
  await kari.waitForTimeout(500);
  sjekk(await kari.evaluate(() => !document.getElementById('meny').hidden), 'kari: sidemenyen er aapen');
  await T.angrip(vert, 't28');
  await vert.waitForTimeout(4000);
  const d = await duell(vert);
  sjekk(!d, 'vert: ingen duell, Kari sa nei (' + JSON.stringify(d) + ')');
  /* kampen starter litt etter avslaget; da faar Karis ridder datamaskinen (+$36 = 4) */
  const ctlNaa = () => vert.evaluate(() => { const K = window.moonDebug.Kjerne; return [K.les8(0x8d638 + 0xb), K.les8(0x8d638 + 0x39)]; });
  await T.venter(async () => (await ctlNaa())[1] === 4, 20000);
  const ctl = await ctlNaa();
  sjekk(ctl[0] === 4 && ctl[1] === 4, 'vert: datamaskinen styrer ridderen til Kari i kampen (+$0B ' + ctl[0] + ', +$36 ' + ctl[1] + ')');
  sjekk(!(await duell(kari)), 'kari: er ikke i en duell');
  sjekk(await kari.evaluate(() => window.moonDebug.modus()) === 'hver', 'kari: fortsatt i rommet');
  console.log('status vert:', await T.statusTekst(vert));
  await T.skjerm(vert, 't28-vert.png');
});
