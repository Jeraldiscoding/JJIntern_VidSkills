# JJIntern — simple graphic direction, revision 03

Historical study, superseded by [revision 04](../revision-04/direction.md): the user subsequently requested no person/photo in the careers scene and the original JJIntern logo instead of a receiving browser.

17 October 2026. Latest user instruction: the browser, receiving feed and packet can be cartoonish; the priority is clean, neat, slick and informative enough to understand. This supersedes the earlier realistic metal/studio treatment. Revision 02 and prior stills remain unapproved historical studies.

## New visual language

Flat 2D shapes, one soft blue background (`#edf3ff`), white information surfaces, dark readable type (`#203145`), thin blue-gray outlines and JJIntern blue (`#0071e3`). No physical studio, gradients, simulated reflections, metal bevels, cast shadows or camera perspective. Neutral browser surrounds are illustrative presentation graphics.

1. **Source:** a minimal browser title strip identifies Microsoft Careers. The authentic page excerpt shows Internship programs, its original photograph and Global university internships. The dense paragraph is outside the crop. Only employer and internship context need to be understood.
2. **Packet:** a simple rectangular data tile with three information bars, a blue leading-edge seam and three clear leftward trails. It is an abstract information symbol, not a payment card, notification or employer interface. During future motion, source content must visibly compact into this shape.
3. **Receiving:** a matching browser strip identifies JJIntern and the real feed domain. The screenshot crop concentrates on two complete real role rows, Tencent and DBS. Site navigation, counters and filter controls are outside the crop; no rows or dates are rewritten.

## Exact assets

- Microsoft: `../captures/microsoft-internship-programmes-540.png`, source crop `[0,110,1620,960]`; actual P08 capture from https://careers.microsoft.com/v2/global/en/students. This is programme context, not a newly published individual vacancy. Original photograph and text pixels are retained at uniform scale.
- Feed: `../revision-02/captures/feed-light-tech-scrolled.png`, source crop `[0,720,1720,980]`; actual P09 light-theme Tech-filter capture from https://jjintern.com/feed. The crop is contiguous and uniformly scaled. Its subset is not presented as complete coverage or a new Microsoft ingestion result.
- Presentation browser titles/domains are editorial labels. Actual page content remains captured evidence. There is no fabricated employer vacancy, UI action, date, count, alert, status change or posting stamp.

## Story unchanged

The confirmed flight remains **4.500–6.500 seconds**, increasing speed over two seconds and arriving at 6.500. Total duration remains **18.000 seconds**. Exact payoff: **Found.** followed by **We handle the finding. / You focus on applying.** Final 15.000–18.000 sign-off: **JJIntern** alone. The same restrictions on instant detection, complete coverage, personal matching, auto-application and hiring promises remain.

The native 120 fps master and alternate-original 60 fps export are future deliverables. No animation/audio is produced at this approval stage. The original user instruction still requires approval of revised style frames before production; after approval, inspect the causal morph, two-second accelerating flight and direct arrival in a motion test first.

## Files and reproduction

`styleframes/01-browser.png`, `02-packet.png` and `03-feed.png` are 1080×1920 PNGs rendered from the new Canvas source. `approval-board.png` is a review layout; its captions are outside the film frames. `phone-board.png` shows each frame at 360px width for a reduced-size check. These stills cannot verify continuity, acceleration or exact motion duration.

Start an isolated Chrome profile with remote debugging port 9354, then run:

```sh
node creative/archive/rectangle/revision-03/source/render-styleframes.mjs 9354
```

Canvas evaluates at 2160×3840 and downsamples to the requested still dimensions. The self-contained `source/preview-bundled.html` opens to the source frame; `drawFrame(2)` and `drawFrame(3)` select the other studies. Input and output hashes, crop rectangles and browser version are recorded in `styleframe-manifest.json`. The render uses installed Node/Chrome and system sans, with no added packages or redistributed fonts.
