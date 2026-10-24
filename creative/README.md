# JJIntern creative operating system

A small production system for useful student-facing videos and manual-swipe carousels: verified product facts → different ideas → selected concept → purposeful execution → evidence-based review.

**Start with [AGENTS.md](AGENTS.md).** For the next video, invoke `$jjintern-grounding`, `$jjintern-concepts`, then `$jjintern-video`; use `$jjintern-qa` on the script/export. For carousels, use `$jjintern-carousel`. [Skill invocation and fallback](playbooks/skills.md) explains the supported `.agents/skills/` location and what has actually been tested.

## What is ready

| Need | Read / use |
|---|---|
| Product truth and feature boundaries | [Product brief](product/brief.md), [evidence register](product/evidence.md) |
| Actual identity and proposed marketing rules | [Brand guide](brand/guide.md), [machine-readable tokens](brand/tokens.json) |
| Specific techniques to adapt | [Inspected references](references/library.md), [rejected patterns](references/rejected.md) |
| Find a different idea | [Story directions](playbooks/directions.md), [concept selection](playbooks/concept-selection.md) |
| Salary hooks and best-tech-company lists | [Career content playbook](playbooks/career-content.md), [TikTok study and Stripe source](references/tiktok-career-study-2026-10-24.md) |
| Exact language and claims | [Copy guide](playbooks/copy.md), [claim rules](claims/README.md), [ledger](claims/ledger.json), [new-record template](claims/template.json) |
| Produce / export | [Video](playbooks/video.md), [carousel](playbooks/carousel.md), [current platform research](references/platform-guidance.md) |
| Review / learn | [Rubric](qa/rubric.md), [performance workflow](playbooks/performance.md), [post log](qa/post-log.csv) |
| Use completed briefs | [A: actual product search](briefs/A-product-demo.md), [B: sourced GIC discovery](briefs/B-opportunity.md), [C: relatable tab-search situation](briefs/C-student-search.md) |
| Inspect the proof | [12-second rough](examples/proof/company-search-rough.mp4), [contact sheet](examples/proof/contact-sheet.png), [reproduction instructions](examples/proof/README.md), [artifact review](qa/proof-review.md) |
| Maintain | [Ownership, audit and unresolved questions](MAINTENANCE.md), [changelog](CHANGELOG.md), [asset inventory](assets/README.md) |

## Evidence boundaries

On 17 October 2026 this workspace was **empty, with no Git metadata or application source**. No existing campaigns could be inspected. Product and brand evidence therefore comes from public JJIntern HTML/CSS/assets and a logged-out browser. This limitation is retained throughout the system; public marketing assertions are not silently verified as features.

The public **company search was actually tested**: typing Microsoft narrowed the directory to the matching company. Saving/tracking/Telegram are public-site assertions awaiting authenticated tests. Homepage sample roles and board are explicitly illustrative. No product roadmap or planned-feature list was verified. GIC's programme eligibility is sourced; intake, placement city, pay and current vacancy are unknown.

The proof is a reproducible local timing demonstration, with genuine discrete product states and no voiceover, avatar, paid service or new application toolchain. It is not a complete release: physical-phone, platform-preview and final campaign-rights checks remain pending. The reference library names exactly what was inspected; missing native carousel and full short-form story references are labelled as gaps.

## First production choice

**A is strongest for proving this system now:** verified input → changed results → clear company-search payoff → direct next action. C is the stronger candidate for the next attention test because its relatable problem gives the same product proof a narrative entry. B has useful discovery value, but its weaker product connection and missing employer visual captures make it a later execution. None is a promised high-performing post.

## Example future prompt

> Use $jjintern-grounding, $jjintern-concepts and $jjintern-video in this workspace. Create a 15-second vertical JJIntern video for Singapore students who keep losing employer tabs. Compare three distinct ideas, select one before animation, use a freshly verified real product action, and deliver exact copy, shots, a local rough, transcript, sources and completed QA. Read creative/AGENTS.md. Keep unperformed phone and upload-preview checks explicit. Do not publish.

Local validation: `python3 creative/scripts/validate-system.py`. This checks broken links, JSON, skill frontmatter, evidence hashes and material claims invariants; it does not judge taste, verify online freshness or certify release readiness.
