# TimerRing

The ring fills toward the target time; the clock sits inside.

- Track `surface-3`, progress `text` (milk), a thin 3px stroke with square ends. Hidden at zero.
- Clock: system font at weight 200, tabular figures, tenths at half size in `text-muted`; `target 3:00` beneath.
- Updates every frame while running; never animate the digits themselves.
