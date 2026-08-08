# Fix Trading Loops

This repository is a local working copy of the Europa Universalis V Steam Workshop mod
["Fix Trading Loops"](https://steamcommunity.com/sharedfiles/filedetails/?id=3664872597)
(Workshop ID `3664872597`), imported so it can be inspected, patched, and fixed up locally.

## Original author

Created by **Rikkert** (Steam username `Rikkerd_01`). All credit for the original design and
implementation belongs to them — this copy exists purely to track local bug fixes and
tweaks on top of their work, not to claim authorship.

## What the mod does

Vanilla EU5 gives buildings/provinces flat **trade efficiency** bonuses (`tiny_trade_efficiency_bonus`,
`small_trade_efficiency_bonus`, `medium_trade_efficiency_bonus`, etc., see
`main_menu/common/script_values/default_values.txt`). High trade efficiency lets merchants sell
goods profitably even when there's barely any price difference between markets, which enables
"trade loops": exploitative, unrealistic trade routes that generate money by exploiting the
efficiency bonus rather than genuine supply/demand differences.

This mod zeroes out those `*_trade_efficiency_bonus`/`*_trade_efficiency_penalty` script values and
redirects the value they used to provide into **profit from trade** modifiers instead, across the
buildings, government reforms, laws, advances, traits, religions, and other systems that granted
trade efficiency in vanilla. Net effect:

- Trade loops built purely around exploiting trade efficiency become unprofitable/less viable.
- Countries still gain the underlying economic benefit, but via profit from trade rather than a
  mechanic that trivializes distance/price differences.
- Markets that were previously propped up by loop exploitation may depreciate once the fix is
  in effect.
- Early game trade income becomes less "free" and more tied to real, sustained trade with
  temporary imports during construction phases.

The mod is intended to be save-compatible — it can be toggled on/off without corrupting saves.

## Layout

Files mirror the game's own mod folder structure and are grouped by the two contexts EU5 mods
load into:

- `in_game/common/...` — gameplay data loaded during a running game (advances, building types,
  estate privileges, government reforms, gods, laws, parliament issues, religions, societal
  values, subject types, traits).
- `main_menu/common/...` — data loaded at the main menu / game setup stage (script values,
  static modifiers), including the `default_values.txt` script values referenced above and the
  `TE2_trade_income_scale.txt` tuning file described below.
- `.metadata/metadata.json` — Steam Workshop mod metadata (name, supported game version, tags).

## Fixes on top of the original upload

The Workshop version zeroes the vanilla `*_trade_efficiency_bonus`/`penalty` script values (this
part works) but tries to compensate every affected object with a `trade_income` bonus via
`INJECT:`. `INJECT:` can only add a key at the *root* of the named object — it cannot reach into
a sub-block. Roughly a quarter of the affected objects (laws/policies, buildings, estate
privileges, subject types, religions, societal values, traits, government reforms, parliament
issues, one god) define their modifier inside a named sub-block (`country_modifier`,
`capital_country_modifier`, `definition_modifier`, `subject_modifier`, `left_modifier`/
`right_modifier`, `modifier`, `modifier_when_in_debate`). The original mod injected `trade_income`
as a sibling of that sub-block instead of inside it, so the compensation silently never applied —
net result was a flat nerf on those objects rather than a redirect (the `porto_pisano` building
is the case a Workshop comment flagged, but the same bug affected 47 objects). Four societal-value
injections also targeted object names that don't exist in the game files at all (e.g.
`aristocracy_vs_plutocracy_right_modifier` — the real object is
`aristocracy_vs_plutocracy = { right_modifier = {...} }`), so those did nothing; two of those four
also had the bonus/penalty sign backwards relative to what they were replacing.

This copy fixes all of that: every `INJECT` now nests `trade_income` at the same depth as the
vanilla modifier it replaces, the four fabricated targets have been retargeted to their real
objects (and the two inverted signs corrected), and all hardcoded magnitudes have been replaced
with named constants (see below). Verified against the base game files: all 174 injected objects
resolve to a real vanilla object, place `trade_income` at the correct nesting depth, and no
hardcoded numeric literals remain in any `INJECT` block.

## Tuning

All magnitudes live in one place: `main_menu/common/script_values/TE2_trade_income_scale.txt`
defines `tiny/small/medium/large/huge_trade_income_bonus` and their `_penalty` counterparts
(mirroring vanilla's own trade-efficiency tier scale), plus `scaled_trade_income_penalty` for the
one auto-modifier case that used a non-tiered vanilla value. Every `INJECT` block across the mod
references one of these named constants instead of a literal number, so rebalancing a tier means
editing one line instead of hunting through ~50 files.

## Testing (England is a good candidate — no country-specific content required)

Most of the fixed nested cases are generic laws/estate privileges available to any country:

- Adopt the `regulated_gold_export` law (socioeconomic law category, crown estate) or the
  `noble_patronage` burghers estate privilege, then check the country modifier tooltip for a
  "Trade Income" entry. Before this fix, adopting these did nothing; now they should show the
  compensating trade income bonus.
- England's own `navigation_acts` advance was already correctly scoped in the original mod
  (trade income sits at the advance's root, which is valid there), so it's unaffected by this bug
  — useful as a baseline/control to compare against the previously-broken cases above.
- `porto_pisano` (the building named in the original bug report) requires Pisa specifically, so
  it's not reachable as England — inspect `in_game/common/building_types/TE2_unique_buildings.txt`
  directly, or verify in a Pisan/Italian game instead.

## Status

Imported from the Workshop upload, then patched locally to fix the `INJECT` scoping bug described
above and to centralize tunable values. Further adjustments will be tracked here going forward.
