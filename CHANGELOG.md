# Changelog

## 1.0.0 — macOS port

First public fork of [clawd-mv](https://github.com/YojenWang/clawd-mv).

### Fixed
- **Hard-coded Edge path** replaced by `find_browser()`: probes Chrome, Chromium, Edge and
  Brave on macOS / Linux / Windows; `--browser=` overrides.
- **`--use-angle=d3d11`** removed — Windows-only flag that broke Metal/GL contexts.
- **`--no-sandbox`** added to the launch flags (required for headless Chrome in sandboxes).
- **BOM** at the top of `render.py` stripped (it broke `python` on some shells).

### Added
- `--port` for the DevTools endpoint (default 9333) so several projects can coexist.
- `--project DIR` plus automatic discovery of `studio.html` (next to the script, then CWD,
  then parent) — the renderer no longer has to live inside the animation project.
- `--workers 1` documented as the stable default, with a resume loop in `SKILL.md`.
- `SKILL.md`: shot-density rules, the verify-with-sheets workflow, a rendering failure
  table, and the p5.brush notes (wash opacity, fill border hairlines, ridge seams,
  camera argument type, shot-local time for walkers).
- `examples/` stills.

### Known upstream issue, not fixed
- `FASTFILL` mentioned in the original `SKILL.md` does not exist in the vendored
  `p5.brush` build; 1080p renders run at ~130 ms/frame on an Apple M5 without it.
