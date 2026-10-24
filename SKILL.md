---
name: clawd-mv-macos
description: Turn a song into a hand-drawn (p5.brush watercolor) animated MV — plan shots on the lyric timeline, animate a clawd character, render 1080p frames headlessly on macOS/Linux/Windows, and mux with the audio.
---

# clawd-mv (macOS edition)

Use this skill when someone gives you a song (mp3/wav + optional lyrics) and wants an
animated MV, a lyric video with real drawings, or a canvas-animation short.

You do **not** write a video editing project. You write JavaScript frames: every scene is
a pure function of time `f(t)`, so any frame can be rendered in any order, in parallel, or
twice. That property is what makes long renders survivable.

## 1. Layout

```
my-mv/                     ← animation project (ClaudeAnimationBase fork)
  studio.html              ← the "studio": loads engine + scenes, exposes window.ready
  src/core.js              ← paint / inkLine / camera / letters / timing helpers
  src/clawd.js             ← the character: body, face, emotions, poses
  src/world.js             ← reusable scenery: sky, ridge, ground, clouds, props
  src/scenes/<song>.js     ← YOUR WORK: shot list, each shot a pure function of t
  src/lyrics.js            ← generated: [{t:[start,end], s:'line'}, …]
  render.py                ← from this skill
  out/                     ← frames, stills, sheets, final mp4
```

## 2. Pipeline

1. **Probe the song.** duration, sample rate, first downbeat. Set
   `PROJECT = {duration, bpm, offset}` in `src/config.js`.
2. **Parse the lyrics.** If a `.yrc` (or `.lrc`) file exists, parse it — do not guess
   timings by ear. Skip credit lines (arranger / mixing / mastering) and keep the singing
   lines only. Write `src/lyrics.js` with `CREDITS`, `LYRICS`, `lineAt(t)`.
3. **Design the world** before the shots: sky palette, ridge colours, ground, and 8–12
   reusable props. Reuse beats novelty: the same mountain must return in the last chorus.
4. **Storyboard on anchors.** Every lyric line start is a cut candidate. Group lines into
   beats (a beat = 2–12 s) and give each beat exactly one idea: *want → obstacle →
   consequence*. Write the shot list as data first, then implement.
5. **Implement shot functions** in one file, in time order, each wrapped by the local
   `sl()` helper that handles the camera and the subtitle.
6. **Verify visually, three ways** before rendering anything long:
   `--stills` for a single frame, `--sheet` for a section, `--strip` for motion inside one
   shot. Never trust "it compiles" — trust pixels.
7. **Render frames**, then **encode** with the audio.

## 3. Rules that keep it from looking cheap

- **One idea per shot.** If you cannot say what changed between the first and last frame,
  the shot is a wallpaper.
- **Density**: 5–7 shots per 10 s in intro/outro, 8–10 in verses, 6–8 in the chorus,
  5–7 in instrumental breaks. Long gaps are where amateurs appear.
- **Four layers of motion** in every shot: background (clouds drift), midground (a prop
  that reacts), character (a pose or emotion change), camera (push, pan, or none — pick one).
- **Emotions do the talking.** Use the character's faces (determined / tired / confused /
  surprised / proud / dizzy / hopeful) instead of explanatory text.
- **Subtitles carry the song, nothing else.** One line, bottom centre, hand-lettered look.
  No dialogue boxes, no narration cards.
- **Repeat with variation**: the chorus returns, so return its shots with a different
  camera and a different time of day. That reads as choreography, not laziness.
- **Composition**: characters belong between 1/4 and 3/4 of the frame height. Empty upper
  sky is fine; an empty lower half usually is not.

## 4. Rendering and the failure table

```bash
python render.py --stills=12.5,22 --out=out/check
python render.py --sheet=35.5,37.5,47.5 --cols=3 --w=520 --out=out/sheet.jpg
python render.py --strip=148.1:150.8 --cols=8 --w=320 --out=out/strip.jpg
python render.py --frames --fps=24 --workers=1 --out=out/frames
python render.py --encode --audio=assets/song.mp3 --out=out/video.mp4
```

| Symptom | Cause | Fix |
|---|---|---|
| `browser not found` | no Chrome/Chromium/Edge | install one, or `--browser=/path/to/chrome` |
| `studio.html not found` | wrong working dir | `--project=/path/to/project` |
| `window.ready never became true` | JS error in setup, or WebGL dead | open `studio.html` headed, read console |
| `ConnectionResetError` / tab died mid-render | one tab per worker, long renders | `--workers=1`, re-run: existing frames are skipped |
| every frame identical | scene ignores `t` | your shot function is not a function of time |
| offsets off by a second | `--fps` mismatch between `--frames` and `--encode` | same fps both times |
| frames render but video is silent | no `--audio` | `--encode --audio=…` |
| video longer than audio | `-shortest` trims audio | expected; add frames if the tail matters |

**Resume loop** for a 3000+ frame render (crashes are normal):

```bash
for i in $(seq 1 15); do
  python render.py --frames --fps=24 --workers=1 --out=out/frames
  n=$(ls out/frames/*.jpg 2>/dev/null | wc -l)
  echo "pass $i -> $n"
  [ "$n" -ge "$TOTAL" ] && break
done
```

## 5. Engine notes (p5.brush)

- `paint(points, {wash, fill, ink, …})` is the local wrapper: wash = flat color layer,
  fill = watercolor body, ink = tapered outline. Keep `washOpacity ≈ 238`,
  `fillOpacity ≈ 135`, `fillTexture(0.4, borderStrength ≈ 0.1)`.
- Always close polygons that leave the frame, and extend ridge lines past the edges —
  otherwise the translucent fill shows its own boundary as a seam.
- `camBegin(cx, cy, zoom, rot)` maps a world point to screen centre; **pass four numbers,
  not an array**. Letters queued while a camera is active go through it automatically.
- `stroll(t, t0, t1, x0, x1, u)` returns `{x, walk, view, flip, dy}`; pass *shot-local*
  time (`lt`), never absolute song time, or the walker starts and ends off-screen.
- Randomness must be seeded per shot (`boilSeed`) or the watercolor edges will crawl
  between frames.

## 6. Deliverables checklist

- [ ] `out/video.mp4` — h264 + aac, 1080p, fps matches the frame render
- [ ] `STORYBOARD.md` — section table, shot counts, anchor timestamps, known limitations
- [ ] `src/lyrics.js` — generated, reproducible from the source lyric file
- [ ] frames kept (or at least a contact sheet) so shots can be re-rendered individually

Be honest in the storyboard: list the shots you know are weak, and why. The next person
opening the project will find them anyway.
