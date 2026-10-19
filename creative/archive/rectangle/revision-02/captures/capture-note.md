# Authentic light-feed capture

Checked **17 October 2026, Europe/Stockholm** at https://jjintern.com/feed in a fresh isolated, logged-out Chrome profile on port **9356**. All production PNGs are **1720×3360**, captured at **430×840 CSS pixels, 4× DPR**. No personal account or employer handoff was used. The owned capture browser has been closed.

1. Captured the fully loaded **All roles** feed in dark mode.
2. Clicked the real **Switch to light mode** button using pointer press/release events. The root class changed `dark` → `light`; body background changed `rgb(11,11,12)` → `rgb(255,255,255)`.
3. Clicked the real **Tech** category and observed the loaded filtered results. Search remained empty.
4. Scrolled the real document to **scrollY=100**. The site's existing sticky header and filter controls remained visible; aggregate metrics naturally left the viewport.

**Selected:** `feed-light-tech-scrolled.png`. Revision 02 uses contiguous crop **[0,0,1720,2274]**, retaining the site header, selected Tech controls and complete Tencent, DBS and SAP rows. Preserve this crop's natural proportions. No page content, colours, layout, dates, rows or marks were edited or recomposed.

`feed-dark-before.png` and `feed-light-all.png` document the theme change. `feed-light-tech.png` is the settled unscrolled Tech alternative. `feed-light-tech-loading.png` preserves an actual transient loading observation and is **not a production asset**. The capture script's readiness check was corrected after initially seeing stale pre-filter row text.

These captures verify the observed public theme toggle and Tech filtering only. They show existing site data, not a newly ingested Microsoft vacancy, measured detection speed, complete coverage or employer-confirmed availability. No account, application, notification or product-data write occurred.

`capture-record.json` records actions, visible content, styles, bounds, viewport, scroll and screenshot hashes. `manifest.json` hashes the package. `capture-feed-light.mjs` reproduces the public interaction in an explicitly supplied isolated Chrome session; `capture-note.txt` retains fuller operational notes.
