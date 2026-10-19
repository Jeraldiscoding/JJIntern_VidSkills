# Company-search rough

[Watch the 12-second local MP4](company-search-rough.mp4). [Phone-size contact sheet](contact-sheet.png). [Brief A](../../briefs/A-product-demo.md). [Actual artifact review](../../qa/proof-review.md).

This is a silent, text-led timing proof. It uses ten actual public company-directory states, captured through real browser inputs, not a fabricated interface. A stable frame connects typed input to the narrowed result. Input cadence is edited; it is not a claim about product latency. The final qualification distinguishes company presence from an open vacancy.

**Output verified:** 1080×1920, H.264/yuv420p, 30 fps, 360 frames, 12 seconds, no audio stream. See `render-manifest.json` for source hashes, capture provenance, software versions and file properties. The pre-encode contact sheet is for reviewing composition; encoded checkpoint inspection is documented separately.

This remains the historical search proof. When the owner's marketing direction was updated on 19 October 2026, its original [brand-token snapshot](brand-tokens-2026-10-17.json) was preserved byte-for-byte and the manifest was pointed to that snapshot, retaining the original hash. The proof video and scene were not changed. Use [current creative direction](../../CREATIVE-DIRECTION.md) for new work.

## Reproduce using installed tools

Prerequisites: Node with global WebSocket (tested v25.1.0), Google Chrome (macOS path below), FFmpeg/libx264 and ffprobe on PATH. No npm/Python packages needed. Run from the workspace root. Browser graphics/system-font rendering can differ across OS/browser versions; pin the recorded host for consistent appearance.

Start a **new isolated** browser; never point these commands at a personal browser profile:

```sh
JJINTERN_CHROME_PROFILE=$(mktemp -d /tmp/jjintern-creative.XXXXXX)
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --disable-gpu --no-first-run --no-default-browser-check \
  --user-data-dir="$JJINTERN_CHROME_PROFILE" \
  --remote-debugging-address=127.0.0.1 --remote-debugging-port=0 about:blank
```

Chrome prints a local debugger URL with a port. In another terminal use that numeric port in place of `PORT`:

```sh
# Optional fresh public recapture; uses network, validates real result before recording success.
node creative/scripts/capture-public.mjs PORT YYYY-MM-DD

# Offline render from the saved screenshots; only loopback networking is used.
node creative/scripts/render-proof.mjs PORT

ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,pix_fmt,avg_frame_rate,nb_frames \
  -of json creative/examples/proof/company-search-rough.mp4
ffmpeg -hide_banner -v error -i creative/examples/proof/company-search-rough.mp4 -f null -
python3 creative/scripts/validate-system.py
```

`PORT` and `YYYY-MM-DD` are parameters, not runnable literals. Supply the actual client check date; do not reuse the first audit date for a new check. The renderer starts a temporary server bound only to 127.0.0.1 and serves only the scene and named screenshot files, then closes it. It never serves the whole workspace. Chrome local debugging exposes its isolated session on loopback; stop the Chrome process after production using Ctrl-C in its terminal. Do not kill unrelated browsers.

The capture overwrites the current set; archive it to a dated snapshot before a new campaign recapture. It generates a fresh capture manifest after success; rendering generates its source/output manifest after success. For a new campaign, update the scene's visible date, captions and brief to the actual recheck date; this scene is the 17 October 2026 proof. If the validation cannot confirm the matching company, it fails; never publish incomplete captures or invent results. A rendering failure is a failure, even if an incomplete output file exists.

## Handoff and limitations

- `scene.html`: deterministic `drawScene(t)` and a width assertion for every editorial line; actual captured UI is cropped faithfully.
- `frame-0.png`…`frame-5.png`: source checkpoint frames at 0, 2.5, 4.75, 6.5, 9, 11 seconds.
- `contact-sheet.png`: those frames at 360×640 each, before video compression. Full-size words are best checked in the individual frames.
- `transcript.vtt` / `caption.txt`: accessible equivalent and destination, with no speech implied.
- `render-manifest.json`: successful build properties and source hashes. Regenerate after a source or render change.

Physical-phone readability, current platform upload previews, full real-time viewing and campaign rights are not automatically passed by export. See the review's performed/pending checks. The proof does not announce a vacancy, make a salary claim or demonstrate saving/tracking.
