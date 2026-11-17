# Motion

Everything that moves in drawdown moves on a spring. Nothing fades linearly, nothing eases in. Motion tells you what happened, then gets out of the way.

## The three springs

| Name | Feel | Duration | Use |
| --- | --- | --- | --- |
| **soft** | Critically damped, no overshoot | 0.59s | Sheets opening, content entering, the page receding, bars filling back |
| **bounce** | Slight overshoot (~4%) | 0.51s | Only when a finger throws something (a flicked sheet). Never for taps |
| **snappy** | Quick, ~1% overshoot | 0.40s | Sheets closing, small settles |

In CSS each spring is a `linear()` easing sampled from a real spring (36 points), with `cubic-bezier(.32,.72,0,1)` as the fallback for older browsers. The exact curves live in the app's stylesheet as `--spring-soft`, `--spring-bounce` and `--spring-snappy`.

## Patterns

- **Press:** feedback on pointer-down: scale to 97% in 100ms ease-out; spring back with *soft* on release. List rows flash `rgba(255,255,255,.09)` while held, with no delay.
- **Tab change:** the tab label settles from 88% with *soft*; the new screen's blocks rise 14px and fade in with *soft*, staggered 25ms apart.
- **Sheets:** slide up with *soft* while the page behind scales to 93% and dims to 60%. Drag the grabber to close: it follows your finger, rubber-bands upward, and closes past 140px or on a quick flick, inheriting the flick's speed. Pulling up rubber-bands with Apple's 0.55 constant.
- **Segmented control:** the thumb slides with *soft*; the content below cross-fades up 8px.
- **Timer:** the ring and clock update every frame. Start gives the ring a small *soft* settle. The current pour bar grows 10% taller and fills live; finished bars dim. A new pour instruction rises in; countdowns tick in place without animating. Reset unwinds the ring with *soft*, then fades the cap.
- **Ratings:** stars settle in sequence, 35ms apart, from 125%.

## Rules

- Respect Reduce Motion: movement becomes a 200ms cross-fade; nothing slides or scales, nothing stops working.
- Never animate something the person is reading mid-pour: numbers that tick (seconds, grams) change in place.
- One movement per moment. If two things spring at once, they share the same spring.
