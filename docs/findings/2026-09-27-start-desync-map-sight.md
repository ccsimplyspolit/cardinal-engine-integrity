# 2026-09-27 — start-of-match desync and AI map sight

User reported two consecutive network matches ending in a desync. Local
evidence was read before the next launch rotated the overlay log. Copies of
the four SyncError reports and the second overlay session are in
`K:\aoe4_dlc\analysis\desync-20260927` (not committed).

## Evidence

| Match | Local observation |
|---|---|
| 21:32:55 start, process 53892 | 21:32:56.478: `map sight: fog lifted for player 1000 (all) ... tick=1 copies=2/2`; SyncError at 21:32:57, frame 3, local CRC `31ffea13` (previous frame 2 `99613e09`) |
| 21:36:07 start, process 3904 | All four load checksums `1866426792`; 21:36:07.926: `map sight: fog lifted for player 1006 (all) ... tick=4 copies=2/2`; 21:36:09.136: local station 4 frame 5 CRC `FBDAA27D` vs station 1 `3034E9B0` (previous frame 4 `46d0f1f6`) |

The second game's warning log explicitly reports `network out of sync` and
disconnect reason `OnSyncErrorDetected`. The later `Application crashed`
line is after match teardown; it is not proof of a separate access violation.
No fatal native exception has been established as the initiating event.

`ai_map_sight=2` was persisted. Commit `239683493c` introduced the map-sight
service with All as both the UI and configuration default. Its roster check
was `NativeOverridesOtherHuman() == 1`; an empty, unscanned lobby roster
returns **-1**, which therefore enabled the simulation write. Neither saved
session shows a completed lobby scan before the write. The service is called
from the AI session and writes both world copies.

This is a confirmed faulty gate and a strong explanation of both incidents:
an unsynchronized reveal occurred immediately before each network mismatch.
The local SyncError frames include fog sight/exploration checksums, but they
are adjacent local frames, **not peer dumps**. Their differences alone do not
prove which field first differed between peers. A new network match has not
been run to establish that this was the only possible desync source.

## Fix

- Require roster result exactly **0** before raising map sight. Unknown and
  another human both block the write, with distinct log messages. Existing
  owned reveal cleanup is retained.
- Default to **Only what it scouted** in both configuration and UI. Invalid
  configuration values also go to Off.
- Old settings without `ai_map_sight_policy=1` are migrated to Off at load.
  This removes the former implicit All default even if an old running DLL
  saves its settings again before exit. New saves include the policy marker.
- Explain in the UI that Whole map / Everything are solo-only. The cached
  lobby scan is not an authoritative current-session roster; explicit reveal
  must remain off for network games, including when switching from solo play.
- Correct the header guidance that previously recommended accepting unknown
  rosters for every C++ gate.

No synchronization check is disabled or altered. The corrected path avoids
the local simulation change.

## Verification

New `test_ai_map_sight_service.cpp` links the actual production
`ai_map_sight.cpp`, supplies a synthetic world and stubs reads/writes and the
roster source. It exercises the full service path, not a copied gate.

Before the fix:

```text
FAIL: unknown roster must not touch simulation fog (writes=1 walks=1 reveal=1)
```

After the fix:

```text
map sight service: roster/write regression scenarios passed
```

Cases cover unscanned roster with All and Map, known human, disabled AI/Off,
explicit solo reveal, no repeated write, loss of roster, detection of a human,
and leaving scenario-owned reveal alone. Added to `tests/adversarial/run_host.ps1`.

The host test verifies prevention of the offending write. It does not run
Relic's network simulation or establish peer CRC equality.

Completed validation: all 65 host-suite entries passed (459 Python test
cases plus the C++ executables). Both InternalInjector and Standalone built
successfully in Release|x64. The packaged DLL was compared byte-for-byte
with the new DLL, the pack's SHA-256 verified, and the complete pack found
inside `dist/AOE4HOOK.exe`. `git diff --check` passed.

DLL SHA-256: `f1324426264a8418d1ad2bf793fc90a8e69712de87d0b59c067beab80830c1bf`.
EXE SHA-256: `491238e55f8e906fd21c49cd8865b19ab78cdd0552c0593485ba3be2c2326f0b`.

The game was already restarted with the old DLL during the investigation;
the fix applies on the next clean game launch with the new build. No live
process was stopped or reinjected.

## Second gate: the game's own network flag

The roster is a cached lobby scan, so a 0 from it is still not the game's
word. `World_IsMultiplayerGame` (`0x1955760`) is
`*(u8*)(qword_84952B0 + 1) == 1`; `0x686920` writes that byte from the match
descriptor: 0 single player, 1 network, 2 skirmish. It is a plain pointer,
read without SCAR (`aoe4sdk::kGameSetup` / `kGameSetupType`).

Map sight now also needs that byte to read 0 or 2. Network (1) or an
unreadable byte blocks the write and releases a reveal we own; the reason is
logged once (`map sight: off, this is a network game (game type 1)`).

`test_ai_map_sight_service` gained the cases: network type with an empty
roster (All and Map), skirmish then network (release), unreadable byte,
single player. On the previous service (`a242326af9`):

```text
FAIL: network game type blocks reveal with an empty roster (writes=5 walks=6 reveal=1)
```

Now it passes. Not yet seen in a match: which byte a custom lobby with only
AI players carries. If it reads 1 there, map sight stays off in such games,
which is the safe side: `docs/CHECKSUM_AUDIT.md` lists sim fog among the
checksummed surfaces.

Sim fog cannot be changed in a network game without a desync, however it is
written: the tiles are part of the synchronized state every peer checks.
Giving the native AI more than the player has scouted is solo-only.
