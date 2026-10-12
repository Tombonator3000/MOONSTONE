// PC-klikk reiser med originalfart. Samme kommando har betrodd eier i Turns.
const T = require('./felles');
const { sjekk } = T;
const pos = (p, k = 0) => p.evaluate(k => moonDebug.Kjerne.hverRidder(k).slice(0, 2), k);
const kart = p => p.evaluate(() => moonDebug.Kjerne.kartAktiv());
const eier = p => p.evaluate(() => moonDebug.Kjerne.portSpillere()[1]);
const lik = (a, b) => a[0] === b[0] && a[1] === b[1];
async function punkt(p, x, y) {
  return p.evaluate(({ x, y }) => {
    const r = document.querySelector('#lerret').getBoundingClientRect(), c = moonDebug.Visning.utsnitt(), v = moonDebug.Kjerne.vindu();
    return { x: r.left + (v[0] + x * 2 - c[0]) / (c[2] - c[0]) * r.width,
      y: r.top + (v[1] + y - c[1]) / (c[3] - c[1]) * r.height };
  }, { x, y });
}
async function klikk(p, x, y, button = 'left') {
  const q = await punkt(p, x, y);
  await p.mouse.click(q.x, q.y, { button });
}
async function reis(p, x, y) { await klikk(p, x + 4.5, y + 10.5); }
async function portrett(p, k) {
  const x = await p.evaluate(k => { const K = moonDebug.Kjerne, a = 0x8f516 + 2*k; return (K.les8(a)<<8 | K.les8(a+1)) + 32; }, k);
  await klikk(p, x, 118);
}
async function faste(vert, gjesteport) {
  await vert.evaluate(port => {
    const N = moonDebug.Nett, g = N.spillere().find(s => !s.vert);
    N.settPort('vert', 'p1'); N.settPort(g.id, port); N.settModus('fast');
  }, gjesteport);
  await vert.waitForTimeout(500);
}

T.kjor(async () => {
  const b = await T.nettleser(), errors = [];
  const original = { hd: 'original', hdValgt: true };
  const p = await T.side(b, { innst: original });
  p.on('pageerror', e => errors.push(e.message));
  await p.goto(T.U); await T.tilTittel(p);
  const seed = T.tilstand('kart_ny.sav');
  const start = async () => { await p.setInputFiles('#importer', seed); await p.waitForFunction(() => moonDebug.Kjerne.kartAktiv()); await p.waitForTimeout(150); };
  await start();
  sjekk(lik(await pos(p), [10, 10]), 'PC-fixturen staar paa originalkartet ved 10,10');
  await reis(p, 30, 25);
  const first = await pos(p);
  sjekk(!lik(first, [30, 25]), 'et PC-klikk gir reise, uten teleportering');
  sjekk(await T.venter(async () => lik(await pos(p), [30, 25]), 12000), 'PC-klikk gaar til riktig fotpunkt paa kartet');
  await p.waitForTimeout(500);
  sjekk(lik(await pos(p), [30, 25]), 'ridderen stopper ved kartmaalet');
  sjekk(await T.les16(p, 0x8e7a0) === 20, 'PC-reisen bruker originalens trekkbudsjett');
  await reis(p, 60, 50); await p.waitForTimeout(120); await reis(p, 36, 22);
  sjekk(await T.venter(async () => lik(await pos(p), [36, 22]), 10000), 'nytt PC-klikk erstatter reisen');
  await start(); await reis(p, 70, 60); await p.waitForTimeout(150); await klikk(p, 120, 80, 'right');
  await p.waitForTimeout(300); const stopped = await pos(p); await p.waitForTimeout(600);
  sjekk(lik(stopped, await pos(p)), 'hoyreklikk stopper reisen');
  await start(); await reis(p, 70, 60); await p.waitForTimeout(150); await T.trykk(p, 'ArrowLeft', 120, 300);
  const manual = await pos(p); await p.waitForTimeout(600);
  sjekk(lik(manual, await pos(p)) && manual[0] < 20, 'tastaturstyring avbryter klikkreise');
  await start(); await reis(p, 70, 60); await p.waitForTimeout(150); await T.trykk(p, 'Space', 180, 100);
  sjekk(await T.venter(async () => !(await kart(p)) && await p.evaluate(() => moonDebug.Kjerne.pekerAktiv()), 12000), 'inventaret stanser reisen og kartklikk');
  await p.context().close();

  const vert = await T.side(b, { navn: 'vert', innst: { ...original, navn: 'Tom', spill: 'sammen' } });
  const guest = await T.side(b, { navn: 'gjest', innst: { ...original, navn: 'Kari' } });
  for (const page of [vert, guest]) page.on('pageerror', e => errors.push(e.message));
  await vert.goto(T.U); await T.tilTittel(vert);
  const link = await T.lagRom(vert, 'vert'); console.log('rom opprettet'); await T.bliMed(guest, link); console.log('gjest klar');
  await T.velg(vert, 5); await vert.waitForTimeout(700); await T.velg(vert, 3);
  await vert.waitForFunction(() => moonDebug.Kjerne.velgerRidder() && !moonDebug.Kjerne.navnAktiv());
  await portrett(vert, 0); await vert.waitForFunction(() => moonDebug.Kjerne.navnKlar()); console.log('vert navn klart'); await T.trykk(vert, 'Enter', 100, 900);
  await guest.waitForFunction(() => moonDebug.Kjerne.portSpillere()[1] === 1 && !moonDebug.Kjerne.navnAktiv());
  await portrett(guest, 3); await guest.waitForFunction(() => moonDebug.Kjerne.navnKlar()); console.log('gjest navn klart'); await T.trykk(guest, 'Enter', 100, 1200);
  await vert.waitForFunction(() => moonDebug.Kjerne.kartAktiv() && moonDebug.Kjerne.portSpillere()[1] === 0);
  await guest.waitForFunction(() => moonDebug.Kjerne.kartAktiv());
  const initial = await pos(vert);
  await reis(guest, 30, 30);
  await guest.evaluate(() => moonDebug.Nett.sendKart(34, 40, 0, 'p2'));
  await vert.waitForTimeout(700);
  sjekk(lik(initial, await pos(vert)), 'gjest paa feil tur kan verken klikke eller forfalske eier');
  await reis(vert, 30, 30);
  sjekk(await T.venter(async () => lik(await pos(vert), [30, 30]) && lik(await pos(guest), [30, 30]), 12000), 'vertens PC-klikk reiser likt hos begge i Turns');
  for (const port of ['p1', 'ingen']) {
    await faste(vert, port);
    await guest.evaluate(() => moonDebug.Nett.sendKart(44, 45)); await reis(guest, 40, 35); await vert.waitForTimeout(500);
    sjekk(lik(await pos(vert), [30, 30]), 'faste porter: gjest paa ' + port + ' kan ikke starte kartreise');
  }
  await faste(vert, 'p2'); await reis(vert, 50, 40); await vert.waitForTimeout(500);
  sjekk(lik(await pos(vert), [30, 30]), 'faste porter: vert paa port1 avvises selv om ridderen tilhoerer verten');
  await guest.evaluate(() => { for (const [x,y] of [[null,40],[34.5,40],['34',40],[320,40],[34,200],[-2,40]]) moonDebug.Nett.sendKart(x,y); });
  await vert.waitForTimeout(500);
  sjekk(lik(await pos(vert), [30, 30]), 'feiltypede, ikke-heltallige og ytre gjestekoordinater avvises');
  await reis(guest, 40, 35);
  sjekk(await T.venter(async () => lik(await pos(vert), [40, 35]) && lik(await pos(guest), [40, 35]), 10000), 'faste porter: port2 kan klikke og styre uavhengig av spillernummer');
  await vert.evaluate(() => moonDebug.Nett.settModus('auto')); await vert.waitForTimeout(500);
  await reis(vert, 70, 65); await vert.waitForTimeout(120); await T.trykk(vert, 'KeyE', 100, 900);
  sjekk(await T.venter(async () => await eier(vert) === 1 && await kart(vert), 15000), 'E avbryter reisen og gir turen til neste menneske');
  const gpos = await pos(vert, 1); await vert.waitForTimeout(500);
  sjekk(lik(gpos, await pos(vert, 1)), 'forrige spillers maal flytter ikke den neste ridderen');
  const gx = Math.max(0, gpos[0] - 10), gy = Math.min(180, gpos[1] + 10);
  await reis(guest, gx, gy);
  sjekk(await T.venter(async () => lik(await pos(vert, 1), [gx, gy]) && lik(await pos(guest, 1), [gx, gy]), 12000), 'gjestens eget kartklikk virker paa gjestens tur');
  await guest.waitForTimeout(2500);
  const stats = await guest.evaluate(() => moonDebug.statistikk);
  sjekk(stats.sjekket > 0 && stats.avvik === 0, 'synkroniserte klikkreiser gir ingen sjekksumavvik: ' + JSON.stringify(stats));
  sjekk(errors.length === 0, 'ingen JavaScript-feil: ' + JSON.stringify(errors));
  await T.skjerm(vert, 'kartmus1-turns.png');
});
