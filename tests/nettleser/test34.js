// Turns-rom med gjest: gjesten styrer menyen og velger Keyboard > Fire. Ingen av dem skal begynne aa vente paa en tast.
const T = require('./felles');
const { sjekk, U, rad, venterRad, velg, statusTekst } = T;

T.kjor(async () => {
  const b = await T.nettleser();
  const vert = await T.side(b, { navn: 'vert', innst: { navn: 'Tom', spill: 'sammen' } });
  const kari = await T.side(b, { navn: 'kari', innst: { navn: 'Kari' } });
  await vert.goto(U);
  await T.tilTittel(vert);
  const lenke = await T.lagRom(vert, 'vert');
  await T.bliMed(kari, lenke, 'gjest', 3000);
  sjekk(await rad(vert, 0) === await rad(kari, 0), 'samme side hos begge: ' + await rad(kari, 0));
  // romsiden er vertens: verten gaar tilbake til tittelmenyen, saa styrer Kari menyen: Options, Keyboard, Fire
  await velg(vert, 5);
  await vert.waitForFunction(() => window.moonDebug.Kjerne.menyRad(0x55) !== -2, null, { timeout: 15000 }).catch(() => {});
  await vert.waitForTimeout(1500);
  await velg(kari, 4, { v: vert });
  sjekk(await venterRad(vert, 0, 'Options'), 'Kari aapnet Options hos verten');
  await velg(kari, 2, { v: vert });
  sjekk(await venterRad(vert, 1, 'Fire  Ctrl'), 'Kari aapnet Keyboard');
  await velg(kari, 1, { v: vert });
  await vert.waitForTimeout(1500);
  sjekk(!(await vert.evaluate(() => Inndata.fanger())), 'verten venter ikke paa en tast');
  sjekk(!(await kari.evaluate(() => Inndata.fanger())), 'Kari venter ikke paa en tast');
  sjekk(await rad(vert, 1) === 'Fire  Ctrl', 'linjen er uendret: ' + await rad(vert, 1));
  console.log('vert status:', await statusTekst(vert));
  console.log('kari status:', await statusTekst(kari));
  sjekk((await statusTekst(vert)).includes('kan ikke endres'), 'verten faar forklaringen');
  sjekk((await statusTekst(kari)).includes('kan ikke endres'), 'Kari faar forklaringen');
  // Default Controls fra Kari endrer heller ikke vertens oppsett
  await vert.evaluate(() => { const o = Inndata.oppsett(); o.flytt1 = 'wasd'; Inndata.settOppsett(o); });
  await velg(kari, 5, { v: vert });                            // Back til Options
  await venterRad(vert, 0, 'Options');
  await velg(kari, 4, { v: vert });                            // Default Controls
  await vert.waitForTimeout(1500);
  sjekk((await vert.evaluate(() => Inndata.oppsett().flytt1)) === 'wasd', 'Default Controls fra gjesten endret ikke verten');
  const st = await kari.evaluate(() => window.moonDebug.statistikk);
  sjekk(st.avvik === 0, 'ingen avvik i sjekksummene ' + JSON.stringify(st));
});
