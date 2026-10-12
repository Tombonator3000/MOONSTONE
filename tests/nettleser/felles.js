// Felles hjelpefunksjoner for nettlesertestene (Playwright).
//
// Innstillinger (argument eller miljovariabel):
//   --port N   / MOONSTONE_PORT      porten til nettsiden paa 127.0.0.1 (standard 8765)
//   --url URL  / MOONSTONE_URL       hele adressen til nettsiden (overstyrer --port)
//   --ut MAPPE / MOONSTONE_UT        hvor skjermbilder og tilstander legges (standard: ny mappe i /tmp)
//                MOONSTONE_PEER      PeerJS-serveren (standard 127.0.0.1:9000)
//                MOONSTONE_MQTT      MQTT-megleren (standard ws://127.0.0.1:8883/mqtt)
//                MOONSTONE_HEADLESS  port/moonstone-headless (standard: den i repoet)
//                MOONSTONE_GAMLE     mappe med lagringer fra eldre versjoner (kamp6.sav, gml.sav)
const { chromium } = require('playwright');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');

function arg(navn) {
  const a = process.argv;
  for (let i = 2; i < a.length; i++) {
    if (a[i] === '--' + navn && i + 1 < a.length) return a[i + 1];
    if (a[i].startsWith('--' + navn + '=')) return a[i].slice(navn.length + 3);
  }
  return undefined;
}

const PORT = arg('port') || process.env.MOONSTONE_PORT || '8765';
const BASE = arg('url') || process.env.MOONSTONE_URL || 'http://127.0.0.1:' + PORT + '/';
const PEER = process.env.MOONSTONE_PEER || '127.0.0.1:9000';
const MQTT = process.env.MOONSTONE_MQTT || 'ws://127.0.0.1:8883/mqtt';
/* adressen med de lokale serverne for nettspill */
const U = BASE + (BASE.includes('?') ? '&' : '?') + 'peer=' + PEER + '&mqtt=' + MQTT + '&mqttv=4';
const ORIGIN = new URL(BASE).origin;
const UT = arg('ut') || process.env.MOONSTONE_UT || fs.mkdtempSync(path.join(os.tmpdir(), 'moonstone-test-'));
fs.mkdirSync(UT, { recursive: true });
const HEADLESS = process.env.MOONSTONE_HEADLESS || path.resolve(__dirname, '../../port/moonstone-headless');
const GAMLE = process.env.MOONSTONE_GAMLE || '';

/* ---- resultater ---- */
const antall = { ok: 0, feil: 0 };
const sjekk = (ok, t) => { console.log((ok ? 'OK   ' : 'FEIL ') + t); if (ok) antall.ok++; else antall.feil++; };
const nettlesere = [];

/* kjorer testen, lukker nettleserne og gir exit 1 ved feil */
function kjor(fn) {
  fn().catch((e) => { sjekk(false, 'testen stoppet: ' + (e && e.stack ? e.stack : e)); }).then(async () => {
    console.log('Ferdig: ' + antall.ok + ' OK, ' + antall.feil + ' FEIL');
    await Promise.all(nettlesere.map((b) => b.close().catch(() => {})));
    process.exit(antall.feil || !antall.ok ? 1 : 0);
  });
}

/* ---- nettleser og sider ---- */
async function nettleser() {
  const b = await chromium.launch({ executablePath: process.env.CHROME || undefined, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  nettlesere.push(b);
  return b;
}

/* ny side i en egen kontekst. navn: merkelapp i loggen, innst: moonstone.innstillinger
   (innstHvisTom: bare om ingen er lagret), konsoll: logg feil fra konsollen,
   utklipp: lov til aa lese utklippstavlen, ctx: ekstra valg til newContext */
async function side(b, o = {}) {
  const ctx = await b.newContext(Object.assign({ viewport: { width: 800, height: 560 } }, o.ctx || {}));
  if (o.utklipp) await ctx.grantPermissions(['clipboard-read', 'clipboard-write'], { origin: ORIGIN });
  /* testene leser norske meldinger: norsk er valgt med mindre testen sier noe annet */
  const innst = o.innst ? Object.assign({ sprak: 'no' }, o.innst) : null;
  const hvisTom = Object.assign({ sprak: 'no' }, o.innstHvisTom || {});
  if (innst) await ctx.addInitScript((s) => { try { localStorage.setItem('moonstone.innstillinger', s); } catch (e) {} }, JSON.stringify(innst));
  else await ctx.addInitScript((s) => { try { if (!localStorage.getItem('moonstone.innstillinger')) localStorage.setItem('moonstone.innstillinger', s); } catch (e) {} }, JSON.stringify(hvisTom));
  const p = await ctx.newPage();
  merk(p, o.navn, o.konsoll);
  return p;
}

function merk(p, navn, konsoll) {
  const n = navn ? navn + ' ' : '';
  p.on('pageerror', (e) => console.log(n + 'pageerror: ' + e.message));
  if (konsoll) p.on('console', (m) => { if (m.type() === 'error') console.log(n + 'console: ' + m.text()); });
  return p;
}

/* tast ned i ms, saa vent (menyen tegnes paa nytt i opptil 0,7 s) */
async function trykk(p, key, ms = 220, etter = 900) { await p.keyboard.down(key); await p.waitForTimeout(ms); await p.keyboard.up(key); await p.waitForTimeout(etter); }

/* fra lastingen til tittelmenyen. Ett trykk slaar paa lyden og hopper over introen.
   alene: vent ogsaa paa modus 'alene'. */
async function tilTittel(p, o = {}) {
  const klikk = o.klikk || 1, tid = o.tid || 60000;   /* tregt naar maskinen har mye annet aa gjoere */
  await p.waitForFunction((alene) => window.moonDebug && (!alene || window.moonDebug.modus() === 'alene') && window.moonDebug.Kjerne.iIntro(), !!o.alene, { timeout: tid });
  await p.waitForTimeout(1500);
  if (klikk > 1) { await p.mouse.click(400, 280); await p.waitForTimeout(1000); }
  /* introen gjoer ferdig overgangen foer den slutter; kom ikke menyen, proev et trykk til */
  for (let i = 0; ; i++) {
    await p.mouse.click(400, 280);
    try { await p.waitForFunction(() => window.moonDebug.Kjerne.menyKlar(), null, { timeout: 25000 }); break; } catch (e) {}
    if (!(await p.evaluate(() => window.moonDebug.Kjerne.iIntro()))) {
      /* introen er over, men menyen er ikke tegnet ennaa (Join Game henter romlisten) */
      await p.waitForFunction(() => window.moonDebug.Kjerne.menyKlar(), null, { timeout: tid });
      break;
    }
    if (i >= 2) throw new Error('introen sluttet ikke etter ' + (i + 1 + (klikk > 1 ? 1 : 0)) + ' trykk');
    console.log('   (fortsatt i introen, trykker igjen)');
  }
  await p.waitForTimeout(o.etter || 800);
}

/* ---- minnet i kjernen ---- */
const les16 = (p, a) => p.evaluate((a) => { const K = window.moonDebug.Kjerne; return K.les8(a) << 8 | K.les8(a + 1); }, a);
/* valgt linje (VALG $8F2D2): tittelmenyen 0-4, sidene 1-5 */
const valg = (p) => les16(p, 0x8f2d2);
/* tekstene paa siden (meny.c: PAGE_TEXTS $F8200, 6 a 48 byte) */
const rad = (p, i) => p.evaluate((i) => { const K = window.moonDebug.Kjerne; let s = ''; for (let j = 0; j < 48; j++) { const c = K.les8(0xf8200 + i * 48 + j); if (!c) break; s += String.fromCharCode(c); } return s; }, i);
const rader = async (p) => { const ut = []; for (let i = 0; i < 6; i++) ut.push(await rad(p, i)); return ut; };
async function venterRad(p, i, t, n = 60) { for (let k = 0; k < n; k++) { if (await rad(p, i) === t) return true; await p.waitForTimeout(150); } return false; }

/* flytt pilen til linjen og trykk fire. Tastene gaar til siden p, valget leses fra siden v
   (i tur for tur kan en gjest styre vertens meny). */
async function velg(p, linje, o = {}) {
  const v = o.v || p, ned = o.ned || 'ArrowDown', opp = o.opp || 'ArrowUp';
  for (let n = 0; n < 12; n++) {
    const x = await valg(v);
    if (x === linje) break;
    const k = x < linje ? ned : opp;
    await p.keyboard.down(k); await p.waitForTimeout(120); await p.keyboard.up(k);
    for (let m = 0; m < 30 && await valg(v) === x; m++) await p.waitForTimeout(50);
    await p.waitForTimeout(200);
  }
  if (await valg(v) !== linje) console.log('   (kom ikke til linje ' + linje + ', staar paa ' + await valg(v) + ')');
  await trykk(p, o.fire || 'ControlLeft', 120);
}

/* verten lager et rom: Options, Online Game, Host Game. Venter paa modusen og gir lenken. */
async function lagRom(vert, modus) {
  await velg(vert, 4); await venterRad(vert, 0, 'Options');
  await velg(vert, 1); await venterRad(vert, 1, 'Host Game');
  await velg(vert, 1);
  await vert.waitForFunction((m) => window.moonDebug.modus() === m, modus, { timeout: 30000 });
  await vert.waitForTimeout(1500);
  return vert.evaluate(() => window.moonDebug.Nett.invitasjon());
}

/* en gjest blir med via invitasjonslenken (rommet staar oeverst i Join Game) */
async function bliMed(p, lenke, modus = 'gjest', vent = 2500) {
  await p.goto(lenke);
  await tilTittel(p, { klikk: 1, etter: 1500 });
  await trykk(p, 'ControlLeft', 120);
  await p.waitForFunction((m) => window.moonDebug.modus() === m, modus, { timeout: 30000 });
  await p.waitForTimeout(vent);
}

/* Separate (hver for seg): verten (Tom) lager rommet, Kari blir med med romkoden, og begge
   starter sitt eget spill fra tittelmenyen til kartet. merke: forstavelse paa skjermbildene. */
async function hverForSegPaaKartet(b, merke) {
  const vert = await side(b, { navn: 'vert', konsoll: true, innst: { navn: 'Tom' } });
  const kari = await side(b, { navn: 'kari', konsoll: true, innst: { navn: 'Kari' } });
  await vert.goto(U);
  await tilTittel(vert, { alene: true });
  for (let i = 0; i < 4; i++) await trykk(vert, 'ArrowDown');
  await trykk(vert, 'ControlLeft');                        // Options
  await trykk(vert, 'ControlLeft');                        // Online Game paa Options-siden
  await skjerm(vert, merke + '-online.png');
  await trykk(vert, 'ControlLeft');                        // Host Game (pilen staar paa den)
  await vert.waitForFunction(() => window.moonDebug.modus() === 'hver', null, { timeout: 30000 });
  sjekk(true, 'vert: rom i Separate, modus hver');
  await vert.waitForTimeout(1500);
  const lenke = await vert.evaluate(() => window.moonDebug.Nett.invitasjon());
  console.log('lenke', lenke);
  const kode = lenke.match(/rom=([A-Z0-9]{6})/)[1];

  await kari.goto(U + '&rom=' + kode);
  await tilTittel(kari, { alene: true, klikk: 1 });            // med romkoden holder ett trykk
  await kari.waitForTimeout(1500);
  await trykk(kari, 'ControlLeft');                        // rommet er valgt paa Join Game
  await kari.waitForFunction(() => window.moonDebug.modus() === 'hver', null, { timeout: 30000 });
  sjekk(true, 'kari: med i rommet, modus hver');
  await skjerm(kari, merke + '-kari-med.png');
  await trykk(kari, 'ControlLeft');                        // Back fra meldingen: rett til tittelmenyen
  await skjerm(kari, merke + '-kari-tittel.png');
  await trykk(kari, 'ArrowUp');                            // Select Knight

  // verten: Back fra Host-siden (rad 5), saa tittelmenyen; pilen staar paa Options, opp en
  await trykk(vert, 'ArrowDown'); await trykk(vert, 'ArrowDown');
  await trykk(vert, 'ControlLeft');
  await skjerm(vert, merke + '-vert-tittel.png');
  await trykk(vert, 'ArrowUp');
  // begge til kartet: Select Knight, ridderen, Return godtar navnet
  await Promise.all([[vert, 'vert'], [kari, 'kari']].map(async ([p, n]) => {
    await trykk(p, 'ControlLeft'); await p.waitForTimeout(8000); await skjerm(p, merke + '-' + n + '-a.png');
    await trykk(p, 'ControlLeft'); await p.waitForTimeout(4000); await skjerm(p, merke + '-' + n + '-b.png');
    await trykk(p, 'Enter');
  }));
  await vert.waitForFunction(() => window.moonDebug.Kjerne.hverKart(), null, { timeout: 40000 }).catch(() => console.log('vert ikke paa kartet'));
  await kari.waitForFunction(() => window.moonDebug.Kjerne.hverKart(), null, { timeout: 40000 }).catch(() => console.log('kari ikke paa kartet'));
  await vert.waitForTimeout(5000);
  return { vert, kari };
}

/* ridderne slik siden ser dem (hver.c): [x, y, liv, figur, navn] per plass, og hele ridderen paa plass 0 */
const ridderInfo = (p) => p.evaluate(() => { const K = window.moonDebug.Kjerne; return { r: [0, 1, 2, 3].map((k) => K.hverRidder(k).concat(K.hverNavn(k))), blob0: K.hverBlob(0) }; });
const duell = (p) => p.evaluate(() => window.moonDebug.duell());

/* fire paa kartet ved siden av den andre ridderen gir valgene; 2 er Battle with. Kommer ikke
   valgene (turen har ikke begynt ennaa paa en treg maskin), trykkes fire igjen. */
async function angrip(p, merke) {
  for (let i = 0; i < 3; i++) {
    await trykk(p, 'ControlLeft');
    if (await venter(() => p.evaluate(() => !!window.moonDebug.Kjerne.kartValg()), 10000)) break;
    console.log('   (ingen valg paa kartet ennaa, trykker fire igjen)');
  }
  await skjerm(p, merke + '-valg.png');
  await trykk(p, 'Digit2');
}

/* x-posisjonen til ridderen paa plass 1 i kampen (+$04) */
const kampX1 = (p) => p.evaluate(() => { const K = window.moonDebug.Kjerne; return K.les8(0x8d638 + 4) << 8 | K.les8(0x8d638 + 5); });

/* i en duell: p (som har maskinen) gaar mot den andre ridderen og slaar til kampen er over
   (den andre staar stille). Tar et skjermbilde hos annen hvert 40. steg. Gir tiden i sekunder. */
async function slaaTilKampenErOver(p, annen, merke) {
  const pos = () => p.evaluate(() => { const K = window.moonDebug.Kjerne, w = (a) => (K.les8(a) << 8 | K.les8(a + 1)) << 16 >> 16;
    return { hx: w(0x8d5b4 + 4), hy: w(0x8d5b4 + 8), kx: w(0x8d638 + 4), ky: w(0x8d638 + 8) }; });
  const t0 = Date.now();
  let i = 0;
  while (Date.now() - t0 < 150000 && await duell(p)) {
    const q = await pos();
    const dx = q.kx - q.hx, dy = q.ky - q.hy;
    const taster = [];
    if (Math.abs(dy) > 6) taster.push(dy < 0 ? 'ArrowUp' : 'ArrowDown');
    if (Math.abs(dx) > 60) taster.push(dx < 0 ? 'ArrowLeft' : 'ArrowRight');
    else if (Math.abs(dy) <= 6) { taster.push('ControlLeft'); taster.push(dx < 0 ? 'ArrowLeft' : 'ArrowRight'); }
    if (i % 25 === 0) console.log('kamp', JSON.stringify(q), taster.join('+'));
    for (const t of taster) await p.keyboard.down(t);
    await p.waitForTimeout(taster.includes('ControlLeft') ? 300 : 200);
    for (const t of taster) await p.keyboard.up(t);
    await p.waitForTimeout(100);
    if (i++ % 40 === 0) await skjerm(annen, merke + '-kamp' + i + '.png');
  }
  const s = Math.round((Date.now() - t0) / 1000);
  console.log('kampen tok', s, 's');
  return s;
}

/* bytene i to ridderblobber (heks) som er ulike, som "indeks:foer>etter" */
function blobForskjell(a, b) {
  const ut = [];
  for (let i = 0; i < 312; i += 2) if (a.slice(i, i + 2) !== b.slice(i, i + 2)) ut.push((i / 2).toString(16) + ':' + a.slice(i, i + 2) + '>' + b.slice(i, i + 2));
  return ut.join(' ');
}

async function venter(fn, ms = 20000) { const t = Date.now(); while (Date.now() - t < ms) { if (await fn()) return true; await new Promise((r) => setTimeout(r, 200)); } return false; }
const statusTekst = (p) => p.evaluate(() => document.getElementById('status').textContent);
const skjerm = (p, navn) => p.screenshot({ path: path.join(UT, navn) });

/* ---- tilstander laget med moonstone-headless (sjekkes ikke inn) ---- */
const TIL_KARTET = ['--headless', '--online-meny', '--log', '0', '--press', '100:esc:4', '--press', '700:down:10', '--press', '760:down:10',
  '--press', '820:down:10', '--press', '880:fire:10', '--press', '1300:fire:10', '--press', '1500:return:6'];
const OPPSKRIFTER = {
  'kart_ny.sav': TIL_KARTET.concat(['--save-state', '2000:kart_ny.sav', '--frames', '2001']),   // et spill paa kartet
  'ny.sav': TIL_KARTET.concat(['--save-state', '1600:ny.sav', '--frames', '1601']),             // like foer kartet
};
function tilstand(navn) {
  const fil = path.join(UT, navn);
  if (fs.existsSync(fil)) return fil;
  if (!OPPSKRIFTER[navn]) throw new Error('ingen oppskrift for ' + navn);
  if (!fs.existsSync(HEADLESS)) throw new Error('fant ikke ' + HEADLESS + ' (make -C port headless)');
  execFileSync(HEADLESS, OPPSKRIFTER[navn], { cwd: UT, encoding: 'utf8' });
  if (!fs.existsSync(fil)) throw new Error('moonstone-headless laget ikke ' + navn);
  return fil;
}
/* en lagring fra en eldre versjon, eller null (testen hopper over sjekken) */
function gammelLagring(navn) {
  const fil = GAMLE ? path.join(GAMLE, navn) : '';
  if (fil && fs.existsSync(fil)) return fil;
  console.log('HOPPER OVER sjekken med ' + navn + ' (legg den i MOONSTONE_GAMLE for aa ta den med)');
  return null;
}

module.exports = { PORT, BASE, U, ORIGIN, UT, HEADLESS, sjekk, kjor, nettleser, side, merk, trykk, tilTittel,
  les16, valg, rad, rader, venterRad, velg, lagRom, bliMed, hverForSegPaaKartet, ridderInfo, duell, angrip, kampX1, slaaTilKampenErOver, blobForskjell, venter, statusTekst, skjerm, tilstand, gammelLagring };
