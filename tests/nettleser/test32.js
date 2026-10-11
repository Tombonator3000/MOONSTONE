// Laste et spill fra kartet mens tittelmenyen vises: menyen skal ikke henge igjen (in_menu).
const T = require('./felles');
const { sjekk, U, trykk } = T;

T.kjor(async () => {
  const b = await T.nettleser();
  let p = await T.side(b);
  const ctx = p.context();
  await p.goto(U);
  await T.tilTittel(p, { alene: true });
  for (let i = 0; i < 3; i++) await trykk(p, 'ArrowDown');
  await trykk(p, 'ControlLeft'); await p.waitForTimeout(8000);
  await trykk(p, 'ControlLeft'); await p.waitForTimeout(4000);
  await trykk(p, 'Enter');
  await p.waitForFunction(() => window.moonDebug.Kjerne.hverKart(), null, { timeout: 40000 });
  await p.waitForTimeout(2000);
  await p.keyboard.press('PageUp');                         // lagre paa kartet
  await p.waitForTimeout(2000);
  // ny side i samme nettleser: tittelmenyen, og last derfra
  await p.close();
  p = T.merk(await ctx.newPage());
  await p.goto(U);
  await T.tilTittel(p, { alene: true });
  sjekk(await p.evaluate(() => window.moonDebug.Kjerne.iMeny()), 'tittelmenyen er framme');
  await p.keyboard.press('PageDown');
  await p.waitForTimeout(3000);
  sjekk(await p.evaluate(() => window.moonDebug.Kjerne.hverKart()), 'spillet fra kartet er lastet');
  sjekk(!(await p.evaluate(() => window.moonDebug.Kjerne.iMeny())), 'menyen henger ikke igjen etter lasting');
  sjekk(await p.evaluate(() => document.getElementById('hint').hidden), 'ingen menyhint over kartet');
  await T.skjerm(p, 't32.png');
});
