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

**Third bug (found via a player report of duplicate law entries):** the fix for the second bug made
those 16 injections succeed, but per Paradox's own documented `INJECT:` behaviour, `INJECT:` *appends*
script to an object rather than merging it by key — see the [Mod structure wiki's `wargoal_scores`
example](https://eu5.paradoxwikis.com/Mod_structure#Inject_and_replace). That's harmless when the
injected key is a plain modifier container (`country_modifier`, `capital_country_modifier`, etc.),
since multiple such blocks on one entity simply sum — which is exactly what makes the ~47-object fix
above safe. It's not harmless when the injected key is itself the *name of an existing, selectable
policy or omen* inside a law/god container: appending a second block with that name creates a second,
visibly duplicate entry in the law/omen choice list (e.g. two identical "Regulated Gold Export"
options), because policies aren't deduplicated by name the way modifier fields are.

Fixed by switching these 14 law objects (and `hermes_god`) from `INJECT:` to `REPLACE:`, which fully
replaces the top-level object instead of appending to it. Since `REPLACE:`/`INJECT:` can only target
top-level blocks (not a nested sub-block), each fix required copying that law/god's complete vanilla
definition into the mod file with the `trade_income` line merged directly into the existing policy's
`country_modifier` — see `in_game/common/laws/TE2_*.txt` and `in_game/common/gods/TE2_hellenism.txt`.
The tradeoff: unlike the rest of the mod, these 14 objects embed a full copy of vanilla content and
will need re-syncing if Paradox changes these specific laws/omens in a future patch.

**Fourth bug (found via a player report of Mercury's empty omen menu):** the third-bug fix copied
`hermes_god`'s complete vanilla `omens` block (all 10 omens) into the `REPLACE:hermes_god` body so
the `giver_of_wealth_omen` change would survive the replace. But omens aren't just a nested field —
they're independently key-checked by the engine's persistent object reader regardless of the parent
god's `REPLACE:`, so redeclaring the 9 *unmodified* omens collided with the copies vanilla's
`hellenism.txt` had already registered. `error.log` showed `Already exists` for all 10 omens
(including `giver_of_wealth_omen` itself), and since every omen in the block failed, Mercury was left
with no omens at all.

Fixed by dropping the 9 untouched omens from the copy (they stay correctly registered from vanilla —
`hermes_god` doesn't need to redeclare them) and adding `REPLACE:` directly on the one nested key that
actually changes: `omens = { REPLACE:giver_of_wealth_omen = { ... } }`. This is a smaller blast radius
than the third-bug fix and only needs updating if `giver_of_wealth_omen` itself changes upstream.

## How to verify it's working

Easiest check, no setup needed: open the country modifier breakdown and look at the
**Aristocracy vs Plutocracy**, **Mercantilism vs Free Trade**, or **Latinization vs Hellenization**
societal value sliders — each now contributes a Trade Income modifier. Confirmed working.

To verify the third-bug fix specifically (no duplicate law/omen entries), check any of these at or
near the 1337 start:

- **Precious Metal Distribution** law (any country producing gold or silver, e.g. Mali or Castile):
  "Regulated Gold Export" should appear **once**, with Trade Income in its tooltip.
- **Estate Laws → Burghers' Rights** (any monarchy with a Burghers estate): "Strengthen Burghers'
  Rights" should appear once, with Trade Income added.
- **Legal System** law for a Sunni country following the Shafi'i school: "Shafi'i" policy should
  appear once, with Trade Income added.
- **Tariff Control decree**, visible to whichever country currently leads the Middle Kingdom
  international organization (China, from the 1337 start): should appear once.

As a contrast, check a *building* like Pisa's unique **Porto Pisano** — it correctly shows as a
single building with both effects (zeroed selling efficiency + Trade Income) combined in one
tooltip, because building modifiers aren't a named-choice list like law policies are.

To verify the fourth-bug fix, follow a Hellenic-religion Greek nation to Mercury's omen menu: it
should show all 10 omens (not empty), with **Giver of Wealth** including both Selling Efficiency and
Trade Income in its tooltip. Also check `error.log` after loading — no more `Already exists` entries
for `messenger_omen`, `golden_wand_omen`, etc.
