# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

"伤口.DEV" — a personal portfolio website for a surveying/mapping engineering student. Deployed at [ssbuxi.top](https://ssbuxi.top). Multi-page static site built with Vite + TypeScript, with a Flask comments API backend. No frontend framework — vanilla JS/TS DOM manipulation only.

## Commands

```bash
npm install          # Install dependencies
npm run dev          # Dev server at localhost:5173 with HMR
npm run build        # tsc type-check + vite build → dist/
npm run preview      # Preview production build locally
```

Build script runs `tsc && vite build` — TypeScript errors will block the build. No linter or test framework is configured.

## Architecture

**Multi-page app, not SPA.** Vite bundles 7 HTML entry points defined in [vite.config.ts](vite.config.ts). CSS code splitting is disabled.

**Three-layer frontend:**

1. **HTML pages** — Each `.html` file contains its own nav, loading screen, inline `<script>` blocks for page-specific interactivity (clock, scroll progress, parallax, comment CRUD, copy email). Pages share a consistent layout pattern.

2. **Vanilla JS** (not bundled by Vite, loaded via `<script>` tags) — [theme.js](theme.js) (dark/light toggle, localStorage), [animations.js](animations.js) (page transitions, lazy loading, scroll animations), [comments.js](comments.js) (two implementations: CommentSystem for Gitalk/GitHub Issues OAuth, SimpleCommentSystem for localStorage fallback — only SimpleCommentSystem is initialized).

3. **TypeScript modules** (bundled by Vite) — Two entry points:
   - [src/pages/index.ts](src/pages/index.ts) — Home page: wires up particles, contour animation, typing effect, fade-in, edit mode (modal login, DOM cleanup before GitHub sync)
   - [src/pages/main.ts](src/pages/main.ts) — All other pages: wires up particles, fade-in, edit mode (prompt-based login)

   Feature modules in [src/modules/](src/modules/): `particles.ts` (canvas particle network), `contour.ts` (marching-squares topographic contours with fBm noise), `typing.ts` (typewriter effect), `fadeIn.ts` (IntersectionObserver scroll reveals), `editMode.ts` (admin inline editing with GitHub API sync).

**Config & types:** [src/config/constants.ts](src/config/constants.ts) exports env vars (`VITE_ADMIN_PWD`, `VITE_GH_TOKEN`, `VITE_GH_OWNER`, `VITE_GH_REPO`). Note: `VITE_GH_TOKEN` is stored base64-encoded in `.env` and decoded with `atob()` at runtime. [src/types/index.ts](src/types/index.ts) defines shared TypeScript interfaces (Particle, EditModeConfig, GitHubSyncPayload, etc.).

**Path alias:** `@/*` maps to `src/*` (configured in [tsconfig.json](tsconfig.json)). TypeScript target is ES2020, strict mode enabled, `noEmit: true` (Vite handles bundling; `tsc` only type-checks).

**CSS architecture:**
- [style.css](style.css) — Global design system: CSS custom properties (dark/light themes via `[data-theme]`), typography, nav, cards, animations, responsive breakpoints. ~1850 lines.
- [index.css](index.css) — Home page hero section styles.
- [life.css](life.css) — Life page warm-color scheme (orange/coral palette).
- [media-tool.css](media-tool.css) — Purple accent overrides for media tool detail page.

## Key Patterns

**Edit mode:** Click logo 5x → enter admin password → text becomes contentEditable → save pushes modified HTML to GitHub Contents API via PUT. The HTML source files are the content store — no CMS.

**Comments:** [index.html](index.html) makes fetch calls to `/api/comments` (Flask backend on the server, stores to flat JSON file at `/var/www/comments.json`). The Flask server is [server.py](server.py).

**Canvas animations:** `particles.ts` and `contour.ts` render to `<canvas>` elements. Contour uses marching squares algorithm with fractional Brownian motion noise for organic topographic lines.

**CSS design tokens:** All colors, spacing, and typography use CSS custom properties defined in [style.css](style.css). Core palette: `--ink` (dark bg), `--amber` (gold accent), `--cyan` (secondary accent), `--ash`/`--fog` (text colors). Font scale uses 1.25 ratio.

**Theme switching:** [theme.js](theme.js) persists preference to `localStorage` and respects `prefers-color-scheme`.

## Deployment

- **Primary:** Alibaba Cloud server (Nginx) at ssbuxi.top. Build then `scp -r dist/* root@8.138.173.71:/var/www/html/`
- **Secondary:** GitHub Pages via GitHub Actions — push to `main` triggers auto build + deploy

## Standalone Tools

[tools/](tools/) contains Python desktop apps (GIS converter, social media scraper) unrelated to the website build. They are showcased on the site but have their own dependencies (`tools/requirements.txt`).

[resume/](resume/) is a standalone HTML resume page with self-contained styles, not part of the Vite build.

[dy工具/](dy工具/) is a Douyin (抖音) video comment scraper with PyQt5 GUI. Built with Playwright (Edge browser automation) + openpyxl (Excel export). Key flow: launch Edge → load/check cookies → login if needed (user scans QR code, clicks "确认登录") → navigate to video → intercept comment API responses + scroll to load more → export to Excel. Entry point: `python main.py`. Dependencies: `pip install -r requirements.txt && playwright install msedge`.
