# Dashboard Visual Assets

## `dashboard-nyc-skyline.png`

This is the staff dashboard hero skyline used behind the greeting banner.

- **Purpose:** Soft background art for the Golden Rose staff workspace home dashboard. It should read as a warm illustrated view of the Manhattan skyline with the Brooklyn Bridge, matching the GPT-created dashboard design artifacts rather than a geometric placeholder.
- **Source of truth:** The user-provided dashboard mockups and screenshot snippets from September 15, 2026. The art is intended to reproduce the feel and placement of those concept images while staying usable in the live React dashboard.
- **Creation path:** Generated as a raster illustration with ImageGen from the supplied dashboard design references, then locally post-processed with `ffmpeg` to remove the checkerboard/background treatment and produce a transparent PNG suitable for both light and dark dashboard themes.
- **Current file:** `apps/web/src/assets/dashboard-nyc-skyline.png`
- **Current dimensions:** `1600 x 533` RGBA PNG.
- **Rendering path:** `apps/web/src/dashboard/artwork.tsx` exposes `SkylineArtwork`, `apps/web/src/dashboard/Dashboard.tsx` places it inside `.dashboard-skyline`, and `apps/web/src/styles.css` attaches this PNG through `.skyline-artwork`.
- **Placement note:** The asset includes intentional transparent padding. The live Chrome-calibrated position is controlled in CSS with `background-position: center -0.85rem`; do not remove or crop the asset padding without retesting in an actual Chrome browser.
- **Theme behavior:** Light mode uses `mix-blend-mode: multiply` and dark mode uses a lower-opacity `screen` treatment from `apps/web/src/styles.css`.

If this asset is replaced, preserve the transparent PNG/alpha workflow and verify the header in a real browser, not only the in-app preview, because Vite/browser style injection can retain stale placement during rapid iteration.
