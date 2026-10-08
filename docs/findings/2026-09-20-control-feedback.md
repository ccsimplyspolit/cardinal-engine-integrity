# Missing unit-control feedback

The running game log showed repeated selection requests and Lua
`sel skip-live` messages, with no acknowledged forced locks. No per-process
monk-clock or pending-selection files were found in the user or Windows temp
directories. This is consistent with failed/unavailable file output; it does
not prove which DLL revision is mapped into that process or why file output
failed.

Add a second transport through `print` and the existing `warnings.log` tail
reader. This channel already carried the game's selection diagnostics.
Clock and pending-squad snapshots carry a per-process/session token and a
monotonic sequence. Parse only complete, bounded records. Re-reading an old
record does not renew freshness, an empty snapshot cancels requests, and
entity ids are rejected where squad ids are required. No new native calls,
blocking log waits or per-frame disk writes are introduced. The existing
window-thread consumer prefers fresh feedback and retains file fallback.

The latest committed Delhi branch also set the permanent handover latch
before age III. The early return at the top of ComputeMonkHandover then
prevented the Castle-age timer from ever running. Remove that bypass: the
permanent latch is exclusively the 300-game-second timer after age III and
the presence of the first religious unit. Early civilization policies must
not reuse this permanent flag.

Tests run the shipped selection and clock Lua with `io=nil`, verify both
feedback records, and exercise complete/partial records, token isolation,
empty snapshots and stale-sequence handling in C++. Existing handover,
religious-objective and economy tests remain applicable.

Remaining limitation: acquiring a Relic-owned unit still waits for an empty
tactic row. This fix restores a missing request/clock transport; it does not
prove immediate control transfer for a busy villager or monk. Native tactic
stripping remains guarded because of the previously recorded crashes. A
live-game test with the new DLL is required before claiming the entire
selection-lock issue resolved.
