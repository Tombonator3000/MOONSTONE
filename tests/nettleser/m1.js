// Mobil: beroering paa en telefon (staaende). Hopper over introen med trykk paa skjermen,
// flytter pilen med styrekorset og gaar til kartet med Fire-knappen.
const T = require('./felles');
const { sjekk } = T;
const MOBIL = { viewport: { width: 412, height: 892 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true,
  userAgent: 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Mobile Safari/537.36' };

T.kjor(async () => {
  const b = await T.nettleser();
  const p = await T.side(b, { ctx: MOBIL });
  const cdp = await p.context().newCDPSession(p);
  const touch = async (x, y, ms = 150) => {
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y }] });
    await p.waitForTimeout(ms);
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
    await p.waitForTimeout(700);
  };
  const boks = (sel) => p.evaluate((s) => { const e = document.querySelector(s); if (!e) return null; const r = e.getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height, skjult: e.hidden || getComputedStyle(e).display === 'none' }; }, sel);
  const knapp = (navn) => p.evaluate((n) => { const e = [...document.querySelectorAll('#touch button')].find((x) => x.textContent === n); const q = e.getBoundingClientRect(); return { x: q.x + q.width / 2, y: q.y + q.height / 2 }; }, navn);
  const kors = async (retning, ms = 150) => {
    const r = await boks('#touch .kors');
    const cx = r.x + r.w / 2, cy = r.y + r.h / 2, d = r.w * 0.35;
    const [dx, dy] = { opp: [0, -d], ned: [0, d], venstre: [-d, 0], hoyre: [d, 0] }[retning];
    await touch(cx + dx, cy + dy, ms);
  };
  await p.goto(T.BASE);
  await p.waitForFunction(() => window.moonDebug && window.moonDebug.Kjerne.iIntro(), null, { timeout: 30000 });
  await p.waitForTimeout(2000);
  await T.skjerm(p, 'm1-01-intro.png');
  console.log('touch', JSON.stringify(await boks('#touch')), 'kors', JSON.stringify(await boks('#touch .kors')), 'lerret', JSON.stringify(await boks('#lerret')));
  console.log('hint:', await p.evaluate(() => document.getElementById('hint').textContent));
  const l = await boks('#lerret');
  await touch(l.x + l.w / 2, l.y + l.h / 2);
  await p.waitForFunction(() => window.moonDebug.Kjerne.menyKlar(), null, { timeout: 30000 });
  await p.waitForTimeout(1500);
  await T.skjerm(p, 'm1-02-tittel.png');
  sjekk(!(await boks('#touch')).skjult, 'ett trykk paa skjermen hoppet over introen, knappene vises i tittelmenyen');
  const v0 = await T.valg(p);
  await kors('ned'); await p.waitForTimeout(600);
  const v1 = await T.valg(p);
  sjekk(v1 === v0 + 1, 'ned paa styrekorset flytter pilen (' + v0 + ' -> ' + v1 + ')');
  await kors('ned'); await p.waitForTimeout(600); await kors('ned'); await p.waitForTimeout(600);
  const v3 = await T.valg(p);
  sjekk(v3 === 3, 'tre ned: pilen paa Select Knight (' + v3 + ')');
  const f = await knapp('Fire');
  await touch(f.x, f.y);
  await p.waitForTimeout(6000);
  await T.skjerm(p, 'm1-03-etter-fire.png');
  sjekk(!(await p.evaluate(() => window.moonDebug.Kjerne.iMeny())), 'Fire valgte Select Knight');
  await touch(f.x, f.y);                                  // velg ridder
  await p.waitForTimeout(4000);
  await T.skjerm(p, 'm1-04-navn.png');
  await touch(f.x, f.y);                                  // Fire godtar navnet
  await p.waitForFunction(() => window.moonDebug.Kjerne.hverKart(), null, { timeout: 30000 }).catch(() => {});
  await T.skjerm(p, 'm1-05-kart.png');
  sjekk(await p.evaluate(() => window.moonDebug.Kjerne.hverKart()), 'Fire valgte ridder og godtok navnet: paa kartet');
});
