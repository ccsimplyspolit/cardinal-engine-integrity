# Concurrent relic and sacred-site objectives

The user clarified that relics and sacred sites should have equal highest
priority, with no requirement to collect all relics before taking sites.

The army controller now installs the religious actuator independently of the
optional Hybrid Files script. Its existing window-thread scan supplies owned
religious units and map objectives. C++ ranks relics and sites together by
distance, breaking ties by entity id. The Lua actuator preserves assignments,
reserves distinct targets, marks sites high priority through the native AI
interface and issues move-then-capture orders. It skips carriers, player-held
units and allied/owned sites, checks capture eligibility, retries failed
commands, and stops issuing orders after handover or disable. It avoids
reissuing movement inside the capture radius.

Relic pickup and delivery still belong to native Relic AI. A relic assignment
reserves a runner for that AI; it does not issue a new pickup command or
override native pickup scoring. The crash-prone relic-kick path remains off.
Thus equal ranking is implemented by the overlay; equal execution priority
inside Relic's own task scheduler is not proven. Live game testing remains
necessary to establish whether native tactics interrupt capture orders.

On resuming, the in-progress changes were already committed and pushed in
`ff6f16ebf5`. That commit also contained a duplicated villager-controller block
and Lua text inside the first C++ CountFreeSacred function. The duplicate was
removed, retaining the complete controller and the new civilization field in
the clock export. Its export test now checks the additional field.

Validation: 132 handover, 11 religious-objective, 8 selection and 10 economy
Lua tests pass. The C++ objective-ranking test passes. Both new religious
tests are registered in the host runner. The earlier full-suite Fast Age
expectation mismatch is separate and remains recorded in the September 19
findings; this work does not change economy allocation.
