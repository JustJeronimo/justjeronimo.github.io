---
name: drawdown
description: Use for any change to the drawdown coffee app (coffee/index.html) or its brand: new features, restyles, copy, icons, share cards. Covers the v2 brand rules, the code map, and the test-then-ship routine.
---

# drawdown

Read `CLAUDE.md` at the repo root first; it has the full context. This skill is the working checklist.

## Before you build

1. Brand source of truth: `drawdown/brand/` (`README.md` brand book, `tokens.json`, `motion.md`, `components/` previews, `logos/`). Live versions: design system https://claude.ai/artifact/J9SQ29AQ8473czVeNMazoY and visual guide https://claude.ai/artifact/NzecqXwt3om82y1k3cggAa.
2. For motion, gestures or mobile polish, use the vendored Emil Kowalski skills in `.claude/skills/` (`apple-design`, `mobile-native`, `gestures`, `animate`, `review-animations`, `break-ui`, `animation-performance`, `emil-design-eng`).

## Brand rules (v2 mono)

- Black ground, milk `#f4f2ec` text, greys for structure. No accent colour. Water blue `#9db8dc` only for water.
- Instrument Serif italic titles · Allo UI (regular/light, uppercase labels) · Geist Mono brew codes.
- Square corners. One solid milk button per screen; everything else outlined (1.5px) or text. Full-width hairlines. Tab bar = BREW · JOURNAL. Brew is a 5-step checklist with the hero timer.
- Brew code `15/250 · G4.1 · 94° · 3:00 · ★4`. Name always lowercase: drawdown.
- Voice: short, specific, units always, no exclamation marks, no emoji.
- Never copy beean's or People Possession's names, logos, colours or layouts. Inspiration only.

## Code map (coffee/index.html)

- Storage: `cloudStore` (Claude artifact db) or `localStorage` `brewlog-v1`; docs keyed by `kind`.
- Plan & timer: `curPlan`, `setPlan`, `pourPlan`, `phases`, `paintTimer` (rAF loop, hero timer). Brew page: `viewBrew`, `flow`, `goStep`, `step*` bodies, `taste`.
- Grinders: `GRINDERS` + `gIdx/gStr/gZone/matchGrinder/shiftGrind/grindRow`. New grinder → add a row with the Honest Coffee Guide pour-over range; use `kind:'text'` unless the dial notation is certain.
- AI (Claude artifact only): `AI`, `askJSON`, prompts `scanPrompt/recipePrompt/advicePrompt` (always include `grindNote`). Any first AI call must start synchronously inside a tap.
- Dial-in: `extraction`, `ruleAdvice`, `starterRecipe`. Grinder images: `gImg`, files from `drawdown/render/grinders3d.py`.
- Bump `APP_VERSION` on every ship.
- v2 look lives in the `/* drawdown v2 · mono */` CSS block; motion in `/* motion */`.

## Ship routine

1. Edit `coffee/index.html`.
2. `python3 drawdown/tests/test_app.py` — must print `ALL PASS`.
3. Look at the screenshots it writes to `/tmp/drawdown-*.png` once.
4. Commit to `master` (that deploys GitHub Pages) and check https://justjeronimo.github.io/coffee/index.html loads.
5. If the Claude artifact copy should match, republish https://claude.ai/artifact/A1N7rxVWZPAmmUSiBfMACf (only possible while it isn't public).
6. Reply to Jeroen in two or three lines with the link.
