# Rectangle/browser asset audit

Checked 17 October 2026 (Europe/Stockholm). Scope: three approval style frames only; no full video, motion test or audio production. Read the supplied revised brief, `creative/AGENTS.md`, product brief/evidence, brand guide/tokens, grounding skill, and BUCK inspection record. Earlier finished films and folded-sheet approval are not current creative approval.

## Selected authentic sources

| Use | Asset | Exact geometry | Guidance |
|---|---|---|---|
| Microsoft opener | `../captures/microsoft-internship-programmes.png` | 1860×2220 PNG; real 620×740 CSS viewport, 3× DPR | Preferred. Authentic responsive Internship programs section and Global university internships card; full paragraph identifies Microsoft. A contiguous source crop `[0,0,1860,1605]` retains heading + first complete card and removes most unrelated next programme. Preserve natural proportions. |
| Narrower opener option | `../captures/microsoft-internship-programmes-540.png` | 1620×2340 PNG; real 540×780 CSS viewport, 3× DPR | Actual responsive layout, slightly larger relative text; includes next programme heading near bottom. Crop as a contiguous rectangle, never reconstruct individual elements. |
| Receiving feed | `../../pipeline/captures/feed-loaded.png` | 1560×3376 PNG; 390×844 CSS, 4× DPR | Clean pre-handoff loaded public feed. Actual JJ Intern header, controls and multiple real role rows. At 900px displayed width its full proportional height is 1947.7px, so use a tighter contiguous vertical crop or a larger composition rather than squeezing it. Top `[0,0,1560,2400]` retains site header, controls and first two complete role rows while excluding bottom navigation; display aspect must remain 1560:2400. |
| Brand mark if needed earlier | `../../../assets/evidence/product/logo-mark.png` | 512×512 original transparent PNG | Optional, modest size, preserve original shape/colour/proportions. Final requested JJIntern is plain textual sign-off, not an assertion that a new wordmark asset is official. |

The browser chrome is the proposed film presentation. Keep its address accurate (`careers.microsoft.com/v2/global/en/students` for opener; `jjintern.com/feed` for receiving proof). The captured page content is authentic and unchanged.

## Fresh Microsoft capture provenance

The actual public page was opened in a clean temporary, logged-out headless Chrome profile on isolated CDP port 9352. Optional cookies were rejected. Only viewport changes and a real page scroll were used; no page text, CSS, DOM layout, image or employer interface was edited. The source title is **Early in profession | Microsoft Careers**. The genuine page header is **static**, so it naturally scrolls out of view at this section. Do not transplant the header into a new position or imply it is sticky. The displayed source address and real body identification establish Microsoft context.

- URL: https://careers.microsoft.com/v2/global/en/students
- Reproducer: `../captures/capture-microsoft.mjs` (expects the explicitly isolated Chrome port)
- Record: `../captures/microsoft-programmes-capture-record.json` contains source, viewport, scroll, DOM section, exact heading bounds, PNG SHA-256 hashes and capture timestamps.
- `microsoft-programmes-probe.png` is a discarded wider-context framing probe; use one of the final named captures above.
- Real photography within the original webpage is part of this authentic page capture; no people or employer imagery were generated.

This verifies current programme information only. It does not establish a newly posted individual vacancy, an internship intake, a Singapore opening, employer partnership or JJIntern ingestion. No role-specific page was selected.

## Feed evidence and prohibited inferences

P07 and `../../pipeline/captures/capture-note.txt` establish the loaded public feed and actual company-or-role search. Use the clean initial feed, preserving all role titles, counts and dates. The older Microsoft-specific feed assets show a **1 Sept** Research Intern entry. Its clicked application handoff reached a generic Microsoft careers portal and changed the local status to Applied without a real application; those facts do not prove availability or an application. Do not use the old Microsoft close-up as newly received information.

The revised user direction explicitly removes the on-screen “Example posting” label and permits an authentic programme-to-existing-feed visual metaphor. This supersedes the older label direction for this revision, but does not authorize a fabricated new row, count change, date change, alert, complete coverage or measured detection/ingestion speed. The frame should simply resolve into the already captured existing feed.

## Reference transfer

`../../renewal/reference/inspection.md` documents actual decoded BUCK Microsoft Surface frames. The useful qualities are broad softbox reflections, coherent edge thickness, substantial near-field subject scale, controlled perspective, and abstract material action resolving back to real product proof. Its historical folded folio recommendation is superseded by the new rectangular packet brief. BUCK frames are visual references only and are not campaign assets.

## Readiness and agreed timeline

Assets are ready for the three requested style frames. Read actual composed frames at full size and at a 360px-wide equivalent: browser identity and internship context should be clear; not every programme paragraph must become hero copy. Never sharpen unreadable type by retyping the UI.

The user resolved the conflicting flight instructions: accelerating travel lasts exactly **2.000 seconds, from 4.500 through 6.500 seconds**, with arrival at **6.500 seconds**. For later approved animation use `u=(t-4.500)/2.000`, native 120 fps flight frames 540–779 and arrival frame 780; at 60 fps use flight frames 270–389 and arrival frame 390. This replaces the inconsistent one-second denominator/frame numbers in the earlier pasted brief. The present deliverable remains three still style frames only.
