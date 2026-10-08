# Lobby civ scan is slow — why, and the ScarToolKIT comparison

## Measured cost (debug-78fb47.log, `after_heap`)

Every `CivScanWorker` pass recorded:

- `elapsedMs` **35 000–62 000** — 35–62 s per scan, scheduled every
  `kCivFullRescanMs` = 6 s, so the worker is effectively always running.
- `anchors` **3–5 million** — `CollectAsciiSteamFast`/`CollectUtf16SteamFast`
  match every `"76561…"` byte run across the whole heap; the vector plus its
  two `std::sort`s (here and in `FindLobbyCluster`) dominate.
- `hits` **60 000–138 000** — the 16-entry PBG catalog is small decimal DWORDs
  (106553, 131384, …) that collide with random heap DWORDs.
- `chased` **20000** (budget fully drained) while `grouped` **0–1** — the
  CivForcer pointer-chase (`CollectCivForcerSteamIdsNearPbg`, one RPM of
  `pbg-0x80` per hit) ran 20 000 times and produced almost nothing.

Root cause: `NativeOverridesScanCivs` calls `BeginWorker(false)` — the civ scan
has **no time budget** (the 12 s `kHeapScanBudgetMs` is level/xp only), so it
runs the full two-pass sweep to completion.

## How ScarToolKIT / CivForcer finds (reference)

`civctrl_scan_B5CBB0` + `civctrl_write_B5D450` (dumps in
`tools/_lobby_dump_extract/`) are **external** (`OpenProcess` handle in a global,
`VirtualQueryEx` + `ReadProcessMemory`). The scan:

1. Looks for **one 8-byte magic** `"CIVCTRL1"` = `0x314C525443564943` at 8-byte
   stride, record stride `0x28` — a single qword compare per step, ~0 false
   positives (vs our 16-value catalog + text).
2. Runs **once**, caches the block base in a global (`[rip+0x21a54d]`) behind a
   done-flag (`[rip+0x224225]`). Every later Force is O(1) fixed-offset
   read/write into that block (`civctrl_write_B5D450`).
3. The block is planted and kept fresh by an **injected helper** that hooks the
   Relic lobby — the external UI never re-scans.

So the reference is not a cleverer *search*; it is (a) one compact marker,
(b) scan-once-and-cache, (c) a hook that feeds the data. AOE4HOOK re-runs a
36–62 s fuzzy full-heap scan every 6 s instead.

## Fix applied (this commit) — `ScanLobbyRegions`

Two provably-safe cost cuts (output for real rosters unchanged; `grouped` was
already ≈0, AI path `AddAiPlayers` is dead code, cluster uses only Text runs):

- **`DropIsolatedTextAnchors`** — per region, keep a Text anchor only if a
  *distinct* Text id sits within `kLobbyPackGap` (the exact precondition for a
  `FindLobbyCluster` run) or it is the local id. Kills the 3–5 M → thousands
  anchor blow-up and both million-element sorts. Qword anchors kept (Force
  targets); text found *near a PBG* stays unfiltered (lone-human path).
- **`AnchorNear` gate** — chase a PBG hit only when a Steam anchor is within
  `kSteamIdNearBytes` of it. Collapses `chased` 20000 → ~roster with no change
  to `grouped`.

Built clean: `msbuild AOE4HOOK.sln /t:InternalInjector /p:Configuration=Release`.

## Confirmed live (build 16.3.11308, 2026-09-27)

`after_heap` before → after, in an 8-slot AI lobby:
- `anchors` 6,100,000–6,600,000 → **15,675 then 6,619** (~400× fewer).
- `chased` 20,000 (budget drained) → **271–978**.
- `elapsedMs` 36,000–62,000 → **3,859 / 3,907** (~10–15× faster).

The residual seconds were the **large-region pass reading multiple GiB** even after
the small pass already had the roster. Added `kCivLargePassBudgetMs` (2500 ms):
once `FindLobbyCluster` returns a cluster from the small pass, the large-region
sweep is time-boxed (Force re-gathers write-copies on demand). That is what took
the fast scans to ~3.9 s.

Remaining (pre-existing, not from these cuts): AI slots never show (steam-only
path, `AddAiPlayers` dead), and persona-name guessing yields junk names
("ui_priority", "IsMapALocalUnit"). Both are fixed cleanly only by the direct
lobby-model read (see `2026-09-27-lobby-model-direct-read.md`).

## Not done (bigger levers, if still slow)

- **Tier 2 — walk the Relic lobby root, zero scan.** Being internal, AOE4HOOK
  can read the roster by pointer chain like it already reads
  `LocalPlayerProfileModel` (image `0x7FF6F65C0000`, offsets in
  `native_overrides.cpp`). Needs the lobby-session container global from IDA
  (`7ff6f65c0000.RelicCardinal.exe.i64`); patch-fragile.
- **Cadence** — after the first good scan, lean on `RefreshCachedCivPlayers`
  and only full-rescan on a membership change; raise `kCivFullRescanMs`.
- **PBG false positives** — validate a catalog DWORD by the adjacent SteamID64
  qword at `pbg-408` (nested layout: steam +8, pbg +416) before recording.
