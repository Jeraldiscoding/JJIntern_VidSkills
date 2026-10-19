# JJIntern Videos

Creative direction, brand assets, reproducible motion projects and revision history for JJIntern.

## Start here

- **[Watch the latest video](creative/projects/discovery-packet/revision-11/JJIntern-revision11-60fps.mp4)** — discovery packet, revision 11.
- **[TikTok caption](creative/projects/discovery-packet/revision-11/tiktok-caption.txt)** — ready to copy.
- **[What our videos should feel like](creative/CREATIVE-DIRECTION.md)** — owner preferences, accepted examples and rejected approaches.
- **[Current project](creative/projects/discovery-packet/README.md)** — master, source, score, timing and review.
- **[Creative library](creative/README.md)** — product evidence, brand, briefs and production guidance.

## Folder map

```text
JJIntern_Videos/
├── README.md
├── AGENTS.md
├── .gitignore
├── .agents/skills/             Project skills
└── creative/
    ├── CREATIVE-DIRECTION.md   What we want and what we reject
    ├── projects/              Current and future video projects
    │   └── discovery-packet/
    │       ├── README.md
    │       └── revision-11/   Video, caption, source, audio and review
    ├── archive/               Earlier films, experiments and revisions
    ├── assets/                Original brand assets and shared captures
    ├── brand/                 Identity and marketing treatments
    ├── product/               Product facts and evidence
    ├── claims/                Claim records
    ├── briefs/                Concept briefs
    ├── playbooks/             Production workflows
    ├── references/            Inspected examples and rejected patterns
    ├── qa/                    Reviews and publication/learning records
    ├── examples/              Initial company-search proof
    ├── scripts/               Shared capture, render and validation tools
    └── maintenance/           Folder-migration record
```

## Working on a video

Use a descriptive project folder under `creative/projects/`. Keep its brief and navigation in `README.md`, then group each revision's deliverables, `source/`, `audio/`, `stills/` and `review/` together. Point the project README to the current accepted revision. Older work belongs in the archive with its dependencies and history retained.

The current film's [production notes](creative/projects/discovery-packet/revision-11/production-notes.txt) contain reproduction commands. Run shared documentation and evidence checks from the repository root:

```sh
python3 creative/scripts/validate-system.py
```

The `.gitignore` excludes local metadata, caches and credentials. It intentionally retains `.agents/skills`, creative assets, videos, audio and review evidence. This folder organization does not publish anything to GitHub or social platforms.
