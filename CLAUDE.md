# CLAUDE.md

Context for Claude working in this repo. Read it before changing anything.

## Working with Jeroen

- Answers: **concise and conversational**. Short replies, no walls of text, no recaps.
- Wants things to just work: build it, test it, give the link. Ask only when a decision is really his.
- Prefers **visual** over written deliverables (brand guide as boards, not a document).
- Netherlands-based, Dutch-speaking, chats in English. His own gear: Hario V60, Fellow Ode Gen 2, Fellow Stagg EKG.

## This repo

- GitHub Pages site for **jbaars.com** (see `CNAME`). Branch `master` deploys.
- Root is a built Vue site (`index.html`, `about.html`, `static/…`). Don't touch it unless asked.
- `coffee/` is **drawdown**, the coffee app → **jbaars.com/coffee/**.
- `_config.yml` keeps this file out of the published site.

## drawdown: the app

A pour-over brew log for iPhone, used from Safari / home screen.

Features: setups (brewer, hand or electric grinder, kettle, filter); beans (scan a bag photo or add by hand); brew log (dose, water, auto ratio, grind, temp, bloom, time, 1–5 stars, taste tags, notes); ring timer with pour plan; "Brew again"; Journal with All / Top rated and best recipe per bean; next-brew advice (AI, or rule-based fallback); grinder-aware grind sliders.

### Code

- One file: `coffee/index.html` — vanilla JS, no build step, no dependencies. Plus `manifest.webmanifest` and `assets/` (icons, mark SVGs).
- **Storage adapters:** `cloudStore` (Claude artifact `db`, per user at `data/users/<id>`) when `window.claude` exists; otherwise `localStorage` key `brewlog-v1`. On jbaars.com there is no `window.claude`, so data is **per device/browser only** and AI is off (UI says so).
- Docs in one collection, `kind`: `setup` | `bean` | `brew` | `prefs`. `prefs.plan` is the recipe queued on the Brew screen; cleared after logging.
- `curPlan()` priority: saved plan → last brew's advice → last brew → starter recipe from the grinder's V60 start.
- `pourPlan()`: bloom + 3–4 pours, 30 s apart after bloom.
- **Grinders:** `GRINDERS` table, 56 models. `kind`: `steps` (numbers/clicks), `ode` (Fellow 1–11 with .1/.2), `rot` (1Zpresso rotation.number.tick), `text` (typed; notation we don't model). `po` = pour-over range from the Honest Coffee Guide chart; V60 zone = finer 57% of it (400–700 of 400–930 µm); start = middle of the V60 zone; `nudge` = clicks for a noticeable change. Functions: `gIdx`, `gStr`, `gZone`, `matchGrinder` (name → model, longest alias wins), `shiftGrind`.
- **AI** (only inside Claude): `sample` capability, resolved once at boot into `AI`. The first AI call shows Claude's consent prompt and **must run synchronously inside a tap** — that's why scanning is photo → preview → "Read label" button. Prompts always include the grinder's notation (`grindNote`).
- Motion: CSS springs as `linear()` curves (`--spring-soft/bounce/snappy`). Press feedback 97 % / 100 ms ease-out on pointer-down; no bounce on taps; sheets drag-to-dismiss with velocity hand-off and 0.55 rubber band; reduced motion = 200 ms cross-fades.
- Mobile rules applied (Emil Kowalski's `mobile-native` / `apple-design` skills): `viewport-fit=cover`, `interactive-widget=resizes-content`, `touch-action: manipulation`, no text selection on controls, `overscroll-behavior`, safe-area padding, 16 px+ inputs, never disable zoom.

### Testing

Headless Chrome via Playwright (`/usr/bin/google-chrome`). Seed `localStorage['brewlog-v1']`, drive the UI, check `pageerror`. For AI flows, inject a mock `window.claude.use('sample')` and assert `navigator.userActivation.isActive` is true when the AI is called. Check `node --check` on the extracted script after edits. Serve over `python3 -m http.server` (not `file://`) for the web version.

### Other copies

- Claude artifact version (has AI + sync): https://claude.ai/artifact/A1N7rxVWZPAmmUSiBfMACf — it's set to **public**, which Claude can't republish; the latest code (photo fix, v2 look) only reaches it after sharing is switched to named people. Public viewers likely get no AI/sync.
- Brand guide (visual canvas, v1 + v2 pages): https://claude.ai/artifact/NzecqXwt3om82y1k3cggAa
- Design system (tokens, components, logos): https://claude.ai/artifact/J9SQ29AQ8473czVeNMazoY

## Brand: drawdown v2 (mono) — current

Inspired by the *feel* of the beean app (black, italic serif titles, square, outlined). Never copy beean's or People Possession's names, logos, colours or layouts. v1 used orange; Jeroen rejected it ("a bit Strava").

- **Name:** drawdown, always lowercase.
- **Mark:** a lowercase d drawn as one pour — kettle stream falls and spirals into the bed. Milk on black, black on milk. Lockup = mark + "drawdown" in Instrument Serif italic. App icon: milk mark on black (`coffee/assets/`).
- **Colour:** black `#000000` ground · `#121212` panels · `#1c1c1c` inside sheets · `#2a2a2a` tracks · `#3a3a3a` hairlines · `#8c8c8c` secondary · `#5e5e5e` inactive · milk `#f4f2ec` text. **No accent.** Only hue: water `#9db8dc` (deep `#2e3a4a`), only for water. Muted taste tones only on cup labels.
- **Type:** Instrument Serif italic for titles (sentence case) · Geist for UI (regular/light, never bold; uppercase labels +0.04em) · Geist Mono for brew codes.
- **Shapes:** square everything (0 radius except the app icon). Primary = one solid milk block per screen; secondary = 1.5 px milk outline; icon buttons = outlined squares; rows with full-width hairlines, light-weight values, underlined "Change" links; tab bar = four uppercase words, no icons.
- **Brew code:** `15/250 · G4.1 · 94° · 3:00 · ★4` (dose/water · G + grinder notation · °C · time). Brew numbers `BREW 0042`.
- **Cup label:** per brew; taste-colour blocks on top, serif italic bean name, brew code, stars.
- **Voice:** short, specific, a bit cheeky, never snobby. Units always. Verb-first buttons. No exclamation marks, no emoji.

## Open items

- GitHub pushes from Claude are blocked until the Claude GitHub App is installed for this repo.
- AI photo reading + sync on jbaars.com would need a small backend (Claude API key + database).
- Ideas not built yet: grind converter between grinders, water-by-TDS guide, cup-label share cards.
