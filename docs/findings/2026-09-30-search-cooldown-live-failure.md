# Skip search cooldown: live failure with restored ban clearing

The user reproduced the temporary automatch penalty with the switch enabled.
The screenshot shows 4:16, then 3:53 remaining. The overlay simultaneously
shows "Matchmaking ban flag is not set" and a last-server-response refusal
with result 11. A working bypass is not established.

## Version and observations

The checkout was clean at `4896918601`, matching `origin/main`, when inspected.
It already includes `02f6cacf5b` (account ban-bit clearing) and `4896918601`
(retain models after Dodge). Transferring these commits again cannot fix this
reproduction. The running game reports build 16.3.11308.0, PID 34148, with
the overlay loaded. No new injection, debugger attachment, matchmaking
request, or memory write was performed during this verification.

Source: the user's existing `aoe4_internal.log` on September 30, 2026:

- 00:58:48.707: Dodge's native call returned.
- 00:58:48.973: profile inspection found `banKinds=0x0`, `until=-1`,
  `cached=0`.
- 00:58:54.502: saved response `expiry=-1`, `result=0`; service
  `lastError=11`; `wrote=0`.
- Later attempts at 00:59:04, 00:59:09, 00:59:11, 00:59:34 and 00:59:56
  again produced result 11.
- The single scanned profile ID matches the game's local profile ID in the
  log. All observed mask/deadline/cache triples are `0/-1/0`; no ban-clear
  event has `held>0`. This reproduction is not explained by selecting only
  a different player's profile.

## Different client states

All addresses here are RVAs from the saved runtime reconstruction.

- `0x10D6310` evaluates `IsAutomatchBanned` using `0x10CB470` with kind 4.
  It reads the account at profile+`0x13B0`, its mask at +`0x110`, and shared
  account-ban deadline at +`0x138`.
- `0x31AA7B0` independently parses the polling result into Info+`0x30`
  and `automatchCooldownExpireTime` into Info+`0x158`.
- `0x3075DD0` copies Info into the service's saved Info at +`0xD8` only on
  success. A nonzero result instead reaches `0x3074100`. Therefore the saved
  deadline can remain -1 while a current error contains a real penalty.
- `0x3074100` routes result 11 to stop/error handling at `0x30732B0`
  independently of either the account ban bit or the saved expiry.
- `0x85AEB0`, case 11, formats the incoming event's expiry at +`0x170`
  (Info+`0x158`) into the remaining minutes and seconds shown by the game.
- `CanExecute` at `0x13887A0` calls `0x8575C0`, which does have a roster-ban
  check. This is not a reason to claim all local ban checks are absent. It
  does not negate the observed server refusal after a search request.

The original `840c840cf9` cleared client cache/DTO fields. The newer commits
also clear account mask bit 4; they explicitly do not establish server
acceptance. No removed server-cooldown bypass was identified in these commits.
This does not prove that no other version or mechanism ever worked.

## Limits and further work

Successful compilation, a clear local bit, or a request sent to the game is
not an acceptance test. A working restoration requires a search accepted
while a independently observed, unexpired server penalty is still active.
Success after the penalty naturally expires must not be counted as a bypass.

Separate code-review findings remain: the general profile sweep lacks an
explicit local-owner filter, and its empty-list handling resets the retry
deadline on every pass. Those can be corrected as client bugs, but neither
correction is evidence of a server-penalty bypass. No product code was changed
in this initial verification. The subsequent implementation addresses the
current lobby participants and retry handling; see
[the follow-up implementation and HTTP evidence](2026-09-30-automatch-http-and-dodge.md).
