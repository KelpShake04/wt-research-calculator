# War Thunder Research Calculator

Shows how much RP and how many Silver Lions you still need for a target vehicle, on a tree that looks like the in-game research screen. It covers all nations and branches, rank unlock requirements, folders and Silver Lion sales.

워썬더 목표 차량까지 남은 RP·판 수·실버 라이온을 계산하는 도구입니다.

## Use

Open `index.html` in a browser (keep `app.js` and `data.js` next to it). Nothing is sent to a server; progress is saved in the browser.

## Files

- `index.html`: markup and styles, all scoped to `#wtcalc`
- `app.js`: calculator logic
- `data.js`: vehicle data, built by `build_data.py`
- `build_data.py`: rebuilds `data.js` from the community datamine (`python3 build_data.py`)
- `embed.js`: generated from `index.html` by `build_embed.py`; puts the calculator into a blog post
- `build_embed.py`: rebuilds `embed.js` (`python3 build_embed.py`)
- `test_calc.py`: regression test in headless Chrome (`python3 test_calc.py`)

## Embed in a blog post

Paste into the post's HTML view:

```html
<div id="wtcalc"></div>
<script src="https://cdn.jsdelivr.net/gh/KelpShake04/wt-research-calculator@1/embed.js"></script>
```

`@1` follows the newest `v1.x.y` tag, so the post never needs editing after a release.

## Release

```sh
python3 build_embed.py        # after any change to index.html
python3 test_calc.py
git commit -am "..." && git push
git tag v1.x.y && git push origin v1.x.y
# optional, skips jsDelivr's cache (up to 12 hours):
for f in embed.js app.js data.js; do curl -s https://purge.jsdelivr.net/gh/KelpShake04/wt-research-calculator@1/$f; done
```

## Data

Vehicle data and images come from [gszabi99/War-Thunder-Datamine](https://github.com/gszabi99/War-Thunder-Datamine). This is an unofficial fan tool, not affiliated with Gaijin Entertainment. Vehicle names, images and data belong to Gaijin Entertainment.
