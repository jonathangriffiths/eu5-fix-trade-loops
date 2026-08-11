# Fix Trading Loops

A patched copy of the EU5 Workshop mod ["Fix Trading Loops"](https://steamcommunity.com/sharedfiles/filedetails/?id=3664872597)
by **Rikkert** (`Rikkerd_01`) — all credit for the original design to them.

**What it does:** removes vanilla's flat trade efficiency bonuses (which enable exploitative
"trade loops") and redirects that value into Trade Income instead.

## What was broken, and fixed here

The original mod tried to add a `trade_income` bonus via `INJECT:object = { trade_income = X }`,
but for ~47 objects (laws, buildings, estate privileges, religions, societal values, etc.) the
real modifier needed to sit *inside* a sub-block (e.g. `country_modifier`), not at the object's
root. Those injections silently did nothing — a straight nerf instead of a redirect. This copy
nests every injection at the correct depth, fixes 4 fabricated target names (and 2 inverted
bonus/penalty signs) in the societal values file, and moves every hardcoded number into
`main_menu/common/script_values/TE2_trade_income_scale.txt` so tuning is a one-line change.

**Second bug (found via the game's `error.log`):** 16 `INJECT:` targets named a law option or omen directly
(e.g. `INJECT:regulated_gold_export`), but the game database only indexes the *top-level* object —
here, the law group (`precious_metal_distribution_law`) or god (`hermes_god`) that contains it — so every
one of these silently failed with `trying to inject/replace to a non-existing entry`. That meant the
original vanilla bonus was still zeroed out by `default_values.txt`, but the trade_income compensation
never landed: a straight nerf with no offset, for every affected law and the `giver_of_wealth_omen`
Hellenic omen. Fixed by nesting each injection under its real top-level parent
(`in_game/common/laws/TE2_*.txt`, `in_game/common/gods/TE2_hellenism.txt`).

## How to verify it's working

Easiest check, no setup needed: open the country modifier breakdown and look at the
**Aristocracy vs Plutocracy**, **Mercantilism vs Free Trade**, or **Latinization vs Hellenization**
societal value sliders — each now contributes a Trade Income modifier. Confirmed working.
