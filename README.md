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
  static modifiers), including the `default_values.txt` script values referenced above.
- `.metadata/metadata.json` — Steam Workshop mod metadata (name, supported game version, tags).

## Status

Imported as-is from the Workshop upload. Bug fixes and adjustments on top of the original mod
will be tracked here going forward.
