// Flyten uten startside: rett i introen, hopp over, alt nettspill i tittelmenyen (Turns med tre).
const T = require('./felles');
const { sjekk, U, trykk } = T;

async function venterIntro(p, n) {
  await p.waitForFunction(() => window.moonDebug && window.moonDebug.modus() === 'alene' && window.moonDebug.Kjerne.iIntro(), null, { timeout: 30000 });
  sjekk(await p.evaluate(() => document.getElementById('lasting').hidden), n + ': lasteteppet er borte, introen gaar');
}
async function tilTittel(p, n) {
  await p.waitForFunction(() => window.moonDebug.Kjerne.menyKlar(), null, { timeout: 60000 });
  await p.waitForTimeout(800);
  sjekk(true, n + ': tittelmenyen er naadd');
}
const hint = (p) => p.evaluate(() => { const h = document.getElementById('hint'); return h.hidden ? '' : h.textContent; });

T.kjor(async () => {
  const b = await T.nettleser();
  const o = { konsoll: true, innstHvisTom: { spill: 'sammen' } };
  const vert = await T.side(b, Object.assign({ navn: 'vert', utklipp: true }, o));
  const kari = await T.side(b, Object.assign({ navn: 'kari' }, o));
  const ola = await T.side(b, Object.assign({ navn: 'ola' }, o));

  // verten: siden starter rett paa introen
  await vert.goto(U);
  await venterIntro(vert, 'vert');
  console.log('vert hint foer trykk:', await hint(vert));
  await vert.waitForTimeout(3000);
  await T.skjerm(vert, 't12-intro.png');
  await trykk(vert, 'Enter');                              // forste trykk: lyd, ikke hopp
  await vert.waitForTimeout(1000);
  sjekk(await vert.evaluate(() => window.moonDebug.Kjerne.iIntro()), 'vert: forste trykk hoppet ikke over introen');
  console.log('vert hint etter trykk:', await hint(vert));
  await trykk(vert, 'Enter');                              // andre trykk: hopp over
  await tilTittel(vert, 'vert');
  sjekk((await hint(vert)).startsWith('Klikk'), 'vert: menyhintet om klikk vises');
  await T.skjerm(vert, 't12-tittel.png');
  for (let i = 0; i < 4; i++) await trykk(vert, 'ArrowDown');
  await trykk(vert, 'ControlLeft');                        // Options
  await trykk(vert, 'ControlLeft');                        // Online Game paa Options-siden
  await vert.waitForTimeout(800);
  await T.skjerm(vert, 't12-online.png');
  await trykk(vert, 'ArrowDown'); await trykk(vert, 'ArrowDown');
  await trykk(vert, 'ControlLeft');                        // Choose Name
  sjekk(await vert.evaluate(() => !document.getElementById('navn-dialog').hidden), 'vert: navnedialogen aapnet fra menyen');
  await vert.fill('#navn-felt', 'Tom');
  await vert.press('#navn-felt', 'Enter');
  await vert.waitForTimeout(800);
  sjekk(await vert.evaluate(() => document.getElementById('navn-dialog').hidden), 'vert: navnedialogen er lukket');
  await T.skjerm(vert, 't12-navn.png');
  await trykk(vert, 'ArrowUp'); await trykk(vert, 'ArrowUp');
  await trykk(vert, 'ControlLeft');                        // Host Game
  await vert.waitForFunction(() => window.moonDebug.modus() === 'vert', null, { timeout: 30000 });
  await vert.waitForTimeout(1500);
  await trykk(vert, 'ArrowDown');
  await trykk(vert, 'ControlLeft');                        // Public On
  await trykk(vert, 'ArrowUp');
  await trykk(vert, 'ControlLeft');                        // Copy Link
  const lenke = await vert.evaluate(() => navigator.clipboard.readText());
  console.log('lenke', lenke);
  sjekk(/rom=[A-Z0-9]{6}/.test(lenke) && lenke.includes('mqtt='), 'vert: lenken har romkoden og megleren');
  await T.skjerm(vert, 't12-vert.png');

  // Kari via lenken: introen, ett trykk hopper over, Join Game aapnes med rommet
  await kari.goto(lenke);
  await venterIntro(kari, 'kari');
  console.log('kari hint:', await hint(kari));
  await kari.waitForTimeout(1500);
  await trykk(kari, 'Enter');
  await tilTittel(kari, 'kari');
  await kari.waitForTimeout(1500);
  await T.skjerm(kari, 't12-kari-join.png');
  sjekk(!(await kari.evaluate(() => location.search.includes('rom='))), 'kari: rom= er fjernet fra adressen');
  await trykk(kari, 'ControlLeft');                        // Room CODE
  sjekk(await kari.evaluate(() => !document.getElementById('navn-dialog').hidden), 'kari: spurt om navn');
  await kari.fill('#navn-felt', 'Kari');
  await kari.press('#navn-felt', 'Enter');
  await kari.waitForFunction(() => window.moonDebug.modus() === 'gjest', null, { timeout: 30000 }).then(() => sjekk(true, 'kari: med som gjest')).catch(e => sjekk(false, 'kari ble ikke med ' + e.message));

  // Ola: trykk paa skjermen (forste = lyd, andre = hopp), Join Game fra den offentlige listen
  await ola.goto(U);
  await venterIntro(ola, 'ola');
  await ola.waitForTimeout(1500);
  await ola.mouse.click(400, 280);
  await ola.waitForTimeout(1000);
  sjekk(await ola.evaluate(() => window.moonDebug.Kjerne.iIntro()), 'ola: forste trykk paa skjermen hoppet ikke over');
  await ola.mouse.click(400, 280);
  await tilTittel(ola, 'ola');
  // Ola bruker musen: klikk paa radene, og vent til siden har byttet
  const radKlikk = async (y) => { const r = await ola.locator('#lerret').boundingBox(); await ola.mouse.click(r.x + r.width / 2, r.y + r.height * ((y + 9) / 200)); };
  await radKlikk(0xb0);                                    // Options
  await ola.waitForFunction(() => window.moonDebug.Kjerne.menyRad(0x55) === -2, null, { timeout: 15000 });
  await ola.waitForTimeout(1500);
  await radKlikk(0x64);                                    // Online Game
  await ola.waitForFunction(() => window.moonDebug.Kjerne.les8(0xf8200 + 48) === 0x48, null, { timeout: 15000 });   // "Host Game"
  await ola.waitForTimeout(1500);
  await radKlikk(0x78);                                    // Join Game
  await ola.waitForTimeout(4000);
  await T.skjerm(ola, 't12-ola-join.png');
  await radKlikk(0x64);                                    // forste rom
  await ola.waitForTimeout(1500);
  sjekk(await ola.evaluate(() => !document.getElementById('navn-dialog').hidden), 'ola: spurt om navn');
  await ola.fill('#navn-felt', 'Ola Nordmann');
  await ola.press('#navn-felt', 'Enter');
  await ola.waitForFunction(() => window.moonDebug.modus() === 'gjest', null, { timeout: 30000 }).then(() => sjekk(true, 'ola: med som gjest')).catch(e => sjekk(false, 'ola ble ikke med ' + e.message));

  await vert.waitForTimeout(4000);
  for (const [n, p] of [['vert', vert], ['kari', kari], ['ola', ola]]) await T.skjerm(p, 't12-rom-' + n + '.png');
  await trykk(vert, 'ArrowDown');
  await trykk(vert, 'ArrowDown');
  await trykk(vert, 'ControlLeft');                        // Back: spillet med tre spillere
  await vert.waitForTimeout(9000);
  for (const [n, p] of [['vert', vert], ['kari', kari], ['ola', ola]]) await T.skjerm(p, 't12-spill-' + n + '.png');
  for (const [n, p] of [['kari', kari], ['ola', ola]]) {
    const st = await p.evaluate(() => window.moonDebug.statistikk);
    sjekk(st.sjekket > 0 && st.avvik === 0, n + ': sjekksummer ' + JSON.stringify(st));
  }

  // verten lukker: gjestene starter paa nytt fra introen
  await vert.close();
  for (const [n, p] of [['kari', kari], ['ola', ola]]) {
    await p.waitForFunction(() => window.moonDebug.modus() === 'alene' && window.moonDebug.Kjerne.iIntro(), null, { timeout: 30000 })
      .then(() => sjekk(true, n + ': tilbake i introen etter at verten forsvant'))
      .catch(e => sjekk(false, n + ': ' + e.message));
  }
  await kari.waitForTimeout(500);
  console.log('kari status:', await T.statusTekst(kari));
  await T.skjerm(kari, 't12-etter.png');
});
