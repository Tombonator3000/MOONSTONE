// Mobil: sidemenyen i spillets stil, navnet til ridderen med tekstfelt, valgene paa kartet
// som knapper med styrekorset og Fire.
const T = require('./felles');
const { sjekk } = T;
const MOBIL = { viewport: { width: 412, height: 892 }, deviceScaleFactor: 2.625, isMobile: true, hasTouch: true,
  userAgent: 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Mobile Safari/537.36' };

T.kjor(async () => {
  const b = await T.nettleser();
  const p = await T.side(b, { ctx: MOBIL });
  p.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') console.log('console: ' + m.text()); });
  const cdp = await p.context().newCDPSession(p);
  const touch = async (x, y, ms = 150) => {
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y }] });
    await p.waitForTimeout(ms);
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
    await p.waitForTimeout(500);
  };
  const boks = (sel) => p.evaluate((s) => { const e = document.querySelector(s); if (!e) return null; const r = e.getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height, skjult: e.hidden }; }, sel);
  const midt = async (sel) => { const r = await boks(sel); return [r.x + r.w / 2, r.y + r.h / 2]; };
  const kors = async (retning) => {
    const r = await boks('#touch .kors');
    const cx = r.x + r.w / 2, cy = r.y + r.h / 2, d = r.w * 0.35;
    const [dx, dy] = { opp: [0, -d], ned: [0, d] }[retning];
    await touch(cx + dx, cy + dy);
  };
  await p.goto(T.BASE);
  await p.waitForFunction(() => window.moonDebug && window.moonDebug.Kjerne.iIntro(), null, { timeout: 30000 });
  await p.waitForTimeout(1500);
  sjekk(await p.evaluate(() => Spillgrafikk.klar()), 'spillets grafikk er lastet');
  const l = await boks('#lerret');
  await touch(l.x + l.w / 2, l.y + l.h / 2); await p.waitForTimeout(800); await touch(l.x + l.w / 2, l.y + l.h / 2);
  await p.waitForFunction(() => window.moonDebug.Kjerne.menyKlar(), null, { timeout: 30000 });
  await p.waitForTimeout(1200);
  await T.skjerm(p, 'm2-tittel.png');
  // sidemenyen
  await touch(...await midt('#meny-knapp'));
  await p.waitForTimeout(800);
  await T.skjerm(p, 'm2-meny1.png');
  await p.evaluate(() => document.getElementById('meny').scrollTo(0, 700));
  await p.waitForTimeout(400);
  await T.skjerm(p, 'm2-meny2.png');
  await p.evaluate(() => document.getElementById('meny').scrollTo(0, 1500));
  await p.waitForTimeout(400);
  await T.skjerm(p, 'm2-meny3.png');
  const hint = await p.evaluate(() => { const h = document.getElementById('hint'); const m = document.getElementById('meny'); return { hint: h.hidden ? '' : h.textContent, mz: getComputedStyle(m).zIndex, mbg: getComputedStyle(m).backgroundColor }; });
  console.log('hint/meny', JSON.stringify(hint));
  // avkrysning ved trykk: Skygger
  const skyggeFoer = await p.evaluate(() => document.getElementById('effekt-skygge').checked);
  await p.evaluate(() => document.getElementById('effekt-skygge').closest('label').scrollIntoView({ block: 'center' }));
  await p.waitForTimeout(300);
  await touch(...await midt('#effekt-skygge + .verdi'));
  const skyggeEtter = await p.evaluate(() => document.getElementById('effekt-skygge').checked);
  const verdi = await p.evaluate(() => document.querySelector('[data-for=effekt-skygge]').dataset.ptTekst);
  sjekk(skyggeFoer !== skyggeEtter && verdi === (skyggeEtter ? 'På' : 'Av'), 'trykk paa raden slaar av og paa (' + verdi + ')');
  await touch(...await midt('#effekt-skygge + .verdi'));
  await p.evaluate(() => document.getElementById('lukk-meny').scrollIntoView());
  await touch(...await midt('#lukk-meny'));
  await p.waitForTimeout(500);
  sjekk(await p.evaluate(() => document.getElementById('meny').hidden), 'Tilbake til spillet lukket menyen');
  // til kartet: Select Knight, ridderen, navnet (fire godtar)
  for (let i = 0; i < 3; i++) await kors('ned');
  const fire = await midt('#touch button.fire');
  await touch(fire[0], fire[1]);
  await p.waitForTimeout(7000);
  await touch(fire[0], fire[1]);
  await p.waitForTimeout(4000);
  const navnKnapp = await p.evaluate(() => !document.getElementById('navn-knapp').hidden);
  sjekk(navnKnapp, 'knappen for ridderens navn vises paa mobil');
  await T.skjerm(p, 'm2-navn.png');
  await touch(...await midt('#navn-knapp'));
  await p.waitForTimeout(500);
  sjekk(await p.evaluate(() => !document.getElementById('ridder-dialog').hidden), 'tekstfeltet for navnet aapnet');
  await p.fill('#ridder-felt', 'Kari Øy 2');
  await touch(...await midt('#ridder-ok'));
  await p.waitForFunction(() => !window.moonDebug.Kjerne.navnAktiv(), null, { timeout: 40000 }).catch(() => {});
  await p.waitForFunction(() => window.moonDebug.Kjerne.hverKart(), null, { timeout: 40000 });
  const ridder = await p.evaluate(() => window.moonDebug.Kjerne.ridderNavn(0));
  sjekk(ridder === 'KARI OY 2', 'ridderen fikk navnet fra tekstfeltet (' + ridder + ')');
  await p.waitForTimeout(2000);
  // KARI ved siden av (som i headless-scenarioet), saa fire: «1 Enter Village», «2 Battle with KARI»
  await p.evaluate(() => { const K = window.moonDebug.Kjerne; K.hverKmd(1, 2, ''); K.hverKmd(5, 2, ''); K.hverKmd(2, 0, '1 14 12 1 1 KARI'); });
  await p.waitForTimeout(1500);
  await touch(fire[0], fire[1]);
  await p.waitForFunction(() => !document.getElementById('valg').hidden, null, { timeout: 15000 }).catch(() => {});
  await p.waitForTimeout(800);
  const v = await p.evaluate(() => ({ skjult: document.getElementById('valg').hidden, tittel: document.getElementById('valg-tittel').dataset.ptTekst,
    rader: [...document.querySelectorAll('.valg-knapp')].map((b) => b.getAttribute('aria-label')) }));
  console.log('valg', JSON.stringify(v));
  sjekk(!v.skjult && v.rader.length === 2 && /Enter Village/.test(v.rader[0]) && /Battle with KARI/.test(v.rader[1]) && v.tittel === 'KARI OY 2 may ...', 'valgene vises som knapper');
  await T.skjerm(p, 'm2-valg.png');
  await kors('ned');
  const m1 = await p.evaluate(() => [...document.querySelectorAll('.valg-knapp')].findIndex((b) => b.classList.contains('merket')));
  await kors('opp');
  const m2 = await p.evaluate(() => [...document.querySelectorAll('.valg-knapp')].findIndex((b) => b.classList.contains('merket')));
  sjekk(m1 === 1 && m2 === 0, 'styrekorset flytter pilen (' + m1 + ', ' + m2 + ')');
  await touch(fire[0], fire[1]);
  await p.waitForTimeout(2500);
  const etter = await p.evaluate(() => ({ skjult: document.getElementById('valg').hidden, valg: window.moonDebug.Kjerne.kartValg() }));
  sjekk(etter.skjult && !etter.valg, 'Fire valgte Enter Village (spillet venter ikke lenger)');
  await p.waitForTimeout(3000);
  await T.skjerm(p, 'm2-etter-valg.png');
});
