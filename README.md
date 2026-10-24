# clawd-mv-macos

> A macOS-friendly fork of [YojenWang/clawd-mv](https://github.com/YojenWang/clawd-mv) —
> a skill that turns a song into a hand-drawn (p5.brush / watercolor) animated MV.

Upstream is Windows-only: `scripts/render.py` hard-codes an Edge path and forces
`--use-angle=d3d11`. This fork makes the same renderer run on macOS (Apple Silicon and
Intel), Linux, and Windows, and folds in the fixes and gotchas collected while producing
a real 3-minute MV with it.

---

## What you get

`render.py` drives a headless Chrome/Chromium/Edge over the DevTools protocol, loads the
animation project's `studio.html?render`, and then:

| Mode | What it does |
|---|---|
| `--stills=1.2,3.4` | PNG stills at given seconds — the fastest way to judge a shot |
| `--sheet=0.5,1,1.5 --cols=4` | contact sheet of many moments in one image |
| `--strip=2.0:2.5 --cols=6` | strip of consecutive moments inside a time window (motion check) |
| `--frames --fps=24 --workers=1` | full frame sequence `out/frames/f%05d.jpg`, resumable |
| `--encode --audio=song.mp3` | mux frames + audio into `out/video.mp4` with ffmpeg |

All animation code stays in the project (`src/core.js`, `src/clawd.js`, `src/world.js`,
`src/scenes/*.js`); this skill only renders and encodes.

## Requirements

- Python 3.9+
- `pip install websocket-client imageio-ffmpeg` (ffmpeg comes bundled with the latter)
- Chrome, Chromium, Edge or Brave installed (auto-detected; override with `--browser=`)
- Node.js only if you rebuild the animation project (`npm install` in the project)

## Quick start

```bash
# 1. get an animation project (upstream base repo)
git clone https://github.com/JohnHeibel/ClaudeAnimationBase my-mv
cd my-mv && npm install

# 2. this skill: either drop the script in the project root…
cp /path/to/clawd-mv-macos/scripts/render.py .

# 3. …or keep it outside and point at the project
python /path/to/clawd-mv-macos/scripts/render.py --project=/path/to/my-mv --stills=3.5

# 4. look at a shot, then render everything
python render.py --sheet=12.5,22,33.5 --cols=3 --w=560 --out=out/check.jpg
python render.py --frames --fps=24 --workers=1 --out=out/frames
python render.py --encode --audio=assets/song.mp3 --out=out/video.mp4
```

`render.py` finds the project by looking for `studio.html` next to itself, then in the
current directory, then one level up. Pass `--project=DIR` to be explicit.

## Changes vs upstream

| Upstream | This fork | Why |
|---|---|---|
| `EDGE = "C:\\Program Files…msedge.exe"` | `find_browser()` probes Chrome / Chromium / Edge / Brave on macOS, Linux, Windows | upstream dies with `FileNotFoundError` off Windows |
| `--use-angle=d3d11` | removed | d3d11 is Windows-only; Chrome picks Metal/GL itself |
| no `--no-sandbox` | added | needed for headless Chrome in sandboxes/CI (macOS included) |
| `webdriver`-free but Edge-only CDP | same CDP flow, browser-agnostic | — |
| fixed paths from `__file__` | `--project` + auto-detection of `studio.html` | lets the script live outside the project |
| hard-coded `ws://…:9222` | `--port` (default 9333) | avoids clashing with other debuggers |
| no failure guidance | `SKILL.md` pitfall table + resumable frame loop | crashes are the norm, not the exception |

## Known pitfalls (learned the hard way)

1. **`window.ready never became true`** — the studio page did not finish `setup()`.
   Usually a wrong project root (no `studio.html`), a syntax error in the scene file, or
   a WebGL context failure. Open the page in a normal browser and check the console first.
2. **`ConnectionResetError: [Errno 54]`** — the headless tab died after a few hundred
   frames. Use `--workers=1` and wrap the call in a resume loop: frames already on disk are
   skipped, so re-running continues where it stopped.
3. **Flat color blocks instead of watercolor** — `brush.wash(color, 255)` fills opaquely and
   hides the paper texture. 235–240 keeps some life; below ~190 you start seeing the
   polygon fill as a translucent slab (especially with big background shapes).
4. **Thin stray lines along big fills** — p5.brush strokes the fill boundary
   (`fillTexture(texture, borderStrength)`). Keep `borderStrength` low (~0.1) or wide
   background polygons will show hairline edges.
5. **Verticals seams on mountains** — a mountain polygon closed at the ridge ends leaves
   vertical edges inside the frame. Extend the ridge line past the frame edges before closing.
6. **`FASTFILL` is not in this p5.brush build.** The upstream `SKILL.md` mentions it; grep the
   vendored `p5.brush` and it is absent. Renders land around 130 ms/frame at 1080p on an M5
   anyway, so nothing is lost.
7. **`yuvj420p(pc)` in ffprobe** — h264 gets the full-range flag; a few players show it
   slightly contrasty. Add `-color_range tv` if that matters to you.

## Credit

Original skill and the p5.brush animation studio belong to
[YojenWang/clawd-mv](https://github.com/YojenWang/clawd-mv) and
[JohnHeibel/ClaudeAnimationBase](https://github.com/JohnHeibel/ClaudeAnimationBase).
Code stays MIT; see `LICENSE`.
