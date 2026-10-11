// Turns med vert og gjest: hvem styrer i Select a Knight og paa kartet, naar verten velger den andre ridderen (SIR RICHARD).
// For rettingen styrte gjesten da vertens ridder, fordi nettsiden brukte figuren (+$36) i stedet for rekkefolgen.
const T = require('./felles');
const { sjekk, U, trykk, velg, venter, statusTekst } = T;

const eier = (p) => p.evaluate(() => window.moonDebug.Kjerne.portSpillere()[1]);
const velger = (p) => p.evaluate(() => window.moonDebug.Kjerne.velgerRidder());
const markoer = (p) => T.les16(p, 0x8f51e);                     // Select a Knight: figuren pilen staar paa
const pos = (p, k) => p.evaluate((k) => { const K = window.moonDebug.Kjerne, s = 0x8d5b4 + k * 0x84; return [K.les8(s + 0x7e) << 8 | K.les8(s + 0x7f), K.les8(s + 0x80) << 8 | K.les8(s + 0x81)]; }, k);
async function hold(p, key, ms, etter) { await p.keyboard.down(key); await p.waitForTimeout(ms); await p.keyboard.up(key); await p.waitForTimeout(etter); }

T.kjor(async () => {
  const b = await T.nettleser();
  const vert = await T.side(b, { navn: 'vert', innst: { navn: 'Tom', spill: 'sammen' } });
  const kari = await T.side(b, { navn: 'kari', innst: { navn: 'Kari' } });
  await vert.goto(U);
  await T.tilTittel(vert);
  const lenke = await T.lagRom(vert, 'vert');
  await T.bliMed(kari, lenke, 'gjest', 3000);
  // verten: Back til tittelmenyen, saa Select Knight
  await velg(vert, 5);
  await vert.waitForTimeout(2500);
  console.log('Players:', await T.les16(vert, 0x8cdfc));
  await velg(vert, 3);                                         // Select Knight
  sjekk(await venter(async () => await velger(vert) && await velger(kari)), 'Select a Knight hos begge');
  sjekk(await eier(vert) === 0 && await eier(kari) === 0, 'spiller 1 (verten) velger forst: eier ' + await eier(vert));
  console.log('vert status:', await statusTekst(vert), '| kari status:', await statusTekst(kari));
  sjekk((await statusTekst(vert)).includes('Tom velger ridder'), 'statuslinjen: Tom velger ridder');
  const m0 = await markoer(vert);
  await trykk(kari, 'ArrowRight', 150, 1200);
  sjekk(await markoer(vert) === m0, 'gjesten flytter ikke pilen naar verten velger (' + m0 + ' -> ' + await markoer(vert) + ')');
  await trykk(vert, 'ArrowRight', 150, 1200);
  sjekk(await markoer(vert) === 1, 'verten flytter pilen til SIR RICHARD (' + await markoer(vert) + ')');
  await trykk(vert, 'ControlLeft', 150, 2500);                 // velg SIR RICHARD, saa navnet
  await trykk(kari, 'Enter', 120, 1500);                       // gjesten kan ikke godta vertens navn
  sjekk(await eier(vert) === 0, 'gjestens Return godtok ikke vertens navn');
  await trykk(vert, 'Enter', 120, 3000);                       // verten godtar navnet
  sjekk(await venter(async () => await eier(vert) === 1 && await velger(vert)), 'saa velger spiller 2 (Kari): eier ' + await eier(vert));
  await kari.waitForTimeout(1500);
  console.log('kari status:', await statusTekst(kari));
  sjekk((await statusTekst(kari)).includes('Kari velger ridder'), 'statuslinjen hos Kari: Kari velger ridder');
  const m1 = await markoer(vert);
  await trykk(vert, 'ArrowRight', 150, 1200);
  sjekk(await markoer(vert) === m1, 'verten flytter ikke pilen naar Kari velger');
  await trykk(kari, 'ArrowRight', 150, 1500);
  sjekk(await markoer(vert) !== m1, 'Kari flytter pilen (' + m1 + ' -> ' + await markoer(vert) + ')');
  await trykk(kari, 'ControlLeft', 150, 2500);
  await trykk(kari, 'Enter', 120, 3000);
  // kartet: forste tur er plass 0 (verten, SIR RICHARD med figur 1)
  sjekk(await venter(async () => !(await velger(vert)) && await eier(vert) === 0, 30000), 'kartet: verten har turen (plass 0)');
  await vert.waitForTimeout(2000);
  const p0 = await pos(vert, 0);
  await hold(kari, 'ArrowDown', 1500, 1000);
  const p0b = await pos(vert, 0);
  sjekk(p0[0] === p0b[0] && p0[1] === p0b[1], 'gjesten flytter ikke vertens ridder ' + JSON.stringify([p0, p0b]));
  await hold(vert, 'ArrowDown', 1500, 1000);
  const p0c = await pos(vert, 0);
  sjekk(p0c[0] !== p0b[0] || p0c[1] !== p0b[1], 'verten flytter sin ridder ' + JSON.stringify([p0b, p0c]));
  // verten avslutter turen (E): saa er det Kari (plass 1)
  await trykk(kari, 'KeyE', 120, 1500);
  sjekk(await eier(vert) === 0, 'gjestens E avsluttet ikke vertens tur');
  await trykk(vert, 'KeyE', 120, 1500);
  sjekk(await venter(async () => await eier(vert) === 1, 30000), 'saa har Kari turen (plass 1)');
  await kari.waitForTimeout(2500);
  console.log('kari status:', await statusTekst(kari));
  const p1 = await pos(vert, 1);
  await hold(vert, 'ArrowDown', 1500, 1000);
  const p1b = await pos(vert, 1);
  sjekk(p1[0] === p1b[0] && p1[1] === p1b[1], 'verten flytter ikke Karis ridder ' + JSON.stringify([p1, p1b]));
  await hold(kari, 'ArrowDown', 1500, 1500);
  const p1c = await pos(vert, 1);
  sjekk(p1c[0] !== p1b[0] || p1c[1] !== p1b[1], 'Kari flytter sin ridder ' + JSON.stringify([p1b, p1c]));
  const st = await kari.evaluate(() => window.moonDebug.statistikk);
  sjekk(st.avvik === 0, 'ingen avvik i sjekksummene ' + JSON.stringify(st));
  await T.skjerm(vert, 't35-vert.png');
});
