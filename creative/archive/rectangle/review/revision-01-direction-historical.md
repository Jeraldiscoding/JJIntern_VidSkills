# JJIntern — browser / rectangle / discovery

**Current visual revision:** [Revision 03 — simple graphic direction](../revision-03/direction.md). The user now permits a cartoonish treatment and prioritizes clean, simple information. Revision 03 replaces the physical studio/material direction with flat graphics and tighter genuine source excerpts. The confirmed two-second timing and exact story/copy below remain in force. No style set is approved for animation yet.

Revised approval study, 17 October 2026. The three new frames in `styleframes/` are actual locally rendered 1080×1920 PNGs. Earlier finished videos and folded-sheet studies remain rejected or historical. This folder contains no produced animation or soundtrack.

## Direction for approval

One graphite studio connects a genuine Microsoft programme page, its information compacted into a satin-silver rectangular packet, and the authentic JJIntern feed. A fine polished boundary becomes the packet's edge; text from the capture remains as shallow information marks. A narrow blue channel leads toward the right. Broad near-field softbox reflections reveal the solid volume. Leftward tapered trails and a small leading-edge pressure contour establish the direction of travel. The destination opens into readable product proof.

The three approval images show the settled source browser, a representative fast-flight material state, and the settled receiving feed. These are a visual proposal, not proof that the continuous morph, acceleration, arrival or sound already works. Board captions are review annotations outside the actual 1080×1920 frames.

## Timing — user correction applied

The user selected **two seconds, 4.500–6.500 seconds, keeping arrival at 6.500 seconds**. This supersedes every one-second reference and old frame index in the pasted brief.

`u = clamp((t - 4.500) / 2.000, 0, 1)`

`x(u) = x_start + (x_end - x_start) * (0.12*u + 0.88*u*u*u)`

The velocity is positive throughout and increases for every `u > 0`; no braking/ease-out occurs before contact. Native 120 fps flight frames are **540–779**, arrival **780**. At 60 fps they are **270–389**, arrival **390**. The full film remains exactly 18.000 seconds: 2,160 native frames and 1,080 alternate-original frames.

| Time | Visual / action | Exact editorial copy | Sound intent / meaning |
|---|---|---|---|
| 0.000–3.000 | Captured Microsoft Internship programs section in a shallow-perspective browser; controlled entrance, then reading hold. | No added campaign line. Presentation browser title: Microsoft Careers. Actual source URL. | One small synthesized metal ding and restrained settling. Establish employer-page checking, without a posting event. |
| 3.000–4.500 | Same page boundary compacts locally; captured text rows become packet marks and boundary becomes edge. No horizontal travel yet. | None. | Filtered deterministic-noise friction and small closures follow geometry. |
| 4.500–6.500 | Near-field rectangle accelerates left to right over exactly two seconds; left trails lengthen/densify with velocity; shallow pressure at right edge. | None. | New filtered airflow brightens and pans with the same velocity function. |
| 6.500–10.000 | Contact at 6.500; packet face resolves directly into receiving feed by about 7.100, then holds. Feed content/dates/counts remain unchanged. | Actual capture, neutral presentation title JJIntern and jjintern.com/feed address. | Short controlled contact, then room for the proof. This is editorial speed, not measured ingestion. |
| 10.000–10.600 | Found. appears within the continuing feed/material composition. | **Found.** | Small harmonic opening; discovery result, not a latency guarantee. |
| 10.600–11.300 | Transition to two balanced lines, first line then second with a short rhythmic offset. Reflection/seam connects the composition. | **We handle the finding.** / **You focus on applying.** | Harmony opens without a large impact. |
| 11.300–15.000 | Both lines fully legible; restrained continuing material reflection. | Same two lines. | Groove leaves space for relief and agency. |
| 15.000–18.000 | Prompt settle into textual sign-off, held through last frame. | **JJIntern** only. | Confident synthesized harmonic resolution. No tagline, URL, button or CTA. |

## Captures and claim boundaries

- Microsoft source: https://careers.microsoft.com/v2/global/en/students. Fresh isolated public capture on 17 October 2026; native responsive page, optional cookies rejected, no account. The programme heading and description establish internship context, not a new individual vacancy. The original page photography remains part of that capture; no person was generated.
- Source frame uses `captures/microsoft-internship-programmes-540.png`, source rectangle `[0,110,1620,1490]`. The whole rectangular crop is mapped at its original ratio onto the browser plane. Its header was genuinely out of view after scrolling; it was not transplanted. “Microsoft Careers” is a shortened, accurate presentation title. The neutral browser surround is editorial geometry, not an invented employer page.
- Packet text is derived from the same capture's actual heading/description regions and compressed as abstract material marks. No fabricated role, date, logo, alert or requisition is introduced. The photograph does not become a packet-face decoration.
- Feed frame uses the clean pre-handoff `../pipeline/captures/feed-loaded.png`, P07, source rectangle `[0,0,1560,2268]`, ending after the complete Shopee row. Source pixels, dates, counts and row ordering remain unchanged. This is the existing public feed, not evidence of Microsoft ingestion. “JJIntern” in presentation chrome is editorial shorthand; the captured site header remains intact.
- P06 provides the owner's 30-minute scheduled-check truth; this cadence is retained internally and is not on screen. No instant detection, coverage, matching, auto-application, application submission or hiring outcome is claimed. “Found.” names discovery. Applying remains the student's action.
- The user's new authentic-source direction replaces the old fictional-posting treatment. **No “Example posting” label appears.** This is justified by the change to a real programme page and absence of a new-posting event; it is not permission to invent a vacancy.

## Review and next gate

Three frames were rendered, inspected individually, and checked in a 360px-per-panel equivalent. Iterations strengthened Microsoft identity in presentation chrome, replaced a flat packet highlight with finite softbox reflections, varied airflow spacing, shortened the pressure contour and ended the feed crop after a complete row. Source hashes and output hashes are in `styleframe-manifest.json`. Reference notes and visual QA are in `review/`.

As explicitly requested in the pasted brief: **“First create 2–3 revised actual style frames … Wait for the user's approval before full animation/audio production.”** These frames are the approval gate. After approval, implement and inspect a morph → two-second accelerating flight → direct arrival motion test before producing the full 18-second film and new mathematically synthesized groove. The sound will use only oscillators, deterministic noise, filters and envelopes; no old audio, samples or loops.

Full motion, synchronized sound, encoded playback, native frame-count verification, physical-phone and platform-preview checks remain unperformed. No publishing has occurred.

## Reproduce these stills

Uses the installed Chrome, Node and local CDP helper; no added package/toolchain. Launch a clean temporary Chrome profile with remote debugging port 9354, then run from the workspace:

```sh
node creative/archive/rectangle/source/render-styleframes.mjs 9354
```

`source/studio.js` contains new rectangle geometry, light and airflow studies. `source/styleframes.html` composes the authentic textures and browser surround. The render script embeds the original assets into a local preview, renders internally at 2160×3840 and downsamples to 1080×1920 PNGs. System sans resolves on this macOS/Chrome host; no system fonts are redistributed. Reproduction from captures is offline; recapturing the source page is a separate optional script in `captures/`.
