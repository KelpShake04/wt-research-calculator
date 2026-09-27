// War Thunder research calculator. Needs data.js (window.WT_DATA) and a #wtcalc container
// with the markup from index.html. Wrapped in a function so it cannot clash with a host page
// (for example a Blogger theme that uses jQuery's $).
(() => {
  const T = {
    ko: {
      title: "워썬더 연구 계산기", country: "국가", branch: "병과", modeResearch: "연구 체크", modeTarget: "목표 선택", modeBuy: "구매 체크", modeProgress: "진행 RP 입력",
      avg: "판당 평균 RP", reset: "이 트리 초기화", langBtn: "English", howto: "사용법",
      fold: "▴ 접기", openAll: "폴더 모두 펼치기", closeAll: "폴더 모두 접기", units: "대",
      hint: "연구 체크: 줄마다 마지막으로 연구한 차량만 누르면 앞 차량까지 연구+구매로 체크. 다시 누르면 해제. 보유한 프리미엄도 눌러 둘 것. 구매 체크: 연구만 하고 안 산 차량을 눌러 미구매(점선)로 표시. 랭크 해금 대수는 구매한 차량만 셈. 목표 선택: 목표 차량을 누르면 남은 RP·SL 계산. 진행 RP 입력: 연구 중인 차량을 누르고 이미 모은 RP 입력(게임에서 차량에 마우스를 올리면 나오는 숫자).",
      noTarget: "목표 차량을 선택하세요.", done: "연구 완료", remainRP: "남은 RP", battles: "예상 판 수", targetSL: "목표 구매+승무원 SL",
      pathSL: "경로 전체 구매 SL", steps: "남은 차량", premium: "프리미엄",
      discount: "SL 할인", noDiscount: "없음", discounted: "할인 적용",
      pathRP: "경로", unlockRP: "랭크 해금용", unlockSL: "해금용 구매 SL", buy: "구매 추천", notBought: "미구매",
      legend: "주황: 목표 경로 · 파랑: 랭크 해금용 연구 추천 · '구매 추천': 해금 대수를 채우려면 사야 하는 차량",
      short: "트리 전체로도 대수를 못 채우는 랭크", 
      note: "랭크 해금 대수는 이 트리에서 구매(보유) 체크한 차량 기준입니다. 추천은 추가 RP가 가장 적은 차량, 같으면 구매 SL이 적은 차량부터 고릅니다. 상위 랭크 연구 시 RP 감소는 포함하지 않습니다. 비공식 도구이며 Gaijin과 무관합니다.",
      source: "데이터:", updated: "갱신",
      army: "지상", aviation: "항공", helicopters: "헬기", ships: "대형 함선", boats: "소형 함선",
      usa: "미국", germany: "독일", ussr: "소련", britain: "영국", japan: "일본", china: "중국", italy: "이탈리아", france: "프랑스", sweden: "스웨덴", israel: "이스라엘",
    },
    en: {
      title: "War Thunder Research Calculator", country: "Nation", branch: "Branch", modeResearch: "Mark researched", modeTarget: "Pick target", modeBuy: "Mark bought", modeProgress: "Enter progress",
      avg: "Avg RP per battle", reset: "Reset this tree", langBtn: "한국어", howto: "How to use",
      fold: "▴ Collapse", openAll: "Expand all folders", closeAll: "Collapse all folders", units: " vehicles",
      hint: "Mark researched: click only the last researched vehicle in each line; it and earlier ones are marked researched and bought. Click again to unmark. Click premiums you own too. Mark bought: click researched vehicles you have not bought to mark them unbought (dashed). Rank unlocks count bought vehicles only. Pick target: click a vehicle to see remaining RP and SL. Enter progress: click a vehicle you are researching and type the RP already earned (shown when hovering it in game).",
      noTarget: "Pick a target vehicle.", done: "Researched", remainRP: "Remaining RP", battles: "Est. battles", targetSL: "Target purchase + crew SL",
      pathSL: "SL to buy whole path", steps: "Vehicles left", premium: "Premium",
      discount: "SL sale", noDiscount: "None", discounted: "sale applied",
      pathRP: "path", unlockRP: "rank unlock", unlockSL: "SL to buy for unlocks", buy: "buy", notBought: "not bought",
      legend: "Orange: path to target · Blue: research for rank unlock · 'buy': purchase needed to fill rank unlocks",
      short: "Ranks that cannot be filled even with the whole tree",
      note: "Rank unlocks count vehicles marked bought (owned) in this tree. Suggestions pick the fewest extra RP, then the lowest purchase SL. The RP penalty for higher-rank research is not included. Unofficial tool, not affiliated with Gaijin.",
      source: "Data:", updated: "updated",
      army: "Ground", aviation: "Aviation", helicopters: "Helicopters", ships: "Bluewater", boats: "Coastal",
      usa: "USA", germany: "Germany", ussr: "USSR", britain: "Britain", japan: "Japan", china: "China", italy: "Italy", france: "France", sweden: "Sweden", israel: "Israel",
    },
  };
  const D = window.WT_DATA, U = D.units;
  const children = {};
  for (const [id, u] of Object.entries(U)) if (u.req) (children[u.req] ||= []).push(id);

  const ROOT = document.getElementById("wtcalc");
  const $ = (id) => document.getElementById("wt-" + id);
  const saved = (() => { try { return JSON.parse(localStorage.getItem("wtcalc") || "{}"); } catch { return {}; } })();
  const S = {
    lang: saved.lang || (navigator.language.startsWith("ko") ? "ko" : "en"),
    country: saved.country || "country_usa", branch: saved.branch || "army",
    mode: "research", target: saved.target || null, avg: saved.avg || 1500, discount: saved.discount || 0,
    done: new Set(saved.done || []),
    // Older saves had no bought list: treat every researched vehicle as bought.
    bought: new Set(saved.bought || saved.done || []),
    progress: saved.progress || {}, editing: null,
    open: new Set(saved.open || []), // expanded folders; folders start collapsed like in game
  };
  function save() {
    try {
      localStorage.setItem("wtcalc", JSON.stringify({ ...S, mode: undefined, editing: undefined, done: [...S.done], bought: [...S.bought], open: [...S.open] }));
    } catch {}
  }

  const t = (k) => T[S.lang][k] ?? k;
  const fmt = (n) => n.toLocaleString(S.lang === "ko" ? "ko-KR" : "en-US");
  // In-game tree slot icons from the datamine, served by jsDelivr.
  const ICON = "https://cdn.jsdelivr.net/gh/gszabi99/War-Thunder-Datamine@master/atlases.vromfs.bin_u/units/";
  const ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"];

  function chain(id) { const out = []; while (id && U[id]) { out.push(id); id = U[id].req; } return out; }
  function unmark(id) { S.done.delete(id); S.bought.delete(id); for (const c of children[id] || []) unmark(c); }
  // Vehicle purchase price after the SL sale; crew training cost is not discounted.
  function price(id) { return Math.round((U[id].sl * (100 - S.discount)) / 100); }
  function left(id) { return Math.max(0, U[id].rp - (S.progress[id] || 0)); }
  function path() { return S.target ? chain(S.target).filter((id) => !S.done.has(id)) : []; }
  function treeIds() { return D.trees[S.country][S.branch].flat().flatMap((it) => it.ids || [it]); }
  function treeGroups() { return D.trees[S.country][S.branch].flat().filter((it) => it.ids).map((it) => it.group); }
  function needFor(r) { return (D.rankReq[S.country]?.[S.branch] || [])[r - 1] || 0; }

  // Path to target plus the cheapest extra vehicles that fill each rank's unlock count.
  // ponytail: greedy by chain RP, not a true minimum; fine for a planning estimate.
  // Rank unlocks count only bought vehicles, so each pick is a purchase (plus research if needed).
  function plan() {
    const p = path(), planned = new Set(p), extra = [], buys = [], short = [];
    if (!S.target) return { path: p, extra, buys, short };
    const ids = treeIds(), toBuy = new Set();
    const owned = (id) => S.bought.has(id) || toBuy.has(id);
    const count = (r) => ids.filter((id) => U[id].rank === r && owned(id)).length;
    const todo = (x) => !S.done.has(x) && !planned.has(x);
    for (let r = U[S.target].rank - 1; r >= 1; r--) {
      while (count(r) < needFor(r)) {
        let best = null, bestRP = Infinity, bestSL = Infinity;
        for (const id of ids) {
          if (U[id].rank !== r || U[id].premium || owned(id)) continue;
          const rp = chain(id).filter(todo).reduce((s, x) => s + left(x), 0), sl = U[id].sl;
          if (rp < bestRP || (rp === bestRP && sl < bestSL)) { best = id; bestRP = rp; bestSL = sl; }
        }
        if (!best) { short.push(r); break; }
        for (const x of chain(best).filter(todo)) { planned.add(x); extra.push(x); }
        toBuy.add(best); buys.push(best);
      }
    }
    return { path: p, extra, buys, short };
  }

  function click(id) {
    const u = U[id];
    if (u.premium && S.mode !== "research" && S.mode !== "buy") return;
    if (u.premium && S.done.has(id)) unmark(id);
    else if (u.premium) { S.done.add(id); S.bought.add(id); }
    else if (S.mode === "buy") { if (S.done.has(id)) S.bought.has(id) ? S.bought.delete(id) : S.bought.add(id); }
    else if (S.mode === "progress") { if (!S.done.has(id)) S.editing = id; }
    else if (S.mode === "target") S.target = S.target === id ? null : id;
    else if (S.done.has(id)) unmark(id);
    else chain(id).forEach((x) => { S.done.add(x); S.bought.add(x); });
    save(); render();
  }

  function card(id, onPath, onUnlock, onBuy) {
    const u = U[id], b = document.createElement("button");
    b.dataset.id = id;
    b.className = "card" + (u.premium ? " premium" : "") +
      (S.done.has(id) ? " done" + (S.bought.has(id) ? "" : " notbought") : onPath.has(id) ? " path" : onUnlock.has(id) ? " unlock" : "") + (S.target === id ? " target" : "");
    const got = !u.premium && !S.done.has(id) && S.progress[id];
    const tag = onBuy.has(id) ? ` · ${t("buy")}` : S.done.has(id) && !S.bought.has(id) ? ` · ${t("notBought")}` : "";
    b.innerHTML = `<img src="${ICON}${id.toLowerCase()}.png" alt="" loading="lazy" onerror="this.style.visibility='hidden'">` +
      `<span>${u[S.lang]}<small>${u.premium ? t("premium") : got ? `${fmt(got)} / ${fmt(u.rp)} RP` : fmt(u.rp) + " RP"}${tag}</small>` +
      (got ? `<i class="bar" style="width:${Math.min(100, (100 * got) / u.rp)}%"></i>` : "") + "</span>";
    b.title = `${u[S.lang]} · ${fmt(u.rp)} RP · ${fmt(price(id))} SL`;
    b.onclick = () => click(id);
    return b;
  }

  function folderCard(item, onPath, onUnlock) {
    const ids = item.ids, n = ids.length, done = ids.filter((id) => S.done.has(id)).length;
    const has = (set) => ids.some((id) => set.has(id));
    const b = document.createElement("button");
    b.dataset.ids = ids.join(" ");
    b.className = "card folderCard" + (ids.every((id) => U[id].premium) ? " premium" : "") +
      (done === n ? " done" : has(onPath) ? " path" : has(onUnlock) ? " unlock" : "") + (ids.includes(S.target) ? " target" : "");
    const fallback = `${ICON}${ids[0].toLowerCase()}.png`;
    b.innerHTML = `<img src="${ICON}${item.group.toLowerCase()}.png" alt="" loading="lazy" ` +
      `onerror="this.onerror=()=>this.style.visibility='hidden';this.src='${fallback}'">` +
      `<span>${D.groups[item.group][S.lang]}<small>▸ ${n}${t("units")} · ${done}/${n}</small></span>`;
    b.title = ids.map((id) => U[id][S.lang]).join(" / ");
    b.onclick = () => { S.open.add(item.group); save(); render(); };
    return b;
  }

  function renderTree() {
    const cols = D.trees[S.country][S.branch], P = plan(), onPath = new Set(P.path), onUnlock = new Set(P.extra), onBuy = new Set(P.buys);
    const rankOf = (item) => U[item.ids ? item.ids[0] : item].rank;
    const ranks = [...new Set(cols.flat().map(rankOf))].sort((a, b) => a - b);
    const grid = $("grid");
    grid.style.gridTemplateColumns = `44px repeat(${cols.length}, max-content)`;
    const ids = treeIds();
    grid.replaceChildren();
    for (const r of ranks) {
      const label = document.createElement("div");
      label.className = "rank"; label.textContent = ROMAN[r] || r;
      const need = needFor(r);
      if (need) {
        const have = ids.filter((id) => U[id].rank === r && S.bought.has(id)).length;
        label.insertAdjacentHTML("beforeend", `<small class="${have >= need ? "ok" : ""}">${Math.min(have, need)}/${need}</small>`);
      }
      grid.append(label);
      for (const col of cols) {
        const cell = document.createElement("div");
        cell.className = "cell";
        for (const item of col.filter((i) => rankOf(i) === r)) {
          if (!item.ids) { cell.append(card(item, onPath, onUnlock, onBuy)); continue; }
          if (!S.open.has(item.group)) { cell.append(folderCard(item, onPath, onUnlock)); continue; }
          const f = document.createElement("div");
          f.className = "folder";
          const fold = document.createElement("button");
          fold.className = "fold"; fold.textContent = t("fold");
          fold.onclick = () => { S.open.delete(item.group); save(); render(); };
          f.append(fold, ...item.ids.map((id) => card(id, onPath, onUnlock, onBuy)));
          cell.append(f);
        }
        grid.append(cell);
      }
    }
    drawArrows(grid, new Set(ids), new Set([...P.path, ...P.extra]));
  }

  // Prerequisite arrows like the in-game tree. Arrows leaving a folder start at the folder box;
  // arrows entering a folder's top vehicle from outside end at the folder box.
  function drawArrows(grid, inTree, planned) {
    const base = grid.getBoundingClientRect(), NS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(NS, "svg");
    svg.classList.add("arrows");
    svg.setAttribute("width", grid.scrollWidth);
    svg.setAttribute("height", grid.scrollHeight);
    // A vehicle inside a collapsed folder is drawn at the folder card.
    const el = (id) => grid.querySelector(`[data-id="${CSS.escape(id)}"]`) || grid.querySelector(`[data-ids~="${CSS.escape(id)}"]`);
    let html = "";
    for (const id of inTree) {
      const req = U[id].req;
      if (!req || U[id].premium || !inTree.has(req)) continue;
      let from = el(req), to = el(id);
      if (from === to) continue;
      const fromFolder = from.parentElement.closest(".folder"), toFolder = to.parentElement.closest(".folder");
      if (fromFolder && fromFolder !== toFolder) from = fromFolder;
      if (toFolder && toFolder !== fromFolder) to = toFolder;
      const a = from.getBoundingClientRect(), b = to.getBoundingClientRect();
      const x1 = a.left + a.width / 2 - base.left, y1 = a.bottom - base.top;
      const x2 = b.left + b.width / 2 - base.left, y2 = b.top - base.top;
      const ym = y2 - 7;
      const d = Math.abs(x1 - x2) < 1 ? `M${x1} ${y1}V${y2 - 5}` : `M${x1} ${y1}V${ym}H${x2}V${y2 - 5}`;
      const cls = S.done.has(id) && S.done.has(req) ? "done" : planned.has(id) ? "path" : "";
      html += `<g class="${cls}"><path d="${d}"/><polygon points="${x2 - 4},${y2 - 6} ${x2 + 4},${y2 - 6} ${x2},${y2}"/></g>`;
    }
    svg.innerHTML = html;
    grid.prepend(svg);
  }

  function renderSummary() {
    const el = $("summary");
    if (!S.target) { el.textContent = t("noTarget"); return; }
    const u = U[S.target], { path: p, extra, buys, short } = plan();
    const sum = (list) => list.reduce((s, id) => s + left(id), 0);
    const pathRP = sum(p), unlockRP = sum(extra), rp = pathRP + unlockRP;
    const pathSL = p.reduce((s, id) => s + price(id), 0);
    el.innerHTML = `<b>${u[S.lang]}</b>` + (p.length === 0
      ? ` · ${t("done")}`
      : ` · ${t("remainRP")}: <b>${fmt(rp)}</b>` + (unlockRP ? ` (${t("pathRP")} ${fmt(pathRP)} + ${t("unlockRP")} ${fmt(unlockRP)})` : "") +
        ` · ${t("battles")}: <b>${fmt(Math.ceil(rp / Math.max(1, S.avg)))}</b>` +
        ` · ${t("steps")}: ${p.length + extra.length} · ${t("targetSL")}: ${fmt(price(S.target) + u.train)} · ${t("pathSL")}: ${fmt(pathSL)}` +
        (buys.length ? ` · ${t("unlockSL")}: ${fmt(buys.reduce((s, id) => s + price(id), 0))} (${buys.length})` : "") +
        (S.discount ? ` · ${t("discounted")} -${S.discount}%` : "") +
        (short.length ? ` · ${t("short")}: ${short.map((r) => ROMAN[r]).join(", ")}` : "") +
        `<div class="hint">${t("legend")}</div>`);
  }

  function fillSelect(sel, keys, value) {
    sel.replaceChildren(...keys.map((k) => new Option(t(k.replace("country_", "")), k)));
    sel.value = keys.includes(value) ? value : keys[0];
    return sel.value;
  }

  function render() {
    ROOT.lang = S.lang;
    ROOT.querySelectorAll("[data-t]").forEach((e) => (e.textContent = t(e.dataset.t)));
    $("lang").textContent = t("langBtn");
    const groups = treeGroups();
    $("folders").hidden = !groups.length;
    $("folders").textContent = t(groups.every((g) => S.open.has(g)) ? "closeAll" : "openAll");
    $("modeResearch").setAttribute("aria-pressed", S.mode === "research");
    $("modeTarget").setAttribute("aria-pressed", S.mode === "target");
    $("modeProgress").setAttribute("aria-pressed", S.mode === "progress");
    $("modeBuy").setAttribute("aria-pressed", S.mode === "buy");
    $("progressEditor").hidden = !(S.mode === "progress" && S.editing);
    if (S.editing) {
      $("progressName").textContent = U[S.editing][S.lang];
      $("progress").max = U[S.editing].rp;
      $("progress").value = S.progress[S.editing] || "";
      $("progressMax").textContent = `/ ${fmt(U[S.editing].rp)} RP`;
    }
    S.country = fillSelect($("country"), Object.keys(D.trees), S.country);
    S.branch = fillSelect($("branch"), Object.keys(D.trees[S.country]).filter((b) => D.trees[S.country][b].length), S.branch);
    $("avg").value = S.avg;
    $("discount").value = S.discount;
    $("updated").textContent = `${t("updated")} ${D.updated}`;
    renderSummary(); renderTree();
  }

  $("country").onchange = (e) => { S.country = e.target.value; save(); render(); };
  $("branch").onchange = (e) => { S.branch = e.target.value; save(); render(); };
  $("modeResearch").onclick = () => { S.mode = "research"; render(); };
  $("modeTarget").onclick = () => { S.mode = "target"; render(); };
  $("modeProgress").onclick = () => { S.mode = "progress"; render(); };
  $("modeBuy").onclick = () => { S.mode = "buy"; render(); };
  $("progress").oninput = (e) => {
    const v = Math.min(U[S.editing].rp, Math.max(0, Number(e.target.value) || 0));
    if (v) S.progress[S.editing] = v; else delete S.progress[S.editing];
    save(); renderSummary(); renderTree();
  };
  $("avg").oninput = (e) => { S.avg = Number(e.target.value) || 1; save(); renderSummary(); };
  $("discount").onchange = (e) => { S.discount = Number(e.target.value); save(); renderSummary(); renderTree(); };
  $("lang").onclick = () => { S.lang = S.lang === "ko" ? "en" : "ko"; save(); render(); };
  $("folders").onclick = () => {
    const groups = treeGroups(), close = groups.every((g) => S.open.has(g));
    groups.forEach((g) => (close ? S.open.delete(g) : S.open.add(g)));
    save(); render();
  };
  $("reset").onclick = () => {
    treeIds().forEach((id) => { S.done.delete(id); S.bought.delete(id); delete S.progress[id]; });
    save(); render();
  };
  render();

  // Test hook for test_calc.py; the app itself keeps everything inside this function.
  window.WTCALC = { S, U, D, $, click, plan, render, treeIds, left, price };
})();
