# 2026-09-08 — Hippodrome Scout + Golden Horn crossbow belong to the player

Live report (Byzantine Macedonian, screenshots 05:50 / 15:14): Relic was
driving **Разведчик с ипподрома** and the three **арбалетчики** that popped
out of Golden Horn Tower (`building_landmark_age2_galata_tower_byz_ha_mac`).
Both are free landmark gifts. The player wants them locked.

## What was wrong

1. `isScoutLike` / `ecoTypes` treated `scar_hippodrome_scout` as Relic's
   starting scout. Empty spawn name + that type cleared pending and never
   retried. Group-select fallback still keyed on `dummy_champion_scout` /
   `hippodrome_scout`.
2. Earlier "exclude any champion leaf containing `scout`" inverted the
   request: not locking = Relic keeps the unit. Tests encoded that inversion
   (`ids == [62]` while the name said "stays with the player").
3. C++ `dummy && !dummy_champion` dropped Golden Horn dummy crossbowmen from
   `plan.lock`. `WorldLooksLikeServiceBlueprint` did the same for
   `free_dummy` without `dummy_champion`.

Starting `unit_scout_1_*` / `scar_scout` stay with Relic (known lock crash
class). Combat math still classifies the champion scout as `Skip` (200 HP /
5 dmg) — ownership and army composition are separate.

## Riddari (same match, 23:41)

Hippodrome dummy cavalry carries `scar_scout` on the PBG. A riddari leaf
that is not `dummy_champion` / `unit_champion_` (`unit_dummy_riddari_*`,
empty spawn name + `scar_knight`/`scar_riddari`) was read as a scout and
`LockOneSid` logged `skip-eco`. Same gift family as the scout: lock to the
player. `riddari` / `scar_riddari` / `scar_knight` / `scar_horseman` now
beat the scout type for **standing scan** (AI off, 4CE0). Relock
`LockOneSid` after Enable must still refuse `scar_scout` /
`scar_hippodrome_scout` — that is 4A70 / `rva=0x2A45959` (03:03:05). See
[riddari-relock-2A45959](2026-09-08-riddari-relock-2A45959.md).

## Fix

Name + type: Hippodrome champion family, `hippodrome`+`scout` (not
`unit_scout_`), `scar_hippodrome_scout`, `galata` / `golden_horn`, and
dummy+crossbow/arbalet lock to the player. Service dummies (minimap /
preview / ghost / dummy_start) stay out.
