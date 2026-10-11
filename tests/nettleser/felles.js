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
  const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  nettlesere.push(b);
  return b;
}

/* ny side i en egen kontekst. navn: merkelapp i loggen, innst: moonstone.innstillinger
   (innstHvisTom: bare om ingen er lagret), konsoll: logg feil fra konsollen,
   utklipp: lov til aa lese utklippstavlen, ctx: ekstra valg til newContext */
async function side(b, o = {}) {
  const ctx = await b.newContext(Object.assign({ viewport: { width: 800, height: 560 } }, o.ctx || {}));
  if (o.utklipp) await ctx.grantPermissions(['clipboard-read', 'clipboard-write'], { origin: ORIGIN });
  if (o.innst) await ctx.addInitScript((s) => { try { localStorage.setItem('moonstone.innstillinger', s); } catch (e) {} }, JSON.stringify(o.innst));
  if (o.innstHvisTom) await ctx.addInitScript((s) => { try { if (!localStorage.getItem('moonstone.innstillinger')) localStorage.setItem('moonstone.innstillinger', s); } catch (e) {} }, JSON.stringify(o.innstHvisTom));
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

/* fra lastingen til tittelmenyen. Forste trykk slaar paa lyden, det andre hopper over introen.
   Med en invitasjonslenke holder ett trykk (klikk: 1). alene: vent ogsaa paa modus 'alene'. */
async function tilTittel(p, o = {}) {
  const klikk = o.klikk || 2, tid = o.tid || 30000;
  await p.waitForFunction((alene) => window.moonDebug && (!alene || window.moonDebug.modus() === 'alene') && window.moonDebug.Kjerne.iIntro(), !!o.alene, { timeout: tid });
  await p.waitForTimeout(1500);
  await p.mouse.click(400, 280);
  if (klikk > 1) { await p.waitForTimeout(1000); await p.mouse.click(400, 280); }
  await p.waitForFunction(() => window.moonDebug.Kjerne.menyKlar(), null, { timeout: tid });
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
  les16, valg, rad, rader, venterRad, velg, lagRom, bliMed, venter, statusTekst, skjerm, tilstand, gammelLagring };
