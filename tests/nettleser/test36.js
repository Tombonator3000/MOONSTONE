// Turns: gjester som kobler til paa nytt, nummer uten hull, Copy Link og F10 fra en gjest, og joystick som henger naar gjestens side stopper.
const T = require('./felles');
const { sjekk, U, trykk, valg, rad, velg, venter } = T;

const spillere = (p) => p.evaluate(() => window.moonDebug.Nett.spillere().map((s) => s.navn + ':' + s.spiller).join(' '));
const eier = (p) => p.evaluate(() => window.moonDebug.Kjerne.portSpillere()[1]);
const pos = (p, k) => p.evaluate((k) => { const K = window.moonDebug.Kjerne, s = 0x8d5b4 + k * 0x84; return [K.les8(s + 0x7e) << 8 | K.les8(s + 0x7f), K.les8(s + 0x80) << 8 | K.les8(s + 0x81)]; }, k);
/* ny side i samme kontekst som Kari, som starter med id-en hennes i sessionStorage */
async function medId(ctx, navn, id) {
  const p = T.merk(await ctx.newPage(), navn);
  await p.addInitScript((id) => { try { if (!sessionStorage.getItem('moonstone.klient')) sessionStorage.setItem('moonstone.klient', id); } catch (e) {} }, id);
  return p;
}

T.kjor(async () => {
  const b = await T.nettleser();
  const vert = await T.side(b, { navn: 'vert', innst: { navn: 'Tom', spill: 'sammen' } });
  const kari = await T.side(b, { navn: 'kari', innst: { navn: 'Kari' } });
  const kariCtx = kari.context();
  const ola = await T.side(b, { navn: 'ola', innst: { navn: 'Ola' } });
  await vert.goto(U);
  await T.tilTittel(vert);
  const lenke = await T.lagRom(vert, 'vert');
  await T.bliMed(kari, lenke);
  await T.bliMed(ola, lenke);
  console.log('spillere:', await spillere(vert));
  sjekk(await spillere(vert) === 'Tom:0 Kari:1 Ola:2', 'tre spillere med nummer 0, 1, 2');

  // Copy Link fra en gjest: romsiden er vertens (pilen staar paa Copy Link)
  await vert.waitForTimeout(1000);
  console.log('romsiden, linje', await valg(vert), JSON.stringify(await rad(vert, 3)));
  await trykk(kari, 'ControlLeft', 150, 2000);
  sjekk(await vert.evaluate(() => document.getElementById('meny').hidden), 'fire fra en gjest paa Copy Link aapnet ikke sidemenyen hos verten');
  await trykk(kari, 'ArrowDown', 150, 1500);
  sjekk(await valg(vert) === 3, 'gjesten flytter ikke pilen paa romsiden (' + await valg(vert) + ')');

  // F10 fra en gjest avslutter ikke spillet for alle
  await trykk(kari, 'F10', 150, 2500);
  sjekk(!(await vert.evaluate(() => window.moonDebug.Kjerne.stoppet())) && await vert.evaluate(() => window.moonDebug.modus()) === 'vert', 'F10 fra en gjest stoppet ikke spillet hos verten');

  // Kari laster siden paa nytt (samme fane) og kommer tilbake
  await kari.reload();
  await vert.waitForTimeout(2000);
  console.log('etter at Kari gikk:', await spillere(vert));
  await vert.waitForTimeout(500);
  // i menyen tettes hullet: Ola blir 1, og Kari faar 2 naar hun kommer tilbake (1 er tatt)
  sjekk(await spillere(vert) === 'Tom:0 Ola:1', 'i menyen tettes hullet naar en gaar: ' + await spillere(vert));
  await T.bliMed(kari, lenke);
  console.log('Kari tilbake:', await spillere(vert));
  sjekk(await spillere(vert) === 'Tom:0 Ola:1 Kari:2', 'Kari er med igjen, uten hull: ' + await spillere(vert));

  // en kopi av fanen (Dupliser) har samme id i sessionStorage mens den forste lever: den blir en egen deltaker
  const id = await kari.evaluate(() => sessionStorage.getItem('moonstone.klient'));
  const kopi = await medId(kariCtx, 'kopi', id);
  await T.bliMed(kopi, lenke);
  console.log('med kopien:', await spillere(vert));
  sjekk(await spillere(vert) === 'Tom:0 Ola:1 Kari:2 Kari:3', 'en kopi av fanen kaster ikke ut den forste: ' + await spillere(vert));
  sjekk(await kopi.evaluate(() => sessionStorage.getItem('moonstone.klient')) !== id, 'kopien har faatt sin egen id');
  await kopi.close();
  await vert.waitForTimeout(2500);
  // fanen til Kari lukkes uten at siden rekker aa si fra (som et krasj), og hun aapner lenken igjen i en ny fane med samme id: samme plass
  await kari.evaluate(() => { window.moonDebug.Nett.avslutt = () => {}; });
  await kari.close({ runBeforeUnload: false });
  await vert.waitForTimeout(1500);
  const kari2 = await medId(kariCtx, 'kari2', id);
  await T.bliMed(kari2, lenke);
  console.log('etter krasj:', await spillere(vert));
  sjekk(await spillere(vert) === 'Tom:0 Ola:1 Kari:2', 'Kari er tilbake paa plass 2 etter at fanen ble borte: ' + await spillere(vert));
  sjekk(await kari2.evaluate(() => sessionStorage.getItem('moonstone.klient')) === id, 'og beholdt id-en (ingen levende fane hadde den)');

  // Back og Select Knight: tre spillere. Verten, Ola og Kari velger i den rekkefolgen.
  await velg(vert, 5);
  await vert.waitForTimeout(2500);
  await velg(vert, 3);
  for (const [p, n] of [[vert, 0], [ola, 1], [kari2, 2]]) {
    await venter(async () => await eier(vert) === n);
    await trykk(p, 'ControlLeft', 150, 2500);
    await trykk(p, 'Enter', 120, 3000);
  }
  sjekk(await venter(async () => await eier(vert) === 0 && !(await vert.evaluate(() => window.moonDebug.Kjerne.velgerRidder())), 30000), 'kartet: verten har turen');
  await trykk(vert, 'KeyE', 120, 1500);
  sjekk(await venter(async () => await eier(vert) === 1, 30000), 'Ola har turen (plass 1)');
  await ola.waitForTimeout(2000);
  // Ola holder ned, og siden hans fryser (skjult fane, laast mobil): ridderen skal stoppe hos verten
  const p1 = await pos(vert, 1);
  await ola.keyboard.down('ArrowDown');
  await ola.waitForTimeout(800);
  // spillokka hos Ola stopper (som naar fanen skjules uten at nettleseren sier fra): ingen nye meldinger
  await ola.evaluate(() => { window.__raf = window.requestAnimationFrame; window.requestAnimationFrame = () => 0; });
  const spor = [];
  for (let i = 0; i < 6; i++) { await vert.waitForTimeout(1000); spor.push(await pos(vert, 1)); }
  console.log('Ola', JSON.stringify([p1].concat(spor)));
  sjekk(spor[0][1] > p1[1], 'Olas ridder gikk mens han holdt');
  const sist = spor[spor.length - 1], forr = spor[spor.length - 3];
  sjekk(sist[0] === forr[0] && sist[1] === forr[1], 'og stoppet etter at siden hans sto stille');
  await ola.keyboard.up('ArrowDown');
  await ola.evaluate(() => { window.requestAnimationFrame = window.__raf; requestAnimationFrame(() => {}); });
  const st = await kari2.evaluate(() => window.moonDebug.statistikk);
  sjekk(st.avvik === 0, 'ingen avvik i sjekksummene ' + JSON.stringify(st));
});
