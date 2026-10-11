// Versjonssjekk i nettspill: en gjest med et annet lagringsformat (gammel side i hurtigbufferen)
// faar beskjed og blir ikke staaende og vente; romlisten viser bare rom med samme versjon.
const T = require('./felles');
const { sjekk, U } = T;

/* kodene i romlisten slik siden ser den etter 4 sekunder */
const romliste = (p) => p.evaluate(() => new Promise((ok) => { let siste = []; const stopp = Romliste.lytt((l) => { siste = l; }); setTimeout(() => { stopp(); ok(siste.map((r) => r.kode)); }, 4000); }));

T.kjor(async () => {
  const b = await T.nettleser();
  const vert = await T.side(b, { navn: 'vert', innst: { navn: 'Tom', spill: 'sammen', offentlig: true } });
  const gml = await T.side(b, { navn: 'gml', innst: { navn: 'Gml' } });
  const ny = await T.side(b, { navn: 'ny', innst: { navn: 'Ny' } });
  await vert.goto(U);
  await T.tilTittel(vert);
  const lenke = await T.lagRom(vert, 'vert');
  const kode = await vert.evaluate(() => window.moonDebug.Nett.kode());
  console.log('rom', kode, 'format vert', await vert.evaluate(() => Kjerne.formatId()));
  // en gjest med samme versjon ser rommet; en med et annet format ser det ikke
  await ny.goto(U); await T.tilTittel(ny);
  await gml.goto(U); await T.tilTittel(gml);
  await gml.evaluate(() => { Kjerne.formatId = () => 12345; });
  const lNy = await romliste(ny), lGml = await romliste(gml);
  console.log('romlisten: samme versjon', lNy, '| annet format', lGml);
  sjekk(lNy.includes(kode) && !lGml.includes(kode), 'romlisten viser bare rom med samme versjon');
  // gjesten med annet format bruker invitasjonslenken
  await gml.goto(lenke);
  await gml.waitForFunction(() => window.moonDebug && window.moonDebug.Kjerne.iIntro(), null, { timeout: 30000 });
  await gml.evaluate(() => { Kjerne.formatId = () => 12345; });
  await gml.waitForTimeout(1500);
  /* ett trykk hopper ikke alltid over introen (den gjoer ferdig en overgang foerst) */
  for (let i = 0; ; i++) {
    await gml.mouse.click(400, 280);
    try { await gml.waitForFunction(() => window.moonDebug.Kjerne.menyKlar(), null, { timeout: 12000 }); break; }
    catch (e) { if (i >= 3) throw e; }
  }
  await gml.waitForTimeout(1500);
  console.log('join-siden:', await T.rad(gml, 0), '|', await T.rad(gml, 1), '|', await T.rad(gml, 2), 'valg', await T.valg(gml));
  await T.trykk(gml, 'ControlLeft', 120);
  for (let i = 0; i < 6; i++) { await gml.waitForTimeout(1000); console.log('  ', i, await gml.evaluate(() => window.moonDebug.modus()), await T.statusTekst(gml)); }
  const st = await T.statusTekst(gml);
  const m = await gml.evaluate(() => window.moonDebug.modus());
  const nVert = await vert.evaluate(() => window.moonDebug.Nett.spillere().length);
  console.log('gjest med annet format: modus', m, 'status', st, '| spillere hos verten', nVert);
  sjekk(/annen versjon av Moonstone/.test(st), 'gjesten faar beskjed om annen versjon');
  sjekk(m !== 'venter' && m !== 'gjest' && nVert === 1, 'gjesten blir ikke staaende og vente, og verten har ham ikke i rommet');
});
