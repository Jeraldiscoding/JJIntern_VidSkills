# Rectangle/browser revision — direct reference review

Reviewed 17 October 2026. Scope: revised style-frame direction and local rendering feasibility; no animation or audio produced in this review.

## Inspected evidence

- Read the revised pasted brief, `creative/AGENTS.md`, product brief, brand guide/tokens, creative rubric, existing BUCK inspection record, and the earlier rendering sources.
- Opened actual decoded BUCK film images: `contact-sheet.jpg`, `film-03s.jpg`, `film-15s.jpg`, `film-27s.jpg`, `film-35s.jpg`, `film-43s.jpg`, and `sequence-31-39s.jpg` using the image tool. These are direct observations of the saved reference footage, not assumptions from the project page.
- Inspected the previous folded-sheet approval board only to identify rejected choices. Its compositions are not the basis of the new frames.
- Reference provenance remains https://buck.co/work/microsoft-surface and the archived source/inspection record under `../../renewal/reference/`. Reference images are research, never campaign assets.

## Six concrete principles for the new frames

1. **Build the light as a shared studio, then let surfaces reveal it.** At 3 seconds the closed Surface has one broad upper-left illumination field, a fine brighter lower edge, and a soft local ground shadow. At 43 seconds the pearl ribbons and laptop share the same warm field and coherent highlight direction. For the JJIntern graphite set, use a large neutral softbox above/left, a weaker narrow neutral edge source, and only a local blue seam. The browser rim, packet bevel and receiving browser must reflect the same environment; three unrelated gradients will break the story's material continuity. Keep the neutral diffuse face brighter than the graphite without clipping the softbox to solid white.

2. **Separate the satin face, polished bevel and dark seam.** The 35-second plate study reads as thickness because the face, skinny colored edge, overlap shadow and rear plane are visibly different. For the compact rectangle, use a low-gloss pearl/silver face, a genuinely narrow polished chamfer, and a fine dark join with blue confined inside it. Start near 720–850 projected pixels wide with roughly 30–60 projected pixels of visible thickness; the packet should feel substantial, not as thick as a hard drive or as thin as a payment card. Keep corner radii small enough that the four edges still define a rectangle. These measurements are design starting points, not measurements of the reference.

3. **Use one restrained perspective for all causal surfaces.** The Surface product views hold scale and exhibit natural shallow perspective; depth comes from edge exposure, occlusion and focus. Keep the new browser nearly frontal for reading, with a mild three-quarter lean that exposes one lower/side edge. Preserve a related camera orientation when the source plane compacts and when the packet face becomes the feed plane. Do not strongly skew the feed just to make it feel 3D. A useful starting range is 4–10° yaw and 2–7° pitch for reading planes, with a slightly more exposed packet top during flight. Keep the packet in the near field rather than receding toward a vanishing point.

4. **Carry actual information through the material metaphor.** The 31–39-second sequence goes from the laptop to compact layers, back to trackpad action, then opened layers and real multiwindow screen. The connection survives because the abstraction returns to product proof. Here the actual Microsoft source crop must supply the rows and page plane that compact; retain some recognizable row rhythm plus the original browser boundary in the packet's face/seam. At arrival, align a packet edge to the receiving browser's corresponding edge and open that same plane into the authentic feed. Separate pasted screenshots and a generic unrelated metal slab would lose the causal mechanism, even if individually polished.

5. **Spend effects where they explain resistance.** The reference uses quiet environment richness rather than outlining every edge. In the flight style frame, draw leftward trails with different lengths and tapered luminance; concentrate their brightest segments close behind the packet, and let the distant tails disappear into graphite. Shape a shallow contour only just ahead of the right leading corners, with a second much weaker displaced-air trace. Show the packet cleanly over these effects and keep front-face text/data marks sharp enough to connect back to the page. Avoid evenly spaced full-width rails, blue edge glow, smoke, a ring around the object, and any tunnel perspective.

6. **Let each vertical frame have a different information job.** Opening: the real Microsoft identity and Internship programs context dominate within a single refined browser. Flight: the substantial rectangular object and asymmetrical leftward trails dominate, with room on the right indicating its destination. Receiving: a large authentic feed dominates inside the receiving browser, retaining site context and at least one useful complete role. The same graphite field, light direction and edge finish bind them together. Use whitespace to reserve the direction of travel or support reading, not to host a repeated top-left logo and filler caption.

## Earlier implementation pitfalls to avoid

- `renewal/source/styleframes.html` redraws a fake document titled “Example posting.” It must not be reused for this revision; the user explicitly requires a captured Microsoft page and no such label.
- The folded object is curved, open and multi-layered; its silhouette does not satisfy a compact rectangular packet. Replace the geometry and composition rather than changing the old fold's material color.
- The earlier third frame flattens the feed into a direct crop on the canvas. It lacks the requested receiving browser, shared perspective and edge-aligned arrival relationship.
- The earlier frame set repeats a detached upper-left logo and bottom labels. The new source browser supplies Microsoft context; the genuine feed supplies JJIntern context. Additional persistent branding should not displace these subjects.
- `slick-packet.js` uses a saturated blue body, pronounced rounding and a clear-coat look. Its lighting utilities may be informative, but its material/shape would revive the rejected plastic payment-card appearance.
- `renewal/source/studio.js` has a `clock` uniform that is not used in the shader and switches between separate shape modes. That source is a static material study, not evidence of a continuous morph or native-frame animation.
- Existing render sources contain a 20-second duration, 2,400 native frames and 1,200 alternate frames. None of these can be carried into the proposed 18-second deliverable. Native output would later require exactly 2,160 independently evaluated frames, with 1,080 selected originals for 60 fps.
- Existing style-frame export relies on an isolated Chrome CDP port being alive and selects its first page. Use a dedicated new browser profile/port so capture work cannot replace another active scene or user's browsing context.

## Available rendering stack

- `/Applications/Google Chrome.app` exists. `creative/scripts/cdp.mjs` is a local dependency-free CDP client using modern Node WebSocket. Canvas 2D and custom WebGL shaders are already used for deterministic full-resolution exports.
- `/opt/homebrew/bin/node`, `/opt/homebrew/bin/python3` and `/opt/homebrew/bin/ffmpeg` are available. No `blender` executable or `/Applications/Blender.app` was found in the checked paths.
- Existing local code supports image textures, custom per-pixel studio reflections/occlusion, PNG exports, and FFmpeg encoding. New style frames can be produced within this stack without installing dependencies or spending on external renders.
- For text fidelity, map authentic captured pixels to the browser face with uniform pre-crop scale; perspective may transform the whole plane, but never independently stretch or rebuild the UI. Use supersampling for edge quality and inspect the final 1080×1920 PNG, including a 360-pixel-wide equivalent.

## Timing conflict resolved by user

The original pasted brief contains incompatible one- and two-second flight instructions. During this review, the user resolved the timing in favor of **two seconds, 4.500–6.500 seconds, arriving at exactly 6.500 seconds** (relayed by the parent agent). Normalize the accelerating curve with `u = (t - 4.500) / 2.000`. Native flight frames are 540–779, with arrival frame 780; at 60 fps, flight frames are 270–389, with arrival frame 390. The old one-second formula denominator and arrival indices are superseded. The complete film remains 18.000 seconds.

## Readiness

Concept: the revised source-browser → compact rectangle → real-feed mechanism is clear. Assets: authentic source capture and final feed crop need review in the new compositions. Artifact: no new frames inspected by this reviewer yet. Release: not in scope; this is a style-frame approval stage. This review does not certify motion, timing, audio, real-phone readability or final export.
