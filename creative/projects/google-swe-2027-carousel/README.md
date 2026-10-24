# Google 2027 Singapore SWE — picture carousel

**Latest: [revision 02 — reported Singapore salary, three concise pictures](v02/README.md).** [Download the revised pack](v02/JJIntern-Google-2027-salary-picture-post.zip) · [Preview](v02/review/contact-sheet.png). The original four-picture version below is retained as history.

## Original version

24 October 2026, Europe/Stockholm. Four manual-swipe pictures, 1080×1350. Current objective: relevant visits to JJIntern and opening this specific role. User requested a new company after Stripe and sales & trading, accurate facts and a website-oriented post.

## Concept selection

Audience: Singapore university students considering software engineering internships. Desired action: visit **https://jjintern.com/feed**, search **Google**, open **Software Engineering Intern, 2027 (English)** and inspect the full details.

| Mechanism | Interest / proof / relevance / product / feasibility (0–2 each) | Decision |
|---|---|---|
| Pay reveal | 2 / 0 / 2 / 1 / 1 | No current official Google salary figure; reject the amount-led premise. |
| Paid 10–12-week programme overview | 1 / 2 / 2 / 2 / 2 | Accurate and relevant, but does not supply as strong a reason to act now. Keep duration/paid context on the cover. |
| Expected date versus possible early closure | 2 / 2 / 2 / 2 / 2 | Selected: an employer-stated timing condition with an exact matching role on JJIntern. Use the early-closure qualification with the date, not a fake countdown. |

These are editorial selection judgments, not predicted views. The owner says Stripe and sales & trading have already been covered; publication analytics and complete prior-post assets were not supplied.

Sequence: recognisable employer/opportunity → explain the time-sensitive condition → quick fit check → genuine product result and explicit website action. Panel 2 pays off the cover; the final panel offers full role details rather than hiding the basic answer. No fabricated salary, guarantee, partnership, eligibility guarantee or direct-to-Google application claim.

## Sources and product evidence

- [Google's official role](https://www.google.com/about/careers/applications/jobs/results/104489346874122950): source for the programme and timing/qualification facts, read 24 October 2026. Claim `OPP-GOOGLE-SWE-SG-20261024` in the [shared ledger](../../claims/ledger.json).
- [Public JJIntern feed](https://jjintern.com/feed): real search for Google and real title click expanded the matching full description. [Capture record](evidence/capture-record.json) records the states, crop and hashes. The application button says **via LinkedIn**; application handoff/submission was not tested. The CTA promises reading details on JJIntern.
- The public role crop is an authentic, unaltered product capture, not a recreated employer interface or independent logo asset. The original JJIntern mark is used at modest size. No people, stock photos, downloaded music or generated employer marks.

## Delivery and reproduction

[Download the picture-post pack](JJIntern-Google-2027-picture-post.zip): four numbered PNGs, caption, alt text and sources. [Preview all four pictures](review/contact-sheet.png).

- [01 — cover](images/01-cover.png)
- [02 — application window](images/02-application-window.png)
- [03 — fit check](images/03-fit-check.png)
- [04 — visit JJIntern](images/04-visit-jjintern.png)
- [Caption](caption.txt) · [Alt text](alt-text.txt) · [Sources](sources.txt)

Upload the numbered PNGs in order. The 360px-per-panel contact sheet is a review aid, not an upload panel. [Final QA](review/final-qa.json) records passed and pending checks; [delivery manifest](review/delivery-manifest.json) records hashes and verified archive contents. Independent factual/visual review found no must-fix issue. Actual phone/account previews remain pending.

Use an isolated Chrome profile and local debugging port. Existing Node/Chrome tools only; no additional packages:

```sh
node creative/projects/google-swe-2027-carousel/source/capture.mjs 9384
node creative/projects/google-swe-2027-carousel/source/render.mjs 9384
python3 creative/scripts/validate-system.py
```

The first command refreshes source captures and must be followed by a factual review and rerender. Capture date literals must be updated for a future refresh; rerunning is not permission to retain an old check date. Rendering uses [source/carousel.html](source/carousel.html); preview HTML embeds exact captured/brand assets. PNGs use a 4:5 house canvas, not an asserted universal TikTok safe area. Physical-phone and account upload-preview checks remain separate.

Test hypothesis: the specific early-closure hook will earn qualified feed visits more effectively than a generic programme introduction. Primary outcome: measured website visits from the post if attribution is available; secondary: Google searches/role opens if those events are actually instrumented. No analytics were installed, no metrics fabricated and no post published. Future variant changes the cover only and retains the same facts/destination.
