"""Regression test for the research calculator.

Run: python3 test_calc.py
Opens the calculator in headless Chrome (network blocked) twice: as index.html, and through embed.js
the way a Blogger post loads it, inside a deliberately hostile fake blog theme. Both runs
execute JS_CHECKS and compare the calculator's numbers with the reference implementation below.
Set CHROME=/path/to/chrome to override the browser.
"""
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


def load_data():
    with open(os.path.join(HERE, "data.js"), encoding="utf-8") as f:
        s = f.read()
    return json.loads(s[s.index("{"): s.rindex("}") + 1])


D = load_data()
U = D["units"]


def tree_ids(country, branch):
    return [i for col in D["trees"][country][branch] for it in col for i in (it["ids"] if isinstance(it, dict) else [it])]


def chain(i):
    out = []
    while i and i in U:
        out.append(i)
        i = U[i]["req"]
    return out


def price(i, discount):
    return (U[i]["sl"] * (100 - discount) + 50) // 100


def reference_plan(country, branch, target, done, bought, progress=None, discount=0):
    """Same greedy as plan() in index.html, written independently."""
    progress = progress or {}
    left = lambda i: max(0, U[i]["rp"] - progress.get(i, 0))
    ids = tree_ids(country, branch)
    need = D["rankReq"].get(country, {}).get(branch, [])
    path = [i for i in chain(target) if i not in done]
    planned, extra, buys = set(path), [], []
    todo = lambda x: x not in done and x not in planned
    owned = lambda i: i in bought or i in buys
    for r in range(U[target]["rank"] - 1, 0, -1):
        n = need[r - 1] if r - 1 < len(need) else 0
        while sum(1 for i in ids if U[i]["rank"] == r and owned(i)) < n:
            best, best_rp, best_sl = None, float("inf"), float("inf")
            for i in ids:
                if U[i]["rank"] != r or U[i]["premium"] or owned(i):
                    continue
                rp, sl = sum(left(x) for x in chain(i) if todo(x)), U[i]["sl"]
                if rp < best_rp or (rp == best_rp and sl < best_sl):
                    best, best_rp, best_sl = i, rp, sl
            if not best:
                break
            for x in [x for x in chain(best) if todo(x)]:
                planned.add(x)
                extra.append(x)
            buys.append(best)
    return {
        "path": sum(left(i) for i in path),
        "unlock": sum(left(i) for i in extra),
        "buySL": sum(price(i, discount) for i in buys),
        "pathSL": sum(price(i, discount) for i in path),
        "targetSL": price(target, discount) + U[target]["train"],
    }


def check_data():
    problems = []
    for country, branches in D["trees"].items():
        for branch in branches:
            ids = set(tree_ids(country, branch))
            for i in ids:
                r = U[i]["req"]
                if r and (r not in ids or U[r]["premium"] or U[r]["rank"] > U[i]["rank"]):
                    problems.append(f"{country} {branch} {i} <- {r}")
    return problems


JS_CHECKS = r"""
<script>
const R = { errors: [], sweeps: {}, scenarios: {}, checks: {} };
// Filled from window.WTCALC once the app has loaded (embed.js loads it asynchronously).
// Not named $: a host page may already own that global (the fake blog theme does).
let S, U, D, click, plan, render, treeIds, left, price, wt$;
const reset = () => { S.done = new Set(); S.bought = new Set(); S.progress = {}; S.target = null; S.discount = 0; S.open = new Set(); S.mode = "research"; };
const snap = () => {
  const P = plan(), sum = (l) => l.reduce((s, id) => s + left(id), 0);
  return { path: sum(P.path), unlock: sum(P.extra), buySL: P.buys.reduce((s, id) => s + price(id), 0),
           pathSL: P.path.reduce((s, id) => s + price(id), 0), targetSL: price(S.target) + U[S.target].train };
};
function sweep(label) {
  let cards = 0, arrows = 0, expected = 0, kinks = 0;
  for (const c of Object.keys(D.trees)) for (const b of Object.keys(D.trees[c])) {
    if (!D.trees[c][b].length) continue;
    S.country = c; S.branch = b;
    try {
      render();
      const ids = new Set(treeIds()), anchor = {};
      for (const it of D.trees[c][b].flat()) for (const id of it.ids || [it]) anchor[id] = it.ids && !S.open.has(it.group) ? it.group : id;
      expected += [...ids].filter((id) => U[id].req && !U[id].premium && ids.has(U[id].req) && anchor[id] !== anchor[U[id].req]).length;
      arrows += document.querySelectorAll(".arrows g").length;
      cards += document.querySelectorAll(".card").length;
      for (const p of document.querySelectorAll(".arrows path")) {
        const m = p.getAttribute("d").match(/^M([\d.]+) [\d.]+V[\d.]+H([\d.]+)/);
        if (m && Math.abs(m[1] - m[2]) < 12) kinks++;
        if (p.getAttribute("d").includes("NaN")) R.errors.push(`NaN arrow ${c} ${b}`);
      }
    } catch (e) { R.errors.push(`${label} ${c} ${b}: ${e}`); }
  }
  R.sweeps[label] = { cards, arrows, expected, kinks };
}
function runChecks() {
  ({ S, U, D, click, plan, render, treeIds, left, price } = window.WTCALC);
  wt$ = window.WTCALC.$;
try {
  reset(); sweep("collapsed");
  S.open = new Set(Object.keys(D.groups)); sweep("expanded");

  reset(); S.country = "country_usa"; S.branch = "army"; render();
  S.target = "us_m1128_mgs"; R.scenarios.fresh = snap();

  reset(); ["us_m24_chaffee", "us_m18_hellcat", "us_m3a1_stuart"].forEach(click);
  S.mode = "buy"; click("us_m24_chaffee"); click("us_m18_hellcat");
  S.target = "us_m41_walker_bulldog"; R.scenarios.unbought = snap();

  reset(); click("us_m24_chaffee"); S.mode = "target"; click("us_m1128_mgs");
  S.mode = "progress"; click("us_m41_walker_bulldog");
  wt$("progress").value = "999999"; wt$("progress").dispatchEvent(new Event("input"));
  R.checks.progressClamped = S.progress.us_m41_walker_bulldog === U.us_m41_walker_bulldog.rp;
  wt$("progress").value = "10000"; wt$("progress").dispatchEvent(new Event("input"));
  R.scenarios.progress = snap();
  wt$("discount").value = "50"; wt$("discount").dispatchEvent(new Event("change"));
  R.scenarios.discount50 = snap();

  reset(); render(); click("us_m4a1_76w_sherman");
  R.checks.folderChain = [...S.done].sort().join(",") === "us_m3_lee,us_m4a1_1942_sherman,us_m4a1_76w_sherman";
  click("us_m4a1_1942_sherman");
  R.checks.unmarkDescendants = !S.done.has("us_m4a1_76w_sherman") && !S.bought.has("us_m4a1_76w_sherman");
  S.mode = "buy"; click("us_lvt_a_4");
  R.checks.premiumOwned = S.done.has("us_lvt_a_4") && S.bought.has("us_lvt_a_4");
  S.mode = "target"; click("us_lvt_a_4");
  R.checks.premiumNotTarget = S.target !== "us_lvt_a_4";
  reset(); render();
  document.querySelector('[data-ids~="us_m4a1_1942_sherman"]').click();
  R.checks.folderOpens = S.open.has("us_sherman_group") && !!document.querySelector(".folder .fold");
  document.querySelector(".folder .fold").click();
  R.checks.folderCloses = !S.open.has("us_sherman_group");
  R.checks.editorHiddenOutsideProgress = getComputedStyle(wt$("progressEditor")).display === "none";
} catch (e) { R.errors.push("scenario: " + e); }
}
</script>
"""

# Extra checks for the embedded copy: the host page's globals, lang and styles must not leak either way.
BLOG_CHECKS = r"""
<script>
function blogChecks() {
try {
  R.checks.themeDollarIntact = window.__themeDollar === true && window.$() === "theme-jquery";
  R.checks.themeIdIntact = document.getElementById("summary").textContent === "theme summary";
  reset(); render(); wt$("lang").click();
  R.checks.hostLangIntact = document.documentElement.lang === "en" && document.getElementById("wtcalc").lang !== "";
  const card = document.querySelector("#wtcalc .card"), img = card.querySelector("img");
  R.checks.cardStyleIntact = getComputedStyle(card).width === "176px" && getComputedStyle(card).marginTop === "0px";
  R.checks.imgStyleIntact = getComputedStyle(img).paddingTop === "0px" && getComputedStyle(img).borderTopWidth === "0px";
  R.checks.headingStyleIntact = getComputedStyle(document.querySelector("#wtcalc h1")).textTransform === "none";
  R.checks.summaryVisible = getComputedStyle(document.querySelector("#wtcalc .summary")).display === "flex";
} catch (e) { R.errors.push("blog: " + e); }
}
</script>
"""

JS_REPORT = r"""
<script>
(function wait(n) {
  if (!window.WTCALC && n < 200) return setTimeout(() => wait(n + 1), 50);
  if (!window.WTCALC) R.errors.push("app did not load");
  else { runChecks(); if (typeof blogChecks === "function") blogChecks(); }
  document.body.insertAdjacentHTML("beforeend", "<pre id=testout>" + JSON.stringify(R).replace(/</g, "\\u003c") + "</pre>");
})(0);
</script>
"""

HOSTILE_BLOG = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  * { margin: 0; padding: 0; }
  body { font: 18px/1.8 Georgia, serif; color: #333; background: #fafafa; }
  .post-body { max-width: 720px; margin: 0 auto; }
  .post-body img { padding: 6px; border: 3px solid red; box-shadow: 0 0 8px #000; max-width: 100%; height: auto; }
  h1 { font: 40px Georgia, serif; text-transform: uppercase; color: red; }
  button, select, input { width: 100%; text-transform: uppercase; letter-spacing: 3px; padding: 14px; margin: 6px 0; }
  .card { margin: 20px; } .grid { grid-template-columns: 1fr 1fr; } .summary { display: none; } .hint { font-size: 30px; }
</style>
<script>var $ = function () { return "theme-jquery"; };</script>
</head><body>
<div id="summary">theme summary</div>
<div class="post-body">SNIPPET</div>
<script>window.__themeDollar = typeof $ === "function" && $() === "theme-jquery";</script>
</body></html>
"""


def run_browser(page):
    tmp = tempfile.mkdtemp(prefix="wtcalc-test-")
    try:
        for name in ("data.js", "app.js", "embed.js"):
            shutil.copy(os.path.join(HERE, name), tmp)
        with open(os.path.join(tmp, "index.html"), "w", encoding="utf-8") as f:
            f.write(page)
        cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
               f"--user-data-dir={tmp}/profile", "--host-resolver-rules=MAP * ~NOTFOUND",
               "--allow-file-access-from-files", "--virtual-time-budget=15000", "--dump-dom",
               f"file://{tmp}/index.html"]
        # Chrome sometimes keeps running after --dump-dom has printed the page, so poll the
        # output file and stop Chrome once the result is there.
        out_path = os.path.join(tmp, "dom.html")
        with open(out_path, "w") as out:
            proc = subprocess.Popen(cmd, stdout=out, stderr=subprocess.DEVNULL)
            deadline = time.time() + 180
            dom = ""
            while time.time() < deadline:
                with open(out_path, encoding="utf-8", errors="replace") as f:
                    dom = f.read()
                if "</html>" in dom or proc.poll() is not None:
                    break
                time.sleep(0.5)
            proc.kill()
            proc.wait()
        with open(out_path, encoding="utf-8", errors="replace") as f:
            dom = f.read()
        m = re.search(r'<pre id="testout">(.*?)</pre>', dom, re.S)
        if not m:
            sys.exit("FAIL: no test output from Chrome")
        return json.loads(html.unescape(m.group(1)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def pages():
    with open(os.path.join(HERE, "index.html"), encoding="utf-8") as f:
        index = f.read().replace("</body>", JS_CHECKS + JS_REPORT + "</body>")
    sys.path.insert(0, HERE)
    from build_embed import post_snippet
    blog = HOSTILE_BLOG.replace("SNIPPET", post_snippet(".")).replace("</body>", JS_CHECKS + BLOG_CHECKS + JS_REPORT + "</body>")
    return {"index.html": index, "blogger embed": blog}


def check_browser(label, R, expected):
    failures = [f"{e}" for e in R["errors"]]
    for sweep, s in R["sweeps"].items():
        if s["arrows"] != s["expected"] or s["kinks"]:
            failures.append(f"arrows {sweep}: {s}")
    if R["sweeps"].get("expanded", {}).get("cards") != len(U):
        failures.append(f"expanded cards {R['sweeps'].get('expanded')} != {len(U)} vehicles")
    for name, ok in R["checks"].items():
        if not ok:
            failures.append(f"check {name}")
    for name, want in expected.items():
        got = R["scenarios"].get(name)
        if got != want:
            failures.append(f"scenario {name}: browser {got} != reference {want}")
    for label_, s in R["sweeps"].items():
        print(f"  sweep {label_}: {s}")
    print(f"  {len(R['scenarios'])} scenarios, {len(R['checks'])} checks")
    return [f"{label}: {f}" for f in failures]


def main():
    failures = [f"data: {p}" for p in check_data()]
    sys.path.insert(0, HERE)
    from build_embed import embed_js
    with open(os.path.join(HERE, "embed.js"), encoding="utf-8") as f:
        if f.read() != embed_js():
            failures.append("embed.js is stale: run python3 build_embed.py")
    m24 = set(chain("us_m24_chaffee"))
    unb = m24 | set(chain("us_m18_hellcat")) | set(chain("us_m3a1_stuart"))
    expected = {
        "fresh": reference_plan("country_usa", "army", "us_m1128_mgs", set(), set()),
        "unbought": reference_plan("country_usa", "army", "us_m41_walker_bulldog", unb, unb - {"us_m24_chaffee", "us_m18_hellcat"}),
        "progress": reference_plan("country_usa", "army", "us_m1128_mgs", m24, m24, {"us_m41_walker_bulldog": 10000}),
        "discount50": reference_plan("country_usa", "army", "us_m1128_mgs", m24, m24, {"us_m41_walker_bulldog": 10000}, 50),
    }
    for name, want in expected.items():
        print(f"reference {name}: {want}")
    for label, page in pages().items():
        print(label)
        failures += check_browser(label, run_browser(page), expected)
    if failures:
        print("\nFAIL")
        print("\n".join(failures))
        sys.exit(1)
    print("\nOK")


if __name__ == "__main__":
    main()
