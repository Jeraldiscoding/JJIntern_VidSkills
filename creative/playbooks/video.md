# Video from idea to export

Start with the [current owner direction](../CREATIVE-DIRECTION.md) and the latest accepted version of the selected concept. The [revision 11 discovery film](../projects/discovery-packet/README.md) is the current local reference for authored motion and sound. Existing approval persists through requested revisions; do not restart approved style exploration or follow superseded timing from an older draft.

## Stack decision

Initial workspace inspection (2026-10-17): no application, package manifest, renderer, assets or existing video. Installed: Node v25.1.0, Chrome, FFmpeg 8.1.2 and ffprobe; Python has no Pillow/Playwright. Codex CLI reports 0.162.0-alpha.17.2. Use existing Chrome for truthful logged-out capture and deterministic HTML/canvas frames, then FFmpeg H.264 export. This is a small local proof workflow, not a replacement application stack. No paid service or large dependency installation is needed. If a rendering stack is later added, inspect it and prefer its maintained conventions.

## Ordered workflow

1. **Brief:** audience, concrete problem, desired action, platform, length, constraints, evidence and assets. Use [brief-template.md](../examples/brief-template.md).
2. **Research:** check product facts, claims and current listing status; inspect relevant references and record what was actually seen. Save only public/sanitised evidence.
3. **Multiple concepts:** compare at least three mechanisms, then select and record the decision using [concept-selection.md](concept-selection.md). Resolve weak premises before rendering.
4. **Script + shot list:** every shot specifies the fields below. Exact copy includes qualifiers and CTA. Account for reading, action, consequence and hold time.
5. **Storyboard:** export readable frames at the hook, action, proof and payoff. A different section deserves a different composition when it helps the story; no need for an image-generation workflow for genuine product captures.
6. **Rough motion:** choose the appropriate route: a real product demonstration or an authored editorial graphic story. Preserve causality in both. Product captures/reconstructions require verified behaviour and source records; a prototype must be labelled. Editorial shapes can transform and connect without imitating app UI or claiming a real product event. Include sound early when rhythm and synchronized cues are part of the selected direction.
7. **Review:** evaluate idea, evidence, action/result, muted comprehension and layout before effects. Revise idea if the rubric fails.
8. **Final render:** freeze asset versions, fonts, timings and claim IDs; render deterministically. Do not hide loading errors with invented role rows.
9. **QA:** inspect representative frames and watch the whole export with and without sound; test on a real phone; verify claims again near release. Use [rubric.md](../qa/rubric.md).
10. **Export:** produce the platform-specific delivery, caption/transcript and source manifest. Check official requirements in [platform-guidance.md](../references/platform-guidance.md) at delivery time.
11. **Performance review:** log results and decide the next test; see [performance.md](performance.md). Publishing is a separate user action unless explicitly authorized.

## Shot record

| Field | Required detail |
|---|---|
| Time | Start/end seconds; no accidental gaps or overlapping copy. |
| Audience sees | Composition, crop and real visual source. |
| Exact copy | All editorial words and material qualifications. |
| Movement | Input, crop, pan, reveal or cut, with duration. |
| Change and purpose | What becomes clearer because it moves. |
| Product asset | Local capture path and evidence/source URL; no fake interface. |
| Sound | Cue/absence, provenance and meaning. |
| Viewer understanding | The one thing this shot adds. |

## Captures, fonts and assets

Use an isolated logged-out browser profile. Never use existing cookies, credentials or private account data for convenience. For authenticated flows, request a sanitised demo account/capture only if the selected journey requires it. Remove names, email, saved/application history, notification contents, URL query tokens and browser chrome. Check each captured frame; blurring after export can leave earlier frames exposed.

Wait for `document.fonts.ready`, verify `document.fonts.check()` for the family and weight, and inspect the rendered text. Do not invent weights, synthesize a new wordmark or silently substitute an arbitrary typeface. System fonts vary by platform; record the renderer OS and embed an approved/licensed font when cross-platform consistency becomes necessary. Archive only necessary public assets with source URL, hash, date and usage notes. Obtain the official vector logo if a raster mark cannot survive the intended size.

Product motion must show meaningful cause and result: input → filtered company; open menu → real options; select filter → real matching results when verified. Preserve input/results in a stable frame. A single crop may make small UI legible, but moving a static screenshot alone does not demonstrate functionality. Time-compressed captures must be recorded as edited; never claim the edit measures performance.

For editorial motion, preserve the identity of what transforms: source boundary into packet edge, glyphs into data tracks, tracks into a visible receiving action. Design approach, contact and occlusion together. Use background motion and airflow to establish speed while keeping the focal shape legible; foreground translation is not always necessary. End travel before a reading/result hold. These are transferable techniques from revision 11, not a requirement to reuse its packet story in every film.

Review pacing by beat: transformation, apparent travel, handoff, result and reading. The owner rejected both sluggish motion and an indiscriminately rushed edit. A technically accelerating curve can still look slow; inspect the actual rendered motion. A connected handoff and short stable result matter more than adding increasingly elaborate impact effects.

Current reproduction examples: [Canvas source](../projects/discovery-packet/revision-11/source/motion.html), [Chrome/FFmpeg renderer](../projects/discovery-packet/revision-11/source/render-motion.mjs), [original score](../projects/discovery-packet/revision-11/audio/build_score.py), [export verifier](../projects/discovery-packet/revision-11/source/verify-motion.py) and [commands](../projects/discovery-packet/revision-11/production-notes.txt).

## Delivery defaults (house choices, not platform mandates)

- Video: 1080×1920, 9:16, constant frame rate, MP4 H.264, yuv420p, faststart; AAC 48 kHz when audio exists. The initial proof used 30 fps; revision 11 uses 60 fps delivery from a requested native 120 fps master. Choose for the brief and movement, not a universal platform rule. Do not create a claimed native master by duplicating/interpolating a lower-rate render. Choose bitrate/CRF after inspecting gradients and text. Reduced-resolution roughs must be labelled.
- Keep essential copy inside a conservative draft rectangle x=90–900, y=240–1480 at 1080×1920. This is a **house starting point**, not a certified platform safe area. Captions, device crop and platform controls change coverage. Apply each current placement's official overlay/checker and inspect the actual upload preview before release. Demonstrated nonessential UI may extend beyond this box.
- At 1080 width, start headings around 76–110 px, explanation 48–60 px, material qualifiers ≥42 px. Test at 360 CSS px wide; rendered UI often needs a tight crop. If it cannot be read in the available hold, shorten copy or lengthen the shot.
- All meaning must survive mute. Add verbatim captions if speech is later requested; include important non-speech audio meaning in captions. For these text-led examples, provide an equivalent transcript and readable on-screen copy without redundant caption clutter.
- Make an intentional sound choice early. For energetic brand motion, follow the owner's preference for a contemporary drum-led groove and distinct morph, airflow, contact and result cues; avoid passive lounge-like music. A silent structure pass remains useful, but is not the complete music-driven deliverable. Exact 160 BPM and mathematical synthesis belong to the discovery film's brief. Document synthesis or music rights, including holder, placements, territory, duration and expiry; platform-library permission does not automatically transfer. Keep the film understandable muted.

## Local proof commands

See `examples/proof/README.md` for the tested capture/render commands. The proof is an editorial timing demonstration, not a claim of release readiness. Rerender from saved captures offline; recapture only with explicit public URLs and a clean browser session. Never make a successful-export claim until ffprobe and visual inspection confirm it.
