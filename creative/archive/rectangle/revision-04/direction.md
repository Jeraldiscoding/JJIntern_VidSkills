# JJIntern — illustrated careers and original logo, revision 04

17 October 2026. The latest request removes the person/photo from the careers scene, asks for more visual interest than text alone, and replaces the receiving browser with the JJIntern logo. This historical proposal is superseded by [revision 05](../revision-05/direction.md), which reduces the source to the requested role label and the destination to the logo only.

## Visual changes

1. **Careers:** a white programme overview with the genuine “Internship programs” and “Global university internships” heading pixels, plus a simple blue briefcase and document illustration. No person or photograph is rendered. Microsoft Careers and its source domain remain small editorial identifiers. This is an illustrated programme overview, **not an exact screenshot or reproduction of Microsoft's interface**. The illustration has no fabricated vacancy details or interactive controls.
2. **Packet:** the revision 03 data tile is unchanged: three information bars, a blue receiving edge and leftward direction strokes. Its output hash matches revision 03.
3. **JJIntern:** the original transparent logo mark appears intact above the two authentic feed rows. There is no browser bar, address, control dots or enclosing browser outline. The accompanying typeset “JJIntern” is an editorial name label, not a newly claimed official wordmark.

The pale blue background (`#edf3ff`), white surfaces, dark ink and blue graphic accents continue the simple flat direction. The body of the careers scene is now an illustration, with only the necessary programme headings.

## Assets and provenance

- Microsoft headings: P08, `../captures/microsoft-internship-programmes-540.png`, from https://careers.microsoft.com/v2/global/en/students, captured 17 October 2026. Separate source rectangles `[75,232,780,100]` and `[145,995,705,70]` contain the heading/subtitle. They are uniformly scaled and composed around an editorial illustration; they are not a contiguous page screenshot. The photograph and paragraph are excluded. Programme existence is not a claim of an open vacancy.
- Feed: P09, `../revision-02/captures/feed-light-tech-scrolled.png`, from https://jjintern.com/feed. The same contiguous `[0,720,1720,980]` crop retains the full Tencent and DBS rows, source dates, order, tags and controls. No row is inserted or rewritten.
- Logo: `../../../assets/evidence/product/logo-mark.png`, the original 512×512 transparent PNG. The renderer uses the whole square image at 196×196, with original colour, silhouette and padding. Its visible mark is approximately 164px wide. No tracing, recolouring or replacement asset is used.
- The briefcase/document artwork is newly authored Canvas geometry, an editorial career-information symbol rather than employer UI.

Input and output SHA-256 hashes, crop rectangles, palette and rendering host are in `styleframe-manifest.json`. No new product facts, alerts, posting events, intake claims or latency claims are introduced.

## Timing and approval

The film remains 18.000 seconds. The user-confirmed flight is **4.500–6.500 seconds**, with increasing velocity and arrival at 6.500. Exact payoff remains **Found.**, then **We handle the finding. / You focus on applying.** The final 15.000–18.000 sign-off remains **JJIntern** alone. The source programme does not claim to become either displayed feed role.

These are style frames only. The original user brief explicitly says to wait for style-frame approval before animation/audio production. After approval, inspect a causal compression → two-second accelerating flight → direct receiving transition before rendering the complete film. The receiver should reveal the brand mark as the packet expands into the clean feed composition.

## Files and reproduction

`styleframes/01-careers.png`, `02-packet.png` and `03-logo-feed.png` are 1080×1920 PNGs. `approval-board.png` presents all three with captions outside the actual frames. `phone-board.png` presents each frame at 360px width. The native stills and both boards were visually inspected. This is a digital reduced-size check, not a physical-phone or encoded-video check.

Start a dedicated temporary Chrome profile on debugging port 9354, then run:

```sh
node creative/archive/rectangle/revision-04/source/render-styleframes.mjs 9354
```

The dependency-free Canvas renderer draws at 2160×3840 and downsamples to 1080×1920. `source/preview-bundled.html` embeds the verified assets for offline viewing. Installed Chrome, Node and the system sans stack are used; no packages or fonts were added. Review findings are in `review/final-stills-qa.md`.
