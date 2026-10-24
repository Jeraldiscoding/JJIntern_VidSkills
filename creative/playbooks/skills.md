# Invoke and maintain the project skills

Checked **17 October 2026**, Europe/Stockholm. These are local, project-scoped instruction skills; no personal skill folder, global settings, plugin installation or remote service was changed.

## Discovery evidence

Official [OpenAI Docs: Build skills](https://learn.chatgpt.com/docs/build-skills) documents `.agents/skills` under the current working directory and repository ancestors, with a `SKILL.md` containing `name` and `description`. It documents explicit invocation using `$` in Codex CLI/IDE, `@` in ChatGPT, and description-based selection. It says changes are detected automatically, with restart as a fallback. Checked against the fetched page on the date above.

Local `codex --version` reported **0.162.0-alpha.17.2**. The installed skill-creator instructions were inspected, and these five files use their required frontmatter format. **This confirms the documented location, local CLI version and file format; it does not establish that a fresh Codex session has discovered or executed these new skills.** No skill-selection UI or runtime discovery test was performed in this session.

Launch/open the `JJIntern_Videos` workspace (currently `/Users/jeraldlim/Desktop/JJIntern/JJIntern_Videos`), then select a skill if it appears. If a new skill is absent, restart/reopen the session as the official guidance suggests. Do not assume arbitrary Markdown under `creative/` is automatically a skill.

## Choose an entry point

| Skill | Use it for | Local file |
|---|---|---|
| `$jjintern-grounding` | Product truth, brand choices, genuine asset selection | [SKILL.md](../../.agents/skills/jjintern-grounding/SKILL.md) |
| `$jjintern-concepts` | Research, different ideas, hook/payoff and concept selection | [SKILL.md](../../.agents/skills/jjintern-concepts/SKILL.md) |
| `$jjintern-video` | Selected video brief → shot list → rough → inspected export | [SKILL.md](../../.agents/skills/jjintern-video/SKILL.md) |
| `$jjintern-carousel` | A complete manual-swipe sequence and numbered image delivery | [SKILL.md](../../.agents/skills/jjintern-carousel/SKILL.md) |
| `$jjintern-qa` | Evidence, claims, story, artifact and release review | [SKILL.md](../../.agents/skills/jjintern-qa/SKILL.md) |

Only load the detailed playbooks needed for the current work. The skills link back to the shared files; changing a shared rule does not require duplicating it in five places.

**24 October 2026 update:** concepts, video and QA now route salary spotlights and company shortlists/rankings through [career content](career-content.md). For research first: “Use $jjintern-concepts to research Singapore intern-pay and best-tech-company TikToks. Record exactly what you can inspect, verify employer facts and propose hooks; do not produce a video yet.”

## Example prompts and explicit-path fallback

Start a new piece:

> Use $jjintern-grounding and $jjintern-concepts. Develop three distinct concepts for Singapore students who keep reopening company career pages. Choose one using verified public JJIntern behaviour. Write a production brief for a 15–20 second muted-first vertical video, with exact copy, evidence IDs, shot timing and a completed review. Finish useful local work and identify any missing captures.

Produce from a selected brief:

> Use $jjintern-video to produce a local rough from creative/briefs/A-product-demo.md. Recheck the depicted public interaction, preserve real UI, and deliver the rough, transcript, sources and completed QA. Keep phone/upload checks explicit.

If automatic discovery is unavailable in the current host:

> Read .agents/skills/jjintern-video/SKILL.md and follow it as portable project instructions for this task. Use creative/AGENTS.md as the shared entry point.

For a carousel, substitute `$jjintern-carousel` and name the takeaway, platform and requested assets. For review, use `$jjintern-qa` and name the exact script/export paths. Naming a skill does not authorise publishing, spending or production-data changes.

## Validation and upkeep

The normal bundled check is `python3 /Users/jeraldlim/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/NAME`. The available Python environment did not have PyYAML, which that script imports; no dependency was installed just for this check. A narrow standard-library check instead verified the exact two-field frontmatter structure, nonempty values, matching folder/name, valid names, absence of scaffold placeholders, concise length, and local reference paths. This is file validation, not a behavioural or discovery test.

Separately, an independent agent read the QA skill explicitly and applied it to brief A, real captures and the rendered proof. It identified a delayed vacancy qualifier and unspecified placement; both were repaired and rechecked. [Proof review](../qa/proof-review.md) records the inspection limits. This tests the QA instructions in use; it does not prove automatic client discovery or certify all five skills through production.

When editing: keep the trigger precise, preserve required inputs/workflow/output/gates/missing-evidence handling, and move examples into `creative/` rather than expanding every entry point. Revalidate links and frontmatter. After a real failure, correct the relevant shared playbook or narrow skill instruction; do not add overlapping universal rules. The product owner owns product facts and brand decisions; the creative maintainer owns workflow/skill maintenance. Date changes and record material updates in the shared changelog.
