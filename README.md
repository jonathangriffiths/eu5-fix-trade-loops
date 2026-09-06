# Fix Trading Loops

A patched copy of the EU5 Workshop mod ["Fix Trading Loops"](https://steamcommunity.com/sharedfiles/filedetails/?id=3664872597)
by **Rikkert** (`Rikkerd_01`) — all credit for the original design to them.

**What it does:** removes vanilla's flat trade efficiency bonuses (which enable exploitative
"trade loops") and redirects that value into Trade Income instead.

## Why the files aren't all structured the same way

Most objects (~47: laws, buildings, estate privileges, religions, societal values) use a plain
`INJECT:object = { country_modifier = { trade_income = X } }`, nested at the right depth. That's
safe because modifier blocks just sum — multiple injections on one entity combine fine.

14 law files and `TE2_hellenism.txt` are different: the actual target is a named policy/omen
*inside* a law group or god object, not the top-level object itself, and `REPLACE:`/`INJECT:` can
only target top-level objects. `INJECT:` on the top-level object would append a second copy of that
policy/omen rather than merging into it, creating a visible duplicate entry. So these files instead
`REPLACE:` the whole top-level object with a full copy of its vanilla definition, with the fix
merged directly into the target policy/omen inside that copy. Tradeoff: these files embed vanilla
content and need re-syncing if Paradox changes those specific laws/omens.

`TE2_hellenism.txt` additionally nests a `REPLACE:giver_of_wealth_omen` *inside* the `omens` block
rather than replacing the whole block, because omens are independently key-checked by the engine
regardless of the parent's `REPLACE:` — redeclaring unmodified sibling omens would collide with
vanilla's own registration of them (`Already exists` errors).

All tunable numbers live in `main_menu/common/script_values/TE2_trade_income_scale.txt`.

## How to verify it's working

Open the country modifier breakdown and check **Aristocracy vs Plutocracy**, **Mercantilism vs
Free Trade**, or **Latinization vs Hellenization** — each should show a Trade Income modifier.

For the `REPLACE:` law fixes, confirm no duplicate entries appear, e.g.:

- **Precious Metal Distribution** law (gold/silver producer, e.g. Mali or Castile): "Regulated Gold
  Export" appears once, with Trade Income in its tooltip.
- **Estate Laws → Burghers' Rights** (monarchy with Burghers estate): appears once.
- **Legal System** law (Sunni, Shafi'i school): "Shafi'i" appears once.
- **Tariff Control decree** (Middle Kingdom leader, e.g. China at 1337 start): appears once.

Contrast with a building like Pisa's **Porto Pisano**, which correctly shows both effects combined
in one tooltip (buildings aren't a named-choice list).

For the omen fix: a Hellenic Greek nation's Mercury omen menu should show all 10 omens, with
**Giver of Wealth** including both Selling Efficiency and Trade Income. Check `error.log` for no
`Already exists` entries.
