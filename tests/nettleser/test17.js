// Mus i menyene: klikk paa rader, Enter, hint, og fire med klikk i spillet.
const T = require('./felles');
const { sjekk } = T;

async function klikkRad(p, y) {          // y i spillets linjer (0-199)
  const r = await p.locator('#lerret').boundingBox();
  await p.mouse.click(r.x + r.width / 2, r.y + r.height * (y / 200));
  await p.waitForTimeout(700);
}
const naa = (p) => p.evaluate(() => { const K = window.moonDebug.Kjerne; return K.iMeny() ? (K.menyRad(0x55) === 0 ? 'tittel' : 'side') : 'ikke meny'; });
async function side(p, vil) {      // venter til siden er som ventet (tegningen tar opp mot et sekund)
  for (let i = 0; i < 40; i++) { const s = await naa(p); if (s === vil) { await p.waitForTimeout(900); return s; } await p.waitForTimeout(100); }
  return naa(p);
}
/* venter til siden har tittelen, og saa til den er ferdig tegnet */
async function venterRad0(p, tekst) { const ok = await T.venterRad(p, 0, tekst, 40); if (ok) await p.waitForTimeout(900); return ok; }

T.kjor(async () => {
  const b = await T.nettleser();
  const p = await T.side(b);
  await p.goto(T.BASE);
  await p.waitForFunction(() => window.moonDebug && window.moonDebug.modus() === 'alene' && window.moonDebug.Kjerne.iIntro(), null, { timeout: 30000 });
  await p.waitForTimeout(1500);
  await klikkRad(p, 100);                                  // lyd og hopp over
  await p.waitForFunction(() => window.moonDebug.Kjerne.menyKlar(), null, { timeout: 30000 });
  await p.waitForTimeout(1000);
  console.log('hint:', await p.evaluate(() => document.getElementById('hint').hidden ? '(skjult)' : document.getElementById('hint').textContent));
  sjekk(await side(p, 'tittel') === 'tittel', 'tittelmenyen');
  await p.mouse.move(400, 30 + 500 * (0xb9 / 200));
  await p.waitForTimeout(200);
  sjekk(await p.evaluate(() => getComputedStyle(document.getElementById('skjerm')).cursor) === 'pointer', 'haand over Options');
  await klikkRad(p, 0xb0 + 9);                                // Options
  sjekk(await side(p, 'side') === 'side', 'klikk paa Options aapnet siden');
  sjekk(await venterRad0(p, 'Options'), 'Options-siden');
  await klikkRad(p, 0x64 + 9);                                // Online Game
  sjekk(await venterRad0(p, 'Online Game'), 'klikk paa Online Game aapnet siden');
  await T.skjerm(p, 't17-online.png');
  await klikkRad(p, 0x8c + 9);                                // Choose Name
  sjekk(await p.evaluate(() => !document.getElementById('navn-dialog').hidden), 'klikk paa Choose Name aapnet navnefeltet');
  await p.fill('#navn-felt', 'Tom'); await p.press('#navn-felt', 'Enter');
  /* siden tegnes paa nytt med navnet; et klikk mens den tegnes, blir borte */
  await T.venter(async () => await T.rad(p, 3) !== 'Choose Name', 10000);
  console.log('linje 3 etter navnet:', await T.rad(p, 3));
  await p.waitForTimeout(1500);
  await klikkRad(p, 0xa0 + 9);                                // Mode
  await p.waitForTimeout(1500);
  sjekk(await p.evaluate(() => window.moonDebug.innst.spill) === 'sammen', 'klikk paa Mode byttet til Turns');
  await klikkRad(p, 0xa0 + 9);
  await p.waitForTimeout(1500);
  sjekk(await p.evaluate(() => window.moonDebug.innst.spill) === 'hver', 'klikk paa Mode igjen byttet til Separate');
  await klikkRad(p, 0xb4 + 9);                                // Back
  sjekk(await venterRad0(p, 'Options'), 'klikk paa Back gikk til Options');
  await p.keyboard.press('Enter'); await p.waitForTimeout(800);   // pilen staar paa Online Game
  sjekk(await venterRad0(p, 'Online Game'), 'Enter valgte Online Game');
  for (let i = 0; i < 4; i++) { await p.keyboard.press('ArrowDown'); await p.waitForTimeout(900); }   // hvert flytt tegner menyen paa nytt
  await p.keyboard.down('Space'); await p.waitForTimeout(150); await p.keyboard.up('Space'); await p.waitForTimeout(800);
  sjekk(await venterRad0(p, 'Options'), 'piltast ned og mellomrom valgte Back');
  await klikkRad(p, 0xb4 + 9);                                // Back paa Options
  sjekk(await side(p, 'tittel') === 'tittel', 'Back paa Options gikk til tittelmenyen');
  await klikkRad(p, 0x30);                                    // ved siden av radene: ingenting
  sjekk(await side(p, 'tittel') === 'tittel', 'klikk utenfor radene gjorde ingenting');
  await klikkRad(p, 0x88 + 9);                                // Practice
  await p.waitForTimeout(4000);
  sjekk(await side(p, 'ikke meny') === 'ikke meny', 'klikk paa Practice startet spillet');
  await T.skjerm(p, 't17-practice.png');
  const r = await p.evaluate(() => {
    const K = window.moonDebug.Kjerne;
    const t = performance.now(); for (let i = 0; i < 300; i++) K.bilde(); return ((performance.now() - t) / 300).toFixed(3);
  });
  console.log('kjerne i spillet, ms per bilde:', r);
});
