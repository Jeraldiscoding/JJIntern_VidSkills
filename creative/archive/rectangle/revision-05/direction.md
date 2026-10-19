# Revision 05 — source label and logo only

17 October 2026. The latest user instruction is: “just put the jjintern logo, the surce just put microsoft swe internship”.

The source frame now contains only **Microsoft** and **SWE Internship**, arranged on a plain white tile. The receiving frame contains only the original JJIntern logo. The photo, career illustration, browser labels, domain, programme headings, receiving feed and accompanying JJIntern text are removed. The packet and pale blue background are unchanged.

The source is a user-requested editorial role label. It is not an employer screenshot or verified current vacancy. There are no dates, eligibility details, posting events, intake promises, application controls or other role facts. The destination no longer serves as authentic feed proof; the journey is an abstract internship-discovery-to-brand metaphor.

## Assets and checks

Only `../../../assets/evidence/product/logo-mark.png` is used: the original 512×512 transparent PNG, drawn intact at 420×420 without recolouring, tracing, distortion or cropping. Its transparent padding is accounted for in optical centring. No employer or product screenshots are included in this revision.

The three actual style frames are `styleframes/01-source.png`, `02-packet.png` and `03-logo.png`, all 1080×1920. The approval board includes captions outside the film frames; the phone board is a digital 360px-per-frame equivalent. Input/output hashes and renderer details are in `styleframe-manifest.json`. The unchanged packet is byte-identical to revision 04.

To reproduce, start a dedicated temporary Chrome profile with debugging port 9354 and run:

```sh
node creative/archive/rectangle/revision-05/source/render-styleframes.mjs 9354
```

The offline Canvas renderer evaluates at 2160×3840 and downsamples to the PNG deliverables. No packages or fonts are added.

## Remaining story and production

The confirmed flight remains 4.500–6.500 seconds, arriving at 6.500, within an 18.000-second film. The packet now resolves into the original brand mark rather than expanding into a feed. Exact payoff remains “Found.”, followed by “We handle the finding. / You focus on applying.” The final 15.000–18.000 sign-off remains “JJIntern” alone under the original brief; this revision changes the receiving frame.

Historical status at the time these stills were produced: animation and audio awaited style-frame approval. The subsequent attached user brief expressly approved revision 05 and authorized a motion test followed by full production. The completed animation, original score, reproduction commands and review status are recorded in [production-notes.txt](production-notes.txt). No publishing was performed.
