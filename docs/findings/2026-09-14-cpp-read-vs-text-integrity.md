# 2026-09-14 — C++ read vs `.text` integrity

User: чтение игры через C++ не запрещено; запись бьёт integrity **в `.text`**.

## Rule

| Access | Overlay |
|---|---|
| C++ **read** Relic sim / heap (radar, `AI+0x1000` tracking map, health) | First-class. Already `OffsetsReadBytes`. |
| C++ **write Relic `.text`** | Hasher / integrity. `OffsetsWriteBytes` refuses `.text` and any executable page. Patch Game already no Relic `.text`. |
| C++ **write Relic data** (heap `tracking+0x40`, lists) | Allowed when ABI is known. Not a substitute for Control / `AI_Enable` slot create. |
| SCAR natives (`AI_LockSquad` 4A70) | Still the crash leaf on unlocked tracking. Do not call 4A70. |

Old comment «RPM read-only, never write `+0x40`» mixed two things: 4A70 native AV, and a fake ban on all C++ writes. Think `0x2923300` **does** skip locked + empty tactic vec. Native 4A70 on that empty row still AVs (`0x2924350` → `[rax+0x58]`). Heap stamp of `+0x40` is the data poke.

## Overlay change

- `OffsetsWriteBytes` — SEH memcpy, refuse Relic `.text` / RX / PAGE_GUARD.
- `StkAiTrackStampLockFlags` — stamp empty unlocked rows before Enable census.
- Live-stack leftover stays WouldStrip for LockSquad skip-map. Enable-true uses empty-unlocked only (`+emptyEn`).
- Stamp `+heapLock`.

Host: `test_offsets_write.cpp`.

## Negative

Do not VirtualProtect Relic `.text` to poke code. Do not poke `AI+0x12F4` as a fake Enable. Do not drain tactic vec from C++ (that is 4A70 strip).
