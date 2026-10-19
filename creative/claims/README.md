# Claims: evidence before emphasis

Owner: JJIntern product owner for product facts; the named researcher for each external claim. Checked: 2026-10-17. Review before every publication.

Use [template.json](template.json) for a new claim and add the completed record to [ledger.json](ledger.json). The template is a working form, not a claim approved for publication. `null` means unknown or inapplicable as explained in its companion status field; it never means zero pay or unrestricted eligibility.

1. Write the precise claim first. Name the employer, exact vacancy or programme, location and intake. A programme overview does not prove an individual vacancy exists.
2. Inspect a primary source. Record its URL, what was actually accessible, the check date, and the passage or section supporting the claim. Search snippets identify leads; they do not establish live availability.
3. Separate existence, eligibility, compensation and current application status. An accessible programme page or an Apply button alone does not prove that applications for a particular year or city are open.
4. For money, record ISO currency, amount, pay period, base versus total, estimate versus employer-confirmed, gross/net if known, location, year and relevant qualifications. Preserve the original period. Annualising a monthly figure is a calculation, never evidence of internship earnings. Do not infer summer earnings from an annualised rate. If a conversion is essential, show the formula and original figure; label FX source/date and exchange-rate variability. Do not combine reports from different locations or years.
5. Put material limitations in the creative where the claim appears. A caption cannot rescue a misleading opening. Use the caption for the full primary link and details that are not needed to understand the hook.
6. Reopen time-sensitive sources on publication day. Record who checked. Check the actual application destination for an availability claim; if inaccessible, keep `unknown` and remove "open", "apply now", deadlines and intake-year language. A dated evergreen explanation can still proceed after the remaining QA gates pass.
7. Attach a private-information-free screenshot or recording if the creative displays proof. Preserve visible employer attribution; never create a mock employer interface or a fake JJIntern listing to fill an asset gap. Record rights/attribution review separately from factual verification.
8. Keep excluded claims in the ledger so another agent does not recycle them. Retire obsolete records rather than silently overwriting their original date.

`editorial_approved` approves only the wording and scope listed in that record. It is not render, rights, accessibility or publication approval. `release_hold` identifies what remains unresolved. Refresh a record by retaining its ID, adding a check-history entry, and updating the evidence and allowed wording together.

The populated GIC record supports an eligibility discovery for university students. Its placement city, intake year, pay and live application status are unknown. Polytechnic students must not be shown as eligible for this university programme without additional primary evidence. [Brief B](../briefs/B-opportunity.md) carries those limits into the script. The Temasek S$12.5k anecdote is explicitly excluded.
