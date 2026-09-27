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
- `build_embed.py`: writes a snippet for embedding the calculator in a blog post
- `test_calc.py`: regression test in headless Chrome (`python3 test_calc.py`)

## Data

Vehicle data and images come from [gszabi99/War-Thunder-Datamine](https://github.com/gszabi99/War-Thunder-Datamine). This is an unofficial fan tool, not affiliated with Gaijin Entertainment. Vehicle names, images and data belong to Gaijin Entertainment.
