# Image → Particle Collage

[中文](README.md) | **English**

Turn one master image into a collage of thousands of small photos: every particle becomes an asset image, and the brightness of the master image drives the brightness of each tile. The camera can fly out from inside the photo cloud while the tiles assemble into the full image. Export supports 4K, portrait/square, and transparent PNG frame sequences.

**Live demo**: <https://afeiisfine.github.io/particle-collage/>  
**Offline single-file**: [Releases](https://github.com/AfeiIsFine/particle-collage/releases/latest)  
(download the ZIP, unzip, and double-click `index.html` — no local server needed)

![Particle Collage — default scene](screenshot.png)

> **A note from the author**: I'm **阿飞这个名字挺好的** (["AfeiIsFine"](https://github.com/AfeiIsFine)).
> I don't know how to program. Every line of code, every feature — and this document — was written by AI.
> Please forgive any amateurish mistakes, and feel free to open an Issue if you spot one.
>
> **For English readers**: the app UI has a built-in Chinese/English switch; code comments are in Chinese. This README is a full translation of the Chinese one.

---

## What it is

- **The master image defines the form**: drop in an image and it is sampled into particles by pixel luminance. Dark and transparent pixels spawn no tiles, so portraits and silhouettes naturally become cut-outs.
- **The asset folder defines the texture**: upload a folder (subfolders included) and every image replaces one particle. Assets are reused in a loop when there are fewer images than particles.
- **A collage, not a mosaic**: each tile's height follows its source aspect ratio and tiles may overlap. A texture array keeps every asset independent — zoom in and each photo is still readable.
- **Camera animation**: starts inside the photo cloud, pulls back while the tiles fly to their places, and ends on the complete image.
- **Export**: 06 exports the whole fly-in and assembly; 07 exports the current view as a sequence or a single frame. Frames go into a per-run subfolder, ready for an NLE image sequence.

## Highlights

- **Asset texture array + per-layer mipmaps**: assets are no longer packed into one atlas. Distant tiles no longer shimmer or moiré, and close-ups stay sharp; the default 243 assets stay in the 16 MB range.
- **4× MSAA on the composer**: cleaner geometric tile edges.
- **Exports are true snapshots**: the panel is locked, auto-rotate is off, and the load-in fly animation is frozen while exporting. Clicking Play or resizing the window mid-export cannot contaminate the output.
- **Portrait / square**: 4:5, 9:16 and 1:1, with the camera re-framed for the target aspect.
- **Transparent PNG**: alpha-zero background (glow is disabled automatically); JPEG stays on black.
- **Reproducible**: default `seed=20261017`; the same seed and parameters reproduce the same composition. "Reshuffle" picks a new seed.
- **Upright tiles**: no random in-plane rotation.
- **Depth = 0**: noise and depth distribution are disabled automatically instead of appearing broken.
- **Per-run frame folders**: `frames_YYYYMMDD_HHMMSS/`, starting at `frame_00001`, so old frames never leak into a new sequence.

## Quick start

### Online

Open <https://afeiisfine.github.io/particle-collage/>.  
Requires Chrome / Edge or Safari 16.4+, with WebGL2 support.

### Local

```bash
cd particle-collage
python3 -m http.server 8125 --bind 127.0.0.1
# then open http://localhost:8125/index.html
```

Both the online and local versions work offline; images are processed entirely in the browser and are never uploaded.

> Folder export uses the File System Access API, so it needs Chrome / Edge (Safari does not support choosing a folder yet).

## How to use

1. **Replace the master image**: drop an image into the window, or use "Replace master image" in group 01.
2. **Upload collage images**: use "Upload collage images" in group 01 and pick a folder; subfolders are read recursively. You can also drop multiple images into the window (still works after the first load).
3. **Distribution**: group 02 controls particle count, luminance floor/ceiling, and tile size; "Reshuffle" re-rolls the layout.
4. **Depth**: group 03 controls thickness, random/brightness distribution, and noise; the last two are inactive when depth is 0.
5. **Tone**: group 04 chooses Multiply or Luminance swap, with γ / gain.
6. **Appearance**: group 05 controls Fixed / Face-screen facing, float amount, and glow.
7. **Play the animation**: group 06 "Play · fly in & assemble"; "Reset view" also reassembles the image.
8. **Export**: group 07 chooses sequence/single frame, frame rate, resolution, background, and format.

## Export

- **07 "Export sequence"**: records the current view as-is; the camera and assembly do not move, only the subtle particle drift advances.
- **07 "Single frame"**: renders just the current frame.
- **06 "Export assembly sequence"**: ignores the 07 content choice and exports the whole fly-in and assembly.
- **Resolutions**: 1920×1080 / 2560×1440 / 3840×2160 / 1080×1350 (4:5) / 1080×1920 (9:16) / 1080×1080 (1:1) / current window.
- **Formats**: JPEG (0.95) / PNG; PNG can use a transparent background.
- **Files**: a sequence creates `frames_YYYYMMDD_HHMMSS/` inside the chosen folder and names frames `frame_00001.jpg/png`; single frames include milliseconds.
- **Stop**: the progress bar at the top of the screen can stop an export at any time; frames already written are kept.

## Browser / performance

- Best on the latest Chrome / Edge; Safari 16.4+ can run the main scene but cannot choose a folder for export.
- WebGL2 is required (texture array + mipmaps).
- Default scene: 7,790 particles. At 60k particles, 1280×800 / DPR1 holds roughly 60fps on M-series Chrome in testing.
- Asset limit: `min(1024, GPU MAX_ARRAY_TEXTURE_LAYERS)`. Going over shows a warning and truncates instead of silently dropping images.

## Development

```bash
# local static server
python3 -m http.server 8125 --bind 127.0.0.1

# build the single-file share (needs Node/npx + esbuild)
python3 build_share.py
# → dist/index.html + a single-file ZIP (git-ignored; distributed via Releases)
```

Source files:

- `index.html` — page, styles, three.js scene, shaders, and export logic in one file;
- `libs/` — three.js r160 and addons;
- `materials-manifest.js` — the default 243 asset thumbnails as data URLs;
- `main.jpg` — the default master image;
- `test.jpg` / `test-assets/` — development test images;
- `build_share.py` — inlines three.js, the asset manifest, and the master image into one HTML file.

The default assets and master image are the author's demo material; replace them with your own images before commercial use or redistribution.

## Demo assets & license

- **Code** (the script logic in `index.html`, `build_share.py`, and anything outside `libs`): MIT, see [LICENSE](LICENSE).
- **Default demo images** (`main.jpg` and the 243 thumbnails embedded in `materials-manifest.js`): © 2026 AfeiIsFine (阿飞这个名字挺好的), included only as a demonstration. **They are not covered by the MIT license**; contact the author before reusing them. Replace them with your own images when using the code.
- **three.js r160**: MIT, copyright the three.js authors; see the file header of `libs/three.module.js` and <https://threejs.org>.
- `test.jpg` / `test-assets/` are development test patterns and may be used with the code for testing.

## Related project

- Previous: [Image → Particle Point Cloud](https://github.com/AfeiIsFine/particle-pointcloud) — it samples a master image into particles too, but renders points instead of photo tiles.
