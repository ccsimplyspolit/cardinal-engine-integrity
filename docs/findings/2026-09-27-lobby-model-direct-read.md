# Reading the lobby by pointer walk instead of scanning (RE findings)

Goal: replace the 36–62 s heap-text scan (see `2026-09-27-lobby-scan-slow.md`)
with a direct read of the game's own lobby model, the way
`LocalPlayerProfileModel` is already read.

## Confirmed: the lobby is a structured K2D UI model

From the RelicCardinal Hex-Rays export (`/k/aoe4_dlc/aoe4/gamesource/reversed`,
dump imagebase `0x7FF7A5500000` — newer than the `0x7FF6F65C0000` in
`native_overrides.cpp`, so RVAs here are not directly reusable):

The lobby / game-setup container model registers these UI properties
(static initialisers in the `0x132Exxx–0x132Fxxx` cluster):

| RVA (dump) | property |
|-----------|----------|
| sub_132DEB0 | `Name` |
| sub_132E5E0 | `PlayerSlots2` |
| sub_132E8A0 | `PlayerSlots3` |
| sub_132EB60 | `PlayerSlots4` |
| sub_132EE20 | `PlayerSlots5` |
| sub_132F0E0 | `PlayerSlots6` |
| sub_132F3A0 | `PlayerSlots7` |
| sub_132F660 | `PlayerSlots8` |
| sub_132F920 | `ContentBaseGame` |
| sub_132FBE0 | `ContentModded` |
| sub_132FEC0 | `WinConditionGameModes` |

Each `PlayerSlotsN` getter returns a **child slot-model pointer read at a fixed
offset in the container**, refcounted (`_InterlockedIncrement(*(slot+16))`):

```
PlayerSlots3 getter (sub_132E830):  v = *(uint64_t*)(this + 160); if(v) ++*(int*)(v+16);
PlayerSlots4 (sub_132EAF0): this + 168
PlayerSlots5 (sub_132EDB0): this + 176
PlayerSlots6 (sub_132F070): this + 184
PlayerSlots7 (sub_132F330): this + 192
PlayerSlots8 (sub_132F5F0): this + 200
```

So the container holds an **array of 8 slot-model pointers at `this+[152..200]`,
stride 8** (slot2 = +152, slot8 = +200). Each pointer is a refcounted slot model
whose own properties (race/civ, steam/profile, rank, name, AI difficulty) are the
per-player data the overlay currently reconstructs by scanning.

This proves the zero-scan path is real: container → slot[i] → fields.

## The PlayerSlot model class (dump offsets, observable caches)

The child slot model registers its properties in the `0x1209xxx–0x120Bxxx`
cluster (getters are lazy K2D observables — they recompute into a cache field
that the lobby UI keeps warm every frame, so the cache offset is readable while
the lobby screen is shown):

| property | getter (dump RVA) | cache/field offset in slot |
|----------|-------------------|----------------------------|
| PlayerProfile | sub_1209820 | sub-object at **slot+208** (0xD0) → SteamID64 / rank live here |
| PlayerName | sub_1209AC0 | string at **slot+320** (0x140) |
| PlayerColor | sub_1209D80 | — |
| PlayerState | sub_120A280 | observable at slot+480 (0x1E0) |
| Team | sub_120A5D0 | int at **slot+584** (0x248) |
| IsAI | sub_120A890 | bool at **slot+657** (0x291) |
| IsLocalPlayer | sub_120B9C0 | bool at **slot+985** (0x3D9) |
| Race (civ) | sub_120BCB0 | value at **slot+1040** (0x410) |

`Race`+`IsAI`+`Team` co-registered here confirm this is the lobby slot model
(cross-checked: `IsAI`@sub_120AA70, `Team`@sub_120A7B0, `Race`@sub_120BE70).
`SteamId`/`Rank`/`Rating`/`ProfileId` are NOT exposed as named UI properties
anywhere in the dump — they are raw fields inside the PlayerProfile sub-object
(slot+208), best read as the raw SteamID64 qword (hi dword 0x01100001).

Caveat: these offsets are from the dump build (imagebase 0x7FF7A5500000) and are
NOT confirmed against the shipped build; treat as candidates to validate live.

## Robust design (build-independent): shape-scan + per-slot mini-scan

Do not hardcode +1040 etc. Instead: (1) shape-scan for the container (8 qwords at
+152..+200 all pointing to refcounted objects) — one match, ~0 false positives;
(2) inside each ~2 KB slot object (and its slot+208 profile), run the existing
cheap checks (SteamID64 qword + civ PBG dword). 8 slots × ~2 KB = ~16 KB scanned
total vs the current multi-GB text sweep. Robust across patches, and it reads AI
slots (which the current scan cannot — `AddAiPlayers` is never called).

## The "better way" for AOE4HOOK

Instead of the steam-text heap scan, find this **one** container object and walk
it. Two levers, cheapest first:

1. **Shape-targeted scan (no fragile global needed).** Scan heap once for an
   object whose `+152..+200` are 8 qwords that are all heap pointers to objects
   carrying a refcount at `+16`. That shape is near-unique — one match, ~zero
   false positives — versus 3–5 M steam-text anchors today. Cache the container;
   re-read every tick with no scan. This is the same "find model by vtable/shape"
   trick already used for the profile model, applied to the lobby.
2. **Global root (fastest, most fragile).** If a static singleton returns the
   container, walk it directly. Needs the accessor found per build from IDA;
   shifts across patches, so gate it behind the shape-scan as a fallback.

Either way the per-slot field offsets (race/civ PBG, SteamID64, rank/ELO, name,
AI flag) still have to be pinned from the slot-model class getters.

## Blocked on: a live trace to finish it safely

- The on-disk dump base differs from the shipped build, and the slot-model class
  is ambiguous to isolate among 488 087 decompiled functions statically (many
  unrelated models also register `Race`/`Name`/`Rank`).
- The reliable way to pin the container root + slot field offsets is a **live
  trace**: with the game in a lobby, find one slot model, walk up to the
  container, read the field offsets from memory, confirm the shape-scan. That
  needs the Cheat Engine MCP bridge running (it was unreachable this session) or
  ida-pro-mcp connected (it failed to connect this session).

## Next step

Bring the game up in a lobby with the CE bridge (or IDA MCP) reachable, then a
live trace can turn this into concrete offsets and a shape-scan that replaces the
heap-text scan outright. Until then the two cost-cuts already shipped
(`DropIsolatedTextAnchors` + `AnchorNear`) stand.
