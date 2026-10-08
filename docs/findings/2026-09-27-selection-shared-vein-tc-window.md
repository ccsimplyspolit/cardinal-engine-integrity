# 2026-09-27 — selected villagers, ally-occupied veins, second-TC window

Reports: "Selected villagers stay mine does not work", "ignoring an ally's
occupancy of a vein still does not work", "Ayyubids: the bot did not know
what to do around the age-up". Evidence from today's logs and the
16.3.11308 pseudocode (`K:\aoe4_dlc\aoe4\gamesource\reversed`).

## Selected villagers

Live, `warnings.log` 18:00:35 (Ayyubid): the player picks villager 50075.

```
[STK] sel skip-live sid=50075
[AOE4HOOK_CONTROL SEL] ... 1 50075 END
```

`lockVill` never calls `AI_LockSquad` on a row with a live tactic (4A70), and
`StkAiTrackForceLockEmpty` only stamped a row whose tactic vector was empty.
190 `force-locked empty ... source=selection` lines today: every one an idle
squad. A gathering villager never shows an empty vector, and the pseudocode
says why.

| RVA | What it does |
|---|---|
| `0x296D2E0` `AI_LockSquad` | tracked and `+0x40 == 0` → `0x2924A70`; `+0x40 != 0` → no-op; untracked → queue `0x2924CE0` (`AI+0x3E30`) |
| `0x2924A70` (4A70) | removes every tactic using the squad (`0x2923920`), then appends it to the locked list (`AI+0x10D0`). Another task still holding the removed tactic's id reads NULL in `0x2A45930` → `0x2A45959` |
| `0x2924B40` (unlock) | clears `+0x40`, requests a tactic if the vector is short, drops it from the locked list |
| `0x2923300` (think, per row) | locked + empty vector → skipped; **locked + live tactic → that tactic keeps running**; unlocked + empty → `0x2B2C0A0` assigns the next tactic **in the same pass** |

The last row is the whole problem: the pass that empties a busy villager's
vector refills it, so the stamp never sees it empty.

**Change:** a selection is stamped on a live row too (`+0x40`, heap, nothing
removed). The villager finishes the AI's last order; the think then skips it
and never gives it a new one. Monks keep the empty-row rule (Relic's relic
runners). Each live stamp is logged, and the moment its tactic ends:

```
[STK] C++ force-locked live sid=N source=selection
[STK] selection sid=N handed over: AI tactic ended X s after the stamp
```

Not verified in a match yet: how long a gather tactic runs once stamped, and
whether it re-orders a villager the player moved. The second line answers
the first; if X stays large, the next step is ending that tactic the way
the think does it, not 4A70.

## Ally-occupied veins

Zhu Xi 15:50 (2v2, French ally 100 units away), telemetry: the ally mined the
gold at (-8,176), 136 from our Town Center; our AI opened a camp on (8,36),
187 away. Hybrid already noted that Relic's AIGatheringManager treats an
ally's vein as claimed; the C++ contest that replaced it ignores occupancy but
only ever re-tasks **idle** villagers, and a miner Relic sent to a far vein is
never idle. (`gold_deposit_is_claimed` is the Malian pit-mine flag, unrelated.)

**Change:** `AiSharedVeinPlan` (`ai_shared_mine.h`). Per mineral bucket the
contest wants, the ally-occupied vein nearest to one of our drop-offs (within
40, so no new camp is needed); busy miners of that bucket working farther from
our base than that vein by 25 are moved onto it, farthest first, four per
bucket per pass, each miner at most once per 45 s. Logged:

```
[AI] shared vein: N gold miner(s) moved onto ally-occupied deposit ID
```

The same ids every 45 s would mean Relic takes them back. A vein that needs
a new camp (our drop-off farther than 40) is not handled: Relic places camps.

The clearest case, French 17:08 with an English ally 76 away (telemetry,
villagers within 10 of each vein): the gold (-132,-4), 48 from our capital,
had **our own mining camp 12 away** from 2:00. From 4:00 only the ally mined
it (1-3 villagers) while ours worked (-224,116), 124 out, where Relic built a
second camp and later a second TC. The pull measures from the capital (else
the first TC): the mean of our drop-offs sits out by that far camp and TC and
would not fire. At most eight of ours on the shared vein.

No occupancy flag exists to clear. The deposit state-model schema
(`statemodel_schema/resource_deposit_values.rgd`) carries only
`gold_deposit_is_claimed` (Malian pit mine), `ovoo_is_claimed` and similar;
the AI schemas (`aiplayer`, `aientity`) carry none. Relic's gathering code
decides "ally's vein" natively. `state_model_tree_claimed`, which Hybrid used
to clear on trees, is not in the 16.3 bool registry either. Heap writes from
C++ do not reach the RA hasher (`0x3E57050` hashes code and its ranges; the
`+0x40` stamp runs every 250 ms), so a native flag, once found, could be
cleared from C++ in a match against the AI.

## Second-TC window starved gold

Ayyubid 17:45–17:54 and Zhu Xi 15:54–16:00: `tb=1` and gold `0.00` for 6–9
minutes. The window's split is the unpaid TC bill (wood, stone; gold only for
Malians); with the reserve off under a threat, wood went out as fast as it
came in, the bill never banked, and nothing funded the next age.

**Change:** the window keeps 25% of the base split (45% while spending runs:
threat or MASS) in every resource; no stone for civs whose TC costs none.

Not a bug: the Ayyubid `age_up_queued` 1/0 flips at 17:42–17:47 were the
player cancelling the wing research.

## Verification

Host: `test_ai_eco_goal` (gold above zero in the window, more under a threat,
Mongol still no stone), `test_ai_shared_mine` (vein choice, reach, farthest
first, gold not wanted, not ally-occupied, the French case from the capital,
the eight-miner cap), `test_ai_handover.py` (selection may stamp live; monks
keep the empty rule; no vector drain). MSBuild Release|x64 builds (18:14;
18:35 with the capital pull). In the game: none of the three yet; the 18:36
injection reached only the menu.
