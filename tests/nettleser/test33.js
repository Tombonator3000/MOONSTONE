// Options i tittelmenyen: Keyboard og Gamepad, binding av taster og knapper, lagring.
const T = require('./felles');
const { sjekk, U, trykk, valg, rader } = T;

const tittel5 = (p) => p.evaluate(() => { const K = window.moonDebug.Kjerne; let s = ''; for (let j = 0; j < 16; j++) { const c = K.les8(0xf8020 + j); if (!c) break; s += String.fromCharCode(c); } return s; });
const velg = (p, rad, fire = 'Enter', ned, opp) => T.velg(p, rad, { fire, ned, opp });
const venterRad = (p, i, tekst) => T.venterRad(p, i, tekst, 40);
/* den falske spillkontrolleren: knapp k nede i ms */
async function padTrykk(p, k, ms = 150) {
  await p.evaluate((k) => { window.__pad[k] = true; }, k); await p.waitForTimeout(ms);
  await p.evaluate((k) => { window.__pad[k] = false; }, k); await p.waitForTimeout(500);
}
async function gaaTilPad(p, rad) {
  for (let n = 0; n < 12; n++) {
    const v = await valg(p);
    if (v === rad) return true;
    const k = v < rad ? 13 : 12;
    await p.evaluate((k) => { window.__pad[k] = true; }, k); await p.waitForTimeout(120);
    await p.evaluate((k) => { window.__pad[k] = false; }, k);
    for (let m = 0; m < 20 && await valg(p) === v; m++) await p.waitForTimeout(50);
    await p.waitForTimeout(150);
  }
  return await valg(p) === rad;
}

T.kjor(async () => {
  const b = await T.nettleser();
  let p = await T.side(b);
  const ctx = p.context();
  /* en falsk spillkontroller som testen styrer: window.__pad[i] = true/false */
  await ctx.addInitScript(() => {
    window.__pad = new Array(17).fill(false);
    const pad = { id: 'Test', index: 0, connected: true, mapping: 'standard', axes: [0, 0, 0, 0],
      get buttons() { return window.__pad.map((v) => ({ pressed: v, value: v ? 1 : 0 })); } };
    navigator.getGamepads = () => [pad, null, null, null];
  });
  await p.goto(U);
  await T.tilTittel(p, { alene: true });
  sjekk(await tittel5(p) === 'Options', 'tittelmenyen har Options (' + await tittel5(p) + ')');
  await velg(p, 4);
  sjekk(await venterRad(p, 0, 'Options'), 'Options-siden: ' + JSON.stringify(await rader(p)));
  await T.skjerm(p, 't33-options.png');
  // Keyboard
  await velg(p, 2);
  sjekk(await venterRad(p, 1, 'Fire  Ctrl'), 'Keyboard-siden: ' + JSON.stringify(await rader(p)));
  await velg(p, 1);
  sjekk(await venterRad(p, 1, 'Press a Key'), 'venter paa en tast');
  await trykk(p, 'KeyZ');
  sjekk(await venterRad(p, 1, 'Fire  Z'), 'fire er Z');
  await p.waitForTimeout(800);
  sjekk((await rader(p))[1] === 'Fire  Z', 'Z startet ikke valget paa nytt');
  await velg(p, 2);                                          // Move: Arrows -> WASD
  sjekk(await venterRad(p, 2, 'Move  WASD'), 'bevegelse WASD');
  await p.keyboard.down('KeyD'); await p.waitForTimeout(100);
  const medD = await p.evaluate(() => Inndata.les().a);
  await p.keyboard.up('KeyD'); await p.waitForTimeout(300);
  sjekk(medD & 8, 'D er hoyre (' + medD + ')');
  await T.skjerm(p, 't33-keyboard.png');
  // Back (rad 5) med S (ned i WASD) og Z (fire)
  await velg(p, 5, 'KeyZ', 'KeyS', 'KeyW');
  sjekk(await venterRad(p, 0, 'Options'), 'tilbake til Options med S og Z');
  await trykk(p, 'ControlLeft'); await p.waitForTimeout(500);
  sjekk((await rader(p))[0] === 'Options', 'Ctrl er ikke fire lenger');
  // Gamepad
  await velg(p, 3, 'KeyZ', 'KeyS', 'KeyW');
  sjekk(await venterRad(p, 0, 'Gamepad'), 'Gamepad-siden: ' + JSON.stringify(await rader(p)));
  const rg = await rader(p);
  sjekk(rg[1] === 'Fire  A' && rg[2] === 'Inventory  B' && rg[3] === 'Pass  Start' && rg[4] === 'Escape  Back', 'standardknappene vises');
  await velg(p, 1, 'KeyZ', 'KeyS', 'KeyW');
  sjekk(await venterRad(p, 1, 'Press a Button'), 'venter paa en knapp');
  await padTrykk(p, 2);
  sjekk(await venterRad(p, 1, 'Fire  X'), 'fire er X paa spillkontrolleren');
  await p.waitForTimeout(800);
  sjekk((await rader(p))[1] === 'Fire  X', 'X startet ikke valget paa nytt');
  // Back med korset paa spillkontrolleren og X
  await gaaTilPad(p, 5);
  await padTrykk(p, 2);
  sjekk(await venterRad(p, 0, 'Options'), 'X er fire (Back til Options)');
  await padTrykk(p, 0); await p.waitForTimeout(500);
  sjekk((await rader(p))[0] === 'Options', 'A er ikke fire lenger');
  // inventar til A (A er ledig)
  await velg(p, 3, 'KeyZ', 'KeyS', 'KeyW');
  await venterRad(p, 0, 'Gamepad');
  await velg(p, 2, 'KeyZ', 'KeyS', 'KeyW');
  sjekk(await venterRad(p, 2, 'Press a Button'), 'venter paa knapp for Inventory');
  await padTrykk(p, 0);
  sjekk(await venterRad(p, 2, 'Inventory  A'), 'inventar er A');
  // Esc avbryter
  await velg(p, 3, 'KeyZ', 'KeyS', 'KeyW');
  sjekk(await venterRad(p, 3, 'Press a Button'), 'venter paa knapp for Pass');
  await trykk(p, 'Escape');
  sjekk(await venterRad(p, 3, 'Pass  Start'), 'Esc avbrot, Pass er fortsatt Start');
  await T.skjerm(p, 't33-gamepad.png');
  console.log('lagret:', await p.evaluate(() => JSON.stringify(window.moonDebug.innst.kontroller)));
  // ny side: oppsettet huskes
  await p.close();
  p = T.merk(await ctx.newPage());
  await p.goto(U);
  await T.tilTittel(p, { alene: true });
  const o = await p.evaluate(() => Inndata.oppsett());
  sjekk(o.fire1[0] === 'KeyZ' && o.flytt1 === 'wasd' && o.pad[0] === 2 && o.pad[1] === 0, 'oppsettet huskes etter ny lasting');
  // Default Controls (Options rad 4), med de nye tastene (S ned, Z fire)
  await velg(p, 4, 'KeyZ', 'KeyS', 'KeyW');
  await venterRad(p, 0, 'Options');
  await velg(p, 4, 'KeyZ', 'KeyS', 'KeyW');
  await p.waitForTimeout(800);
  const o2 = await p.evaluate(() => Inndata.oppsett());
  sjekk(o2.fire1[0] === 'ControlLeft' && o2.flytt1 === 'piler' && o2.pad[0] === 0, 'Default Controls gir standardoppsettet');
  // Online Game fra Options
  await velg(p, 1, 'ControlLeft');
  sjekk(await venterRad(p, 1, 'Host Game'), 'Online Game fra Options: ' + JSON.stringify(await rader(p)));
  await velg(p, 5, 'ControlLeft');
  sjekk(await venterRad(p, 0, 'Options'), 'Back fra Online Game gaar til Options');
});
