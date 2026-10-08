# Session and economy audit: baseline and migration plan

Audit baseline: working tree at the start of this request, including the prior
sheep repair. This repository already contains many uncommitted changes. The
audit does not attribute all of them to this task.

## Verified source graph before changes

`BeforePresent -> AiSessionService -> TickEcoContest -> PostMessage`
`WM_SCAR_ECO_CONTEST -> HandleEcoContestPosted -> BuildEcoContestScript -> HelperRunSoft`

The normal economy path posts to the window thread. If posting fails, however,
`TickEcoContest` calls `RunEcoContest` synchronously; that fallback can block
Present through the SCAR bridge. The window handler currently performs world
classification, resource occupancy, sorting, nearest-worker selection and Lua
serialization before calling the engine. This is separate from the C++ army
planner already running on the persistent collector.

## Concrete defects to verify and fix

- Own drop-off anchors stop at 16; this also stops counting town centers.
- Ally drop-offs stop at 16 and ally workers at 80. These limits can change
  resource-sharing decisions according to traversal order.
- The prior sheep recovery adds all nearby standing workers ahead of a 16/48
  job limit. That unbounded prefix suppresses every other resource pass.
- `Issue` ignores explicit manual squad locks. Temporary contest unlocks can
  also remove a lock still required by a manual selection/group/garrison owner.
- Command `pcall` success is treated as acceptance; explicit `false`, group
  construction failures and invalid squad conversion are not distinguished.
- Temporary locks expire only when another nonempty job script runs. Their
  cleanup is skipped forever on an empty plan and removed even after unlock
  failure. Handover/reset behavior needs matching lifecycle checks.
- Unchanged economy polling retries every 8 s because snapshot speed/resource
  flags cannot prove native gathering state. This is recovery work, not a
  successful-configuration cache. Native acknowledgement/perception is required
  before eliminating all unchanged recovery probes.

## Migration and validation order

1. Preserve complete discovery data; separate pure job assignment from engine
   execution and expose it to host tests.
2. Bound only the command batch, rotate across the complete sorted job set,
   and test populations larger than a batch. Do not silently truncate analysis.
3. Guard native commands and respect manual ownership at actuation time.
4. Keep expiration maintenance independent of whether a new job exists.
5. Remove synchronous posting fallback. Move computation to an existing worker
   only with a verified copied-snapshot seam and session-generation invalidation.
6. Build Release x64; run actual embedded Lua under mocks plus pure C++ tests.
   Compare log-derived SCAR timings with a controlled runtime capture before
   claiming FPS improvement. Historical spike logs cannot provide whole-run p99.

## Repository index

`graphify extract AOE4HOOK/internal --code-only --no-cluster --out . --max-workers 4`
produced 6,786 nodes and 18,604 edges. One syntax warning in `config.h` means
its AST coverage is partial; raw-source searches remain necessary. Vendor,
archive and binary dumps were excluded. This index is discovery coverage, not
a claim that every line has been semantically audited.
