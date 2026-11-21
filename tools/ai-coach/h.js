window.SIM = (() => {
  const SAVE0 = JSON.parse(JSON.stringify(SAVE));
  let POL = {};
  function setup(o) {
    // fresh copy of default save, then apply preset
    for (const k in SAVE) delete SAVE[k];
    Object.assign(SAVE, JSON.parse(JSON.stringify(SAVE0)));
    SAVE.up = o.up || {}; SAVE.unl = o.unl || {};
    if (o.tw) Object.assign(SAVE.tw, o.tw);
    SAVE.twL = o.twL || {};
    if (o.deck) SAVE.deck = o.deck.slice();
    SAVE.ch = {}; SAVE.chD = {}; SAVE.chLv = {};
    (o.chars || []).forEach(([id, dup, lv]) => { SAVE.ch[id] = true; SAVE.chD[id] = dup || 0; SAVE.chLv[id] = lv || 0; });
    SAVE.chEq = o.chEq || ''; SAVE.chEq2 = o.chEq2 || '';
    SAVE.pet = {}; (o.pets || []).forEach(([id, dup]) => SAVE.pet[id] = dup || 0); SAVE.petEq = o.petEq || '';
    SAVE.inv = {}; SAVE.eq = {};
    (o.gear || []).forEach(([sid, g, t, lv]) => { const id = itemId(sid, g, t); SAVE.inv[id] = lv || 0; SAVE.eq[sid] = id; });
    SAVE.twK = o.twK || {};
    SAVE.st.maxWave = o.fresh ? 0 : 99;   // v0.60 새싹 보호는 처음 하는 계정(fresh)만
    applyDeck(); recalcBon();
    POL = o.pol || {};
  }
  const spread = em => em.slice().sort((a, b) => minD(b) - minD(a))[0];
  const minD = s => towers.length ? Math.min(...towers.map(t => Math.hypot(t.x - s.x, t.y - s.y))) : (R() * 10);
  const tierOf = k => SAVE.deck.indexOf(k);
  function bot(dt) {
    G.botT = (G.botT || 0) - dt; if (G.botT > 0) return; G.botT = .5;
    if (G.hp < G.maxHp * .4 && G.scrap >= repairCost() && !POL.noRepair) { repairBed(); return; }
    { const fc0 = G.fence < FENCE_LV.length - 1 ? fenceCost(G.fence + 1) : Infinity;
      if (G.fence < Math.min(10, Math.floor(G.wave / 3)) && G.scrap >= fc0 && towers.length >= 4) { upgradeFence(); return; } }
    const types = SAVE.deck.filter(isUnlocked).filter(k => !(POL.ban || []).includes(k));
    const empty = SLOTS.filter(s => !s.tower);
    const UT = k => ['glue', 'fan'].includes(TBASE(k));
    const rank = k => TDEF[k].grade * 10 + (UT(k) ? 0 : 5) + tierOf(k) * .1;
    const avail = types.filter(k => (!UT(k) || !towers.some(t => TBASE(t.type) === TBASE(k))) && (!POL.maxEach || towers.filter(t => t.type === k).length < POL.maxEach));
    const best = avail.slice().sort((a, b) => rank(b) - rank(a))[0] || types[types.length - 1];
    const pickFor = budget => { if (POL.only) return isUnlocked(POL.only) && TDEF[POL.only].cost <= budget ? POL.only : null;
      const ok = avail.filter(k => TDEF[k].cost <= budget).sort((a, b) => rank(b) - rank(a)); return ok[0] || null; };
    // fill slots — save for the best tower unless poor for long
    if (empty.length) {
      const k = TDEF[best].cost <= G.scrap ? best : (towers.length < 2 ? pickFor(G.scrap) : null);
      const kk = POL.only ? pickFor(G.scrap) : k;
      if (kk) { place(spread(empty), kk); return; }
      if (!towers.length) return;
    }
    // swap weakest for better during break
    if (!empty.length && G.phase === 'break' && !POL.only) {
      const w = towers.filter(t => !UT(t.type)).sort((a, b) => rank(a.type) - rank(b.type))[0];
      if (w && rank(w.type) + 8 < rank(best) && G.scrap + sellValue(w) >= TDEF[best].cost + 20) { const sl = w.slot; sell(w); place(sl, best); return; }
    }
    const ups = towers.filter(t => t.lvl < towerCap()).sort((a, b) => a.lvl - b.lvl || tierOf(b.type) - tierOf(a.type));
    const fc = G.fence < FENCE_LV.length - 1 ? fenceCost(G.fence + 1) : Infinity;
    if (G.scrap >= fc && (!ups.length || G.scrap >= fc + ups[0].upCost * .5)) { upgradeFence(); return; }
    if (ups.length && G.scrap >= ups[0].upCost) { upgrade(ups[0]); return; }
  }
  function run(maxWave = 60, maxSec = 30000) {
    closePanels(); startGame(false); if (TUT.on) endTut(false);
    G.breakT = 0;
    const bat0 = SAVE.bat, cr0 = SAVE.crate; let steps = 0; const dt = .05;
    while (!G.over && G.wave <= maxWave && steps * dt < maxSec) {
      update(dt); bot(dt); steps++;
      if (G.phase === 'break' && G.breakT > 1) G.breakT = 1;
    }
    const r = { wave: G.cleared, over: G.over, reason: G.overReason || '', fence: G.fence, towers: towers.map(t => t.type + t.lvl).join(','),
      crates: SAVE.crate - cr0, meter: Object.fromEntries(Object.entries(G.meter || {}).map(([k, v]) => [k, Math.round(v)])), perks: JSON.stringify(G.perkLv || {}), repairs: G.repairs || 0 };
    const e = endRun(); r.bat = (e && e.gain) || 0; r.batTotal = SAVE.bat - bat0;
    return r;
  }
  function runFixed(k, lvl, maxWave, mate, fence) {
    closePanels(); startGame(false); if (TUT.on) endTut(false); G.scrap = 1e9;
    for (let i = 0; i < (fence || 0); i++) upgradeFence(); G.hp = G.maxHp;
    SLOTS.forEach((sl, i) => { const kk = i % 2 ? k : (mate || 'cannon'); const t = new TCLASS[kk](kk, sl); t.lvl = lvl; t.spent = 0; sl.tower = t; towers.push(t); });
    G.breakT = 0; let steps = 0;
    while (!G.over && G.wave <= maxWave && steps < 2e6) { update(0.05); steps++; if (G.phase === 'break') G.breakT = 0; }
    const m = G.meter || {}, tot = Object.values(m).reduce((a, b) => a + b, 0);
    return { wave: G.over ? G.cleared : G.wave - 1, share: Math.round((m[k] || 0) / Math.max(1, tot) * 100) };
  }
  return { setup, run, runFixed, bot, setPerk: f => { window.openPerk = () => { const offer = rollPerks(); if (!offer.length) return; const p = f(offer); pickPerk(p); }; } };
})();
window.showToast = () => {}; window.sfx = () => {}; window.achPop = () => {};
SIM.setPerk(o => o[(R() * o.length) | 0].id);
'ok'
;(() => {
  const BY_G = [0, 1, 2, 3].map(g => Object.keys(TDEF).filter(k => TDEF[k].grade === g));
  SIM.randDeck = () => { for (;;) { const used = new Set(); const d = DECK_GRADE.map(g => { const c = BY_G[g].filter(k => !used.has(k)); const k = c[(R() * c.length) | 0]; used.add(k); return k; });
    if (!['glue', 'fan'].includes(TBASE(d[0])) || !['glue', 'fan'].includes(TBASE(d[1]))) return d; } };   // 처음 쓸 두 칸이 모두 보조 타워면 다시
  function mixBot(dt) {
    G.botT = (G.botT || 0) - dt; if (G.botT > 0) return; G.botT = .6;
    if (G.hp < G.maxHp * .4 && G.scrap >= repairCost()) { repairBed(); return; }
    const fc = G.fence < FENCE_LV.length - 1 ? fenceCost(G.fence + 1) : Infinity;
    if (G.fence < Math.min(10, Math.floor(G.wave / 3)) && G.scrap >= fc && towers.length >= 4) { upgradeFence(); return; }
    const empty = SLOTS.filter(s => !s.tower);
    const UT = k => ['glue', 'fan'].includes(TBASE(k));
    const types = SAVE.deck.filter(isUnlocked).filter(k => !UT(k) || towers.filter(t => TBASE(t.type) === TBASE(k)).length < 2);
    if (empty.length && types.length) {
      if (!G.botTarget || !types.includes(G.botTarget)) {   // 다음에 살 타워를 무작위로 정해 두고 돈을 모은다 (새로 풀린 등급일수록 조금 더 자주)
        const w = types.map(k => 1 + TDEF[k].grade * .5); let r = R() * w.reduce((a, b) => a + b, 0), i = 0; while ((r -= w[i]) > 0) i++; G.botTarget = types[i]; }
      if (G.scrap >= TDEF[G.botTarget].cost) { const sl = empty.slice().sort((a, b) => minD(b) - minD(a))[0]; place(sl, G.botTarget); G.botTarget = null; return; }
      if (towers.length < 3) return;
    }
    if (!empty.length && G.phase === 'break' && R() < .3) {   // 칸이 다 차면 가끔 낮은 등급 타워를 팔고 높은 등급으로 교체
      const hiG = Math.max(...types.map(k => TDEF[k].grade));
      const w = towers.filter(t => TDEF[t.type].grade < hiG).sort((a, b) => TDEF[a.type].grade - TDEF[b.type].grade || a.lvl - b.lvl)[0];
      if (w) { const c = types.filter(k => TDEF[k].grade > TDEF[w.type].grade); const k = c[(R() * c.length) | 0];
        if (k && G.scrap + sellValue(w) >= TDEF[k].cost) { const sl = w.slot; sell(w); place(sl, k); return; } }
    }
    const ups = towers.filter(t => t.lvl < towerCap()).sort((a, b) => a.lvl - b.lvl);
    if (G.scrap >= fc && (!ups.length || G.scrap >= fc + ups[0].upCost * .5)) { upgradeFence(); return; }
    if (ups.length && G.scrap >= ups[0].upCost) upgrade(ups[0]);
  }
  const minD = s => towers.length ? Math.min(...towers.map(t => Math.hypot(t.x - s.x, t.y - s.y))) : R() * 10;
  SIM.runMix = (maxWave = 250) => {
    closePanels(); startGame(false); if (TUT.on) endTut(false); G.breakT = 0; G.botTarget = null;
    const ts = {}, dt = .05; let steps = 0;
    while (!G.over && G.wave <= maxWave && steps * dt < 40000) {
      update(dt); mixBot(dt); steps++; if (G.phase === 'break' && G.breakT > 1) G.breakT = 1;
      if (G.phase === 'wave') for (const t of towers) { const o = ts[t.type] || (ts[t.type] = { s: 0, lv: 0 }); o.s += dt; o.lv += dt * t.lvl; }
    }
    const per = {};
    for (const k in ts) per[k] = { s: Math.round(ts[k].s), lv: +(ts[k].lv / Math.max(1e-9, ts[k].s)).toFixed(2), dmg: Math.round((G.meter || {})[k] || 0), kills: (SAVE.twK || {})[k] || 0,
      n: towers.filter(t => t.type === k).length, spent: towers.filter(t => t.type === k).reduce((a, t) => a + t.spent, 0) };
    return { wave: G.cleared, fence: G.fence, fenceDmg: Math.round((G.meter || {}).fence || 0), per, deck: SAVE.deck.slice() };
  };
})();
'ok2'
;(() => {
  // v0.60: 게임 안 AUTO 자동 설치(autoPilot)로 한 판. AI_VAL은 0으로 두고(학습 데이터가 AI 자신을 따라가지 않게) 등급 순으로만 고른다
  SIM.runAuto = (maxWave = 250) => {
    const keep = { ...AI_VAL }; for (const k in AI_VAL) AI_VAL[k] = 0;
    SAVE.unl = { ...(SAVE.unl || {}), autobuild: true }; SET.autoWave = true; SET.autoBuild = true; SET.share = false;
    closePanels(); startGame(false); if (TUT.on) endTut(false);
    const dt = .05; let steps = 0;
    while (!G.over && G.wave <= maxWave && steps * dt < 40000) { update(dt); steps++; }
    const per = {};
    for (const k in G.twTime) per[k] = { s: G.twTime[k], dmg: Math.round((G.meter || {})[k] || 0), n: towers.filter(t => t.type === k).length };
    const r = { wave: G.cleared, fence: G.fence, per, deck: SAVE.deck.slice(), policy: 'auto' };
    Object.assign(AI_VAL, keep); G.hp = 0; update(dt); endRun();
    return r;
  };
})();
'auto'
