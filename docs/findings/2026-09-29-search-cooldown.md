# Search cooldown: corrected target, unverified matchmaking effect

User requested both a local Search unlock and starting matchmaking during a
server penalty. Neither gameplay outcome is established by this change.
The restored switch is explicitly experimental and defaults to off.

## Evidence

Source: runtime reconstruction at `K:/aoe4_dlc/aoe4/gamesource/src/readable/shards`.
All addresses below are RVAs for the reconstructed 16.3 runtime. No disk EXE
was analyzed. A final read-only check also inspected the running game (PID
36512); its loaded overlay still predates this build.

- `0x2F8B060` allocates a 1080-byte service with `0x306B210` and stores it at
  RLink root+6080 (`0x17C0`). Root global is RVA `0x84C8F08`.
- `0x306B210` sets the service vtable to `0x653ADA8` and calls `0x862F50`
  on service+216 (`0xD8`). That constructor sets vtable `0x6292E40` and
  initializes Info+344 (`0x158`) to `-1`.
- The Info is **embedded**, not a pointer member. The old heap pointer walk
  missed this object even after changing the root offset from `0x17E0`.
- `0x31AA7B0` parses `automatchCooldownExpireTime` into Info+`0x158`.
  `0x85D1B0` and `0x306CF90` copy this field.
- `0x3075DD0` copies the response Info to service+`0xD8` on its success
  branch. Its error branch calls `0x3074100` with the response result.
  Thus the saved Info is not a reliable record of the latest failed poll.
- `0x3074100` records the error at service+84 (`0x54`). Result 11 takes
  the stop/error path via `0x30732B0`. This is separate from clearing a
  local deadline. `0x3074C50` is not the `OnPollError` entry point.
- `0x10CEAB0` installs evaluator `0x10D6310` for `IsAutomatchBanned`.
  It calls `0x10CB470(*(profile+5040), 4)`, which checks an account-ban mask
  at account+272 and a deadline at account+312. This is not evidence that
  the byte represents a matchmaking-leave cooldown.
- `0x10C4330` evaluates that property on access when its cached epoch differs
  from the global epoch (except the sentinel). The getter alone does not
  prove a write every 16 ms; the old report overstated that conclusion.

No proven consumer was found showing that clearing saved Info+`0x158`
unlocks Search. No server acceptance during an active penalty was observed.
The patch must not be described as a working penalty bypass.

## Implementation

Replaces the heap walk and cached restore addresses with the exact ownership
chain and both vtable checks. Reads fail explicitly. Only a plausible future
Unix deadline is cleared; zero, `-1`, expired values and invalid layouts are
not successes. The comparison uses the local UTC clock, so clock skew remains
a limitation for classifying a deadline as expired.

The chain and snapshot are read again before an aligned compare/exchange on
a writable, non-executable data page. This reduces races but cannot pin a
game-owned object's lifetime; a live game test is still required. No Relic
function is called and no code or account-ban flag is patched.

Off stops writes. It deliberately does not replay the original deadline:
a subsequent server response may have cleared or replaced it. No raw game
object address is retained for later writes.

The window message consumes the latest requested state. Pending is set before
posting, failed posts restore the requested state, and the periodic Present
service does not wait for the window thread. Status exposes last server
refusal independently of client writes. The log records service, embedded
Info, observed expiry, saved result, last error and actual write outcome.

## Validation

`tests/adversarial/build_lobby_search_cooldown.cmd` compiles with `/W4 /WX`
and runs the production resolver/clear policy against synthetic memory:
embedded Info, zero/-1/expired/invalid deadlines, wrong vtables, the old wrong
root offset, failed reads, replaced owner, response changed before the write,
and server result 11 even when a local field was cleared. Passed.

Release|x64 `InternalInjector.vcxproj` built successfully. The only compiler
warning was the existing `ai_planner.cpp:1488` C4456 (`nowMs` shadowing).
Output: `internal/x64/Release/InternalInjector.dll`. The project's pre-link
step renamed the old loaded DLL; that does not update the running overlay.

A targeted `ReadProcessMemory` check against PID 36512 confirmed both exact
vtables in the current process: service `0x653ADA8`, embedded Info `0x6292E40`.
Observed expiry `-1`, service last error `0`, saved result `-1`. Thus the
ownership chain is verified live, but there was no saved active cooldown to
test. No writes were made to the process, no debugger attached and no DLL
injected during this check.

## Correction, same day: the removed target was the only one with a consumer

The switch above clears the saved polling Info only. That field has no proven
consumer, and on this machine it reads `-1` (status "No local cooldown in the
saved response."), so the switch did nothing observable — the reported
regression. The target it replaced does have one.

`IsAutomatchBanned` is a registered, bindable property. Its evaluator is
`sub_10D6310`, installed by the `PlayerProfileModel` constructor `0x10CEAB0`
(5288 bytes, factory tag `"PlayerProfileModel"`; `LocalPlayerProfileModel`
derives from it):

- `+0xCB0` cached epoch, `+0xCB8` evaluator, `+0xCC0` int delta, `+0xCC8`
  cached bool. `sub_10C4330` re-evaluates only when the cached epoch differs
  from the global `qword_7B41E68`; otherwise the cached byte is the answer.
- `sub_10D6310(model, out)` sets `*out = sub_10CB470(*(model+0x13B0), 4)`.
- `sub_10CB470(account, kind)`:
  `(kind & *(uint32_t*)(account+272)) && (*(int64_t*)(account+312) <= 0
  || serverNow < *(int64_t*)(account+312))`.
- Kinds are one per property: 4 `IsAutomatchBanned`, 8 and 16 the other
  getters (`sub_10D6340` / `sub_10D6370`), and `sub_10D63A0` exposes
  `account+312` as `BannedTime`.

So the automatch gate is one bit in one word. Clearing kind 4 makes the next
evaluation false as well, which is why the 28.09 version had to rewrite the
cached byte every 400 ms and this one does not.

What made the old switch unsafe was its shape test, not its target: any object
with an image vtable, a pointer at +1960 and a 0/1 byte at +0xCC8 passed, so it
zeroed bytes in unrelated objects ("banned=3/4"). The identity test is now the
evaluator slot itself — `*(void**)(model+0xCB8) == image+0x10D6310` — which only
that constructor writes.

Implementation: a read-only sweep of committed private read/write memory (thread
stacks skipped by the guard page in their allocation) for that pointer value, on
its own thread with an 8 s budget; the window thread only re-validates cached
addresses and writes. The sweep refuses to run unless the evaluator is executable
in the loaded image and still carries the `0x13B0` displacement, so a moved
function is a refusal instead of a hunt for a value that no longer means
anything. The mask is re-read immediately before an `InterlockedCompareExchange`,
`+312` is never written (it is shared with the other ban kinds), and off stops
writing without putting the kind back. Every model found is cleared, including
other players' — that changes only what this client believes about them.

The switch is on from inject. Both targets are client state: neither can make
the server accept a search it refuses (result 11).

## Remaining verification

With an actual cooldown in the game, record the overlay status and
`[LOBBY] Skip search CD` lines, whether Search becomes clickable, whether a
search starts, and whether it continues after the next server response.
These are separate outcomes. A cleared field or a started animation is not
proof that the server accepted the search. No matchmaking request or lobby
dodge was issued as part of this offline validation.

For the ban flag specifically, the lines to read after a dodge are
`[LOBBY] Skip search CD scan done models=… banned=…`, the per-model line with
`profileId=` and `banKinds=`, and `[LOBBY] Skip search CD ban state=…`. A scan
that reports `models=0` means no profile model was in memory, and
`layout=0` means the evaluator check refused — neither writes anything.

## Dodge

The overlay's own 8 s lockout after a leave was the toolkit's UI throttle
(`Dodge on cooldown (%ds left)`), copied with the rest of that button. Nothing
in `sub_76D030` or the server path needs it, so it is 1 s now — enough that one
click cannot post the leave twice. The leave itself is unchanged; what it does
to the cached profile models is below.

## What a leave tells the server

`sub_76D030(session)` — the callee the toolkit stub and this overlay both use —
is the game's own leave, not a client-side hide:

- `*(uint32_t *)(session + 56) = 5`, the `+0x38` write the byte pattern matches;
- with a setup at `qword_7B41E28 + 816` whose `+536` is not `-1`, it calls the
  session's `vtable+288` and posts the `MatchResultPosted` event
  (`sub_36246E0(..., "MatchResultPosted")` through `sub_98DB80`);
- then, unconditionally, `(*(root + 248))(qword_84C8F08)` and
  `(*(service + 448))(service, *(uint64_t *)(session + 0x828))` — the Automatch2
  service, with this match id (`RLink::Automatch2LeaveMatchMessage`).

The leave is reported, so the penalty that follows is the server's answer and no
client edit can un-send it. `sub_76D140` is the neighbouring disconnect
(`"<tag> > MatchSetup::Disconnect >"`, service `vtable+240`, reason 0) and is the
entry that reads the cookie string this overlay still passes in rdx; `0x76D030`
takes the session alone on 16.3. Whether the server scores a disconnect
differently from a leave is untested and is not assumed here.

The recovered toolkit is no counter-example: its stub called this same function
(`MAPHACK.md`, the live packed slot ~115 ms after the toolkit's 0x29 stub), and
it never had a cooldown skip at all — `SCARTOOLKIT_FULL_PARITY.csv` M27 lists
only its own 8 s UI throttle.

What the client can do is not believe the penalty, which is the switch above.
Two windows where it could not:

- After a leave the model list was dropped, so a ban landing seconds later stood
  until an 8 s sweep finished, and 20 s longer whenever that sweep found nothing.
  The models are kept now: every pass re-validates the evaluator slot and re-reads
  `model+0x13B0`, so an account rebuilt from the reply is picked up on the next
  400 ms pass. Only the sweep is re-armed.
- A sweep that found something set the next one five minutes out. If every model
  was dropped after that (freed, reused, or rebuilt by a re-login), the list
  stayed empty for the rest of those five minutes. An empty list now falls back
  to the 20 s retry.

A live dodge decides which penalty is actually issued, and the log separates
them: `[LOBBY] Skip search CD state=… expiry=… lastError=… result=…` is the
Automatch2 saved Info, `[LOBBY] Skip search CD ban state=… kinds=0x… until=…` is
the account ban word. If a dodge sets neither while the game still locks Search,
the lock is a third thing and this switch cannot reach it.
