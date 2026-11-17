# drawdown

A brew log for people who dial in. drawdown tracks your pour-over setups, beans and cups, times the pour, and tells you what to change next.

This is the brand book and design system. Every screen, share card, poster and future feature starts here. Comment on anything you want to change.

## The idea: every cup is a release

Specialty coffee's most interesting brands treat coffee as culture, not as a commodity: each release gets its own artwork, its own name, a crew that cares. drawdown takes that attitude and points it at the one coffee nobody designs for: the cup you make at home on a Tuesday morning.

So every brew you log is treated like a release. It gets a number (`BREW #0042`), a code that tells you exactly how it was made (`15/250 · G4.1 · 94° · 3:00`) and a cup label coloured by how it tasted. The app stays calm and native while you brew; the brand gets loud when there is something worth showing off.

> Reference, not source: the street-culture energy of Paris roaster People Possession was a starting point for the attitude. None of their names, marks, colours, layouts or packaging are used here, and nothing in drawdown should look like theirs.

## Principles

1. **The brew is the hero.** Bean name and numbers lead. Chrome, decoration and our own logo stay out of the way on working screens.
2. **Numbers are beautiful.** Grams, clicks, degrees and seconds are set with care: tabular figures, real units, codes in mono. They are the artwork.
3. **Native while brewing, loud when sharing.** The app follows iOS conventions so it disappears in your hands. Cup labels, share cards and posters get the big serif italic and taste colours.
4. **One solid button per screen.** Everything is outlined or plain text except the single thing the screen is for, which is a solid milk block.
5. **Water is blue, taste has colour.** `water` only ever means water. Taste colours only ever describe a cup. Colour always carries meaning.

## Name

**drawdown**, always lowercase, one word. It is the last phase of a pour-over: the water drains through the bed and you find out what you made. It is also what the app does with your notes: draws them down into the next setting.

- In running text: "drawdown" (lowercase even at the start of a sentence, where possible rewrite so it is not first).
- Never "Drawdown", "DRAWDOWN", "draw down" or "DD".
- The app's home-screen name is `drawdown`.

## Logo

The mark is a lowercase **d** drawn as a single pour: the kettle stream falls and spirals into the bed. The lockup pairs it with **drawdown** set in Instrument Serif italic.

- Milk mark on black (`mark-paper.svg`) by default; black mark on milk (`mark-ink.svg`) on light grounds. No colour versions.
- App icon: milk mark on a black square.
- Clear space: the height of the d's bowl. Minimum: mark 16px, lockup 96px wide.
- Don't recolour, outline, rotate or add effects. The earlier orange files stay in Logos for reference only.

## Voice

drawdown talks like the friend at the bar who knows grind sizes and doesn't make you feel bad about yours. Short, specific and a bit cheeky. Never snobby.

- **Be specific.** Say what to do, with the number. "Grind one step finer (4.1 → 4)." not "Consider adjusting your grind."
- **Units always.** 15 g, 94 °C, 3:00, 21 clicks. Space before g and °C in sentences; none inside codes.
- **Short sentences, active verbs.** Buttons start with a verb: "Log brew", "Brew again", "Suggest next settings".
- **Allowed to have fun in empty states and labels.** Not in errors, instructions or anything someone needs mid-pour.
- **No exclamation marks, no emoji, no "barista-grade", "perfect cup" or "elevate".**

| Moment | Say | Not |
| --- | --- | --- |
| Empty journal | No brews yet. Kettle on. | You haven't logged any brews! Get started now 🎉 |
| Timer, bloom | Pour 45 g so all the grounds are wet. | Begin the bloom phase by gently saturating the coffee bed. |
| Tip | This cup reads under-extracted. Grind one step finer. | Your coffee may be lacking extraction. |
| Error | Couldn't save that change. Check your connection and try again. | Oops! Something went wrong. |
| Top cup | Best cup so far. | Amazing!! |

## Colour

Monochrome. Black ground, milk text, greys for structure. There is no brand accent colour.

- `ground` black, `surface-1` #121212 panels, `surface-2` #1c1c1c inside sheets, `line` #3a3a3a hairlines.
- `text` milk does everything: text, outlines, the one solid primary button. `text-muted` grey for values and secondary lines.
- `water` (soft blue) is the only hue in the app and only ever means water.
- Taste tones are muted and appear only on cup labels.
- Milk theme: the same system inverted, for print, web and share cards.

## Type

| Family | Role |
| --- | --- |
| **Instrument Serif italic** (`serif`) | Titles: tab titles, bean names, posters. Sentence case. |
| **Geist** (`sans`) | The interface. Regular and light, never bold. Labels and tabs in uppercase with +0.04em tracking. |
| **Geist Mono** (`mono`) | Brew codes and brew numbers. |

## Brew codes

A brew code is the whole recipe in one line, in mono:

```
15/250 · G4.1 · 94° · 3:00
```

dose/water in grams · **G** + grind in the grinder's own notation (G21 for 21 clicks, G0.6.7 on a 1Zpresso, G4.1 on an Ode) · water temperature in °C · total time. Add `★4` at the end when rated. A brew number (`BREW #0042`) counts up per person and never resets.

Use codes on cup labels, share cards, in the journal's second line and anywhere a recipe has to be copied exactly. In instructions write the numbers out in sentences instead.

## Cup labels

The signature graphic. Every logged brew gets a label, generated from the brew itself:

- **Colour blocks** in the taste colours of its tags, sized by how many tags fall in each family. A balanced, sweet cup is mostly `taste-sweet`; a sour, thin one goes grey.
- **Bean name** in display capitals, **brew code** in mono, **brew number** and date in small mono capitals.
- Square, on #121212, bean name in serif italic.

No two cups look the same, the same way no two releases do. Labels appear on the brew detail, in Best, and as share cards (1080 × 1350).

## Layout

- Square everything. No radius except the app icon.
- Rows: label above, value below in light weight, a 1px hairline under each. An underlined **Change** link sits right when a value can be edited, an `i` chip beside the label when it needs explaining.
- Panels in #121212 on black; 8px gaps between panels.
- Primary button: a full-width milk block with black text, left-aligned label. Secondary: 1.5px milk outline. Icon buttons: 48px outlined squares.
- Tab bar: four uppercase words, no icons, active in milk, others in faint grey.

## Iconography

Very few icons: back, share, close, chevron, an `i` chip, play and stop. Thin 1.5px line, square ends, inside 48px outlined squares. The tab bar is words, not icons. No emoji anywhere.

## Motion

See the Motion section: critically damped springs, no bounce except where a finger throws something.

## Using this system

- Tokens compile to CSS custom properties (`var(--text)`, `var(--space-4)`, `var(--radius-none)`); themes switch with `data-theme="dark"` or `data-theme="light"` on the root.
- Component styles live in `components/bundle.css` as plain classes prefixed `dd-` (no JavaScript, no React). Each component's preview shows the exact markup to copy.
- Fonts load from Google Fonts (`Instrument Serif` italic, `Geist` 300–500, `Geist Mono` 400); `bundle.css` imports them.
- Logos and icons are in the Logos asset group. Never redraw the mark or set the wordmark in a font.
