# Religious handover and selected villagers

The previous religious timer started on the first ordinary monk at any age,
using time since AI startup. Seeing the ground-relic count fall to zero also
triggered handover. HRE's early prelate could therefore trigger it before the
requested Castle-age window.

The timer now consumes player age, game time and monk presence from the same
window-thread Lua scan. It arms only at age III or later with an ordinary
religious unit present, expires after 300 game seconds and stays latched for
the match. A pre-existing prelate arms it at Castle entry; without one it waits
for the first monk. Pause does not advance it. Death or advancing to age IV
does not restart it. Relic/sacred counts no longer determine the timer.

Selection defects addressed:

- AI_IsEnabled could report false while the session was live, skipping ticks.
- Initial highlighted villagers could not be claimed by an explicit click.
- Keyboard selection changes did not record player intent.
- Already-locked tracking rows were not acknowledged by Lua.
- Failed native calls were reported as successful locks.
- The request writer and reader used different temporary-directory paths.
- Retrying a pending claim could continually extend deselection grace.

Both selection requests and religious handover requests now publish bounded
snapshots. Their consumer runs on the window thread and only sets the lock
flag for an empty AI tactic row. Lua acknowledges the resulting published
tracking lock; religious acknowledgements are permanent. Match reset clears
old requests, and requests also expire. Enemy selections are excluded.

## Remaining runtime limitation

A unit with an active AI tactic remains pending until that tactic releases it.
The native operation for forcibly stripping a live tactic remains guarded:
prior crashes are documented in the source. This change does **not** prove or
guarantee immediate handover of busy villagers or monks. New monks discovered
after the timer are also subject to this guard and scan latency. A live-game
run is still required; the running game retained the previous DLL.

## Validation

- 15 C++ timer checks passed.
- 132 embedded Lua army/handover checks passed.
- 8 embedded Lua selection checks passed.
- 10 economy-idle checks passed.
- Release DLL and standalone EXE built successfully.
- Embedded standalone payload and DLL match the new build byte for byte.
- PE check confirms build-order mutable globals remain in writable .data.
- The full host suite stopped at an existing, separate Fast Age test:
  `fast_age keeps food exactly twice gold despite stock relief`.
  The pre-existing local economy changes set food and gold equally. Neither
  those economy changes nor the test expectation were altered in this fix.

Output: `dist/AOE4HOOK.exe`.
SHA-256: `abff9ff66334e682215f842cc843f96422f894c7f08ace7458d03f43cee9e0a3`.
