# Fix Trading Loops

A patched copy of the EU5 Workshop mod ["Fix Trading Loops"](https://steamcommunity.com/sharedfiles/filedetails/?id=3664872597)
by **Rikkert** (`Rikkerd_01`) — all credit for the original design to them.

**What it does:** removes vanilla's flat trade efficiency bonuses (which enable exploitative
"trade loops") and redirects that value into `merchant_maintenance_efficiency` instead — a
same-stage replacement that reduces route maintenance cost rather than reintroducing a
sale/purchase-price modifier.

## Trade maths

Ducats flow through three stages, in this order. Each stage is where a different set of modifiers
hits:

**Stage 1 — profit on a single trade route.** Route profit is (sale value received) minus (purchase
cost paid) minus (route maintenance). Three modifier fields hit the sale/purchase side, and one hits
maintenance:

```
Route profit = SaleValue × (1 + selling_efficiency [+ export_efficiency if selling abroad])
               − PurchaseCost × (1 − import_efficiency)
               − TradeMaintenance
```

- **`selling_efficiency`** — "directly impact[s] the price you sell goods to the target market."
  Hits every sale, domestic or foreign.
  Example active from the 1337 start: the **Aristocracy vs Plutocracy** societal value
  (`societal_values/00_default.txt`) grants `selling_efficiency = small_trade_efficiency_bonus` on
  its Plutocracy side.
- **`export_efficiency`** — same side as `selling_efficiency`, but scoped to "exporting goods to a
  foreign market" specifically. Example: the Ottoman/Anatolian-beylik advance
  `crossroads_of_commerce` (`advances/beyliks.txt`) grants it,.
- **`import_efficiency`** — "reduces the cost paid when importing goods from a foreign market," the
  buy-side counterpart to the two above. Example: the **Mercantilism vs Free Trade** societal value
  grants `import_efficiency = small_trade_efficiency_penalty` on its Mercantilism side, which 
  appears in the Age of Reformation.
- All three pull their bonus/penalty size from the same shared script values,
  `tiny…huge_trade_efficiency_bonus/penalty`.
- **`merchant_maintenance_efficiency`** only touches `TradeMaintenance` (base cost `-0.25` per trade
  capacity used), via the same reciprocal formula EU5 uses for army/navy maintenance efficiency:
  `TradeMaintenance_actual = TradeMaintenance_base / (1 + merchant_maintenance_efficiency)`. It never
  touches `SaleValue` or `PurchaseCost`. Example active from the 1337 start: the Merchant Republic
  government reform (`government_reforms/republic.txt`) grants `merchant_maintenance_efficiency = 0.50`.

This stage is where the issues with trade loops arise, because buying and selling a valuable good 
(like Saffron) between two markets with identical prices, but with a sale price modifier, can be much 
more lucrative than trading other goods between markets that do have a price difference. We don't want 
that to be the case!

**Stage 2 — total trade income pool.** All routes' Stage 1 profits are summed into a country's total
trade income. Nothing in this mod touches this stage directly — it's purely the sum of Stage 1
route profits, unaffected by `trade_income`.

**Stage 3 — crown/estate split.** The Stage 2 pool is split between the crown and the estates by
crown power vs. estate power; only the crown's percentage reaches the treasury (the rest accrues to
estates). `trade_income` acts *at this stage*: the game's own trade panel (`trade_summary.gui`)
labels this split "Trade Income Share" and displays it as
`[Player.GetModifierValueNoFormat('trade_income')]` — i.e. the `trade_income` modifier's value *is*
the number shown for the crown's share. So `trade_income` increases the crown's cut of the Stage 2
pool directly, rather than growing the pool itself. `merchant_maintenance_efficiency` doesn't touch
this stage at all (it only ever affects Stage 1's `TradeMaintenance` term).

### Why `merchant_maintenance_efficiency`

This mod redirects the removed value into `merchant_maintenance_efficiency` — Stage 1, the same
stage as the exploit it's compensating for — rather than into `trade_income` (Stage 3). Reducing
route maintenance cost scales with trade capacity actually in use, so a country running many
routes gets a proportionally larger saving than one running few, tying the compensation to trade
activity rather than making it government/playstyle-agnostic. It also never touches `SaleValue` or
`PurchaseCost`, so it can't recreate the same-price-arbitrage loop the mod is fixing.

The reciprocal formula (`TradeMaintenance_actual = TradeMaintenance_base / (1 +
merchant_maintenance_efficiency)`) gives diminishing returns as sources stack — going from 100% to
200% efficiency only moves cost reduction from 50% to 66%, not from 50% to 100% — so there's a
mathematical ceiling on how much any single route's maintenance can be reduced no matter how many
sources apply. These are the tiny/small/medium/large/huge values used and their relative cost 
reductions:

| value | cost reduction (`value / (1 + value)`) |
|------:|----------------------------------------:|
| 0.025 | 2.4% |
| 0.05  | 4.8% |
| 0.1   | 9.1% |
| 0.2   | 16.7% |
| 0.5   | 33.3% |

Though note that returns will diminish the more you stack.

## Why the files aren't all structured the same way

Most objects (~47: laws, buildings, estate privileges, religions, societal values) use a plain
`INJECT:object = { country_modifier = { merchant_maintenance_efficiency = X } }`, nested at the right depth. That's
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

All tunable numbers live in `main_menu/common/script_values/TE2_merchant_maintenance_scale.txt`.

## How to verify it's working

Open the country modifier breakdown and check **Aristocracy vs Plutocracy**, **Mercantilism vs
Free Trade**, or **Latinization vs Hellenization** — each should show a Merchant Maintenance
Efficiency modifier.

For the `REPLACE:` law fixes, confirm no duplicate entries appear, e.g.:

- **Precious Metal Distribution** law (gold/silver producer, e.g. Mali or Castile): "Regulated Gold
  Export" appears once, with Merchant Maintenance Efficiency in its tooltip.
- **Estate Laws → Burghers' Rights** (monarchy with Burghers estate): appears once.
- **Legal System** law (Sunni, Shafi'i school): "Shafi'i" appears once.
- **Tariff Control decree** (Middle Kingdom leader, e.g. China at 1337 start): appears once.

Contrast with a building like Pisa's **Porto Pisano**, which correctly shows both effects combined
in one tooltip (buildings aren't a named-choice list).

For the omen fix: a Hellenic Greek nation's Mercury omen menu should show all 10 omens, with
**Giver of Wealth** including both Selling Efficiency and Merchant Maintenance Efficiency. Check
`error.log` for no `Already exists` entries.
