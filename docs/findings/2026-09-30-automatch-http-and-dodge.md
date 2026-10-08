# Automatch: HTTP evidence, Dodge and current lobby client flags

## Result

Server penalty skipping and penalty-free Dodge are not established. The captured
successful search occurred **after** the previous penalty expired. A subsequent
Dodge was followed by a new 30-minute server penalty, while the inspected profile
ban masks stayed zero.

The implementation now clears automatch kind 4 in every current human party
record, as well as matching profile models. This corrects the local group
validation target; it does not remove a server-side deadline.

## Capture and timestamps

HTTP Debugger MCP was already configured correctly in the Codex user config.
The executable is HTTPDebuggerMcp.exe 10.0.0.10. Capture diagnostics reported
driver up and installed SSL certificate. The user stopped capture and preserved
3528 transactions.

`list_transactions` and `get_transaction` did not return within the bounded
reads, even with capture stopped. `search_transactions` worked. Cursor searches
were continued to `complete=true` over the session; relevant URL/header/body
fragments were selected by the internal transaction IDs, not the application's
row counters. Credentials and relay tokens were excluded from observations.

The wire responses are **positional JSON arrays**. The client parser supports
both array and named-object forms. Searching bodies for `result` or
`automatchCooldownExpireTime` alone therefore missed these real responses.

Times below are September 30, 2026, Europe/Kiev (UTC+3), converted from the
captured server HTTP Date header. Expiry is a Unix timestamp from the response.

| Internal ID | Request / event | Server time | Response | Meaning |
| --- | --- | --- | --- | --- |
| 3317 | polling | 01:18:21 | result 11, expiry 1790720364 | 63 seconds remain; expiry 01:19:24 |
| 3337 | polling | 01:18:29 | same result/deadline | 55 seconds remain |
| 3343 | polling | 01:18:34 | same result/deadline | 50 seconds remain |
| 3556 | polling | 01:19:54 | result 0 | accepted 30 seconds after the old deadline |
| 3577 | updateStatus | 01:19:58 | `[0,30]` | success, **matchStartDelaySeconds=30** |
| log | Dodge UI-thread call | 01:19:59.322 local | Relic RVA 76D030 returned | native Leave path invoked during pre-match delay |
| 3591 | polling | 01:20:03 | result 11, expiry 1790722202 | new deadline 01:50:02; 1799 seconds remain |

Transaction 3577's request body contains `result=1&resultCode=0`. Its response's
second value is not a penalty duration: parser `31AC8B0`, callback
`306AF60 -> 30766B0` and remaining-time getter `306EB00` establish that this is
the match-start delay in seconds. The 30-minute penalty is independently
observed in transaction 3591's polling deadline.

The internal log at 01:19:59 records both native call and subsequent profile
inspection with mask 0, deadline -1 and cached bool 0. At 01:20:04 the saved
Info still reports expiry -1/result 0 while service lastError becomes 11.
This is consistent with the real response, not evidence that the server has no
penalty. Log times use the local clock; the HTTP table uses the server clock.

## Reproducible response decoding

Complete captured transaction 3317 body (93 bytes, no IDs or tokens):

```json
[11,[],0,1790720364,null,null,null,null,null,null,null,null,0,null,null,0,0,0,null,[],null,0]
```

Its first four fields end at this raw ASCII prefix:

```text
[11,[],0,1790720364,
5b 31 31 2c 5b 5d 2c 30 2c 31 37 39 30 37 32 30 33 36 34 2c
```

Run from the repository in PowerShell:

```powershell
py tools/automatch_response_audit.py --endpoint polling --server-date 'Tue, 29 Sep 2026 22:18:21 GMT' --body '[11,[],0,1790720364,null,null,null,null,null,null,null,null,0,null,null,0,0,0,null,[],null,0]'
py tools/automatch_response_audit.py --endpoint updateStatus --body '[0,30]'
```

The first command returns result 11, 63 seconds remaining and pollAccepted
false. The second returns matchStartDelaySeconds 30. The decoder prints only
the relevant numeric fields and never outputs relayAuthToken, profile IDs,
player names or authorization headers. It does not send requests.

## Protocol and client response flow

Authoritative source is the saved runtime reconstruction, not the protected
on-disk executable. These are client sources; server implementation is absent.

| Message | RVA | Relevant fields |
| --- | --- | --- |
| POST /game/automatch2/polling | 306B780 | matchTypes, factionIDs, race information, partySessionID, options, map vetoes, build/mod checksums; optional relay and previous-match state |
| POST /game/automatch2/stoppolling | 30741A0 | commit, ownerProfileID |
| POST /game/automatch2/updateStatus | 3071920 / 3072080 | matchID, result, resultCode |
| POST /game/party/reportMatch | 300E030 | profile_ids, simplayerIDs, teamIDs, race_ids, results, xpGained, checkSums, countersZip, itemUpdates |

Forms are URL-encoded by `2F46200`; array-valued fields contain JSON text.
Transport `2F33B00` selects CURLOPT_POST. None of these inspected constructors
contains an explicit server-penalty bypass parameter.

Polling array indices from `31AA7B0`: 0=result, 1=searches,
2=estimatedWaitTimeMS, 3=automatchCooldownExpireTime, 4=hostingProfileID,
5=hostingMap, 6=teamID, 7=factionID, 8=raceID, 9=teamCount,
10=maxPlayersPerTeam, 11=matchTypeID, 12=matchID, 13=relayAuthToken,
14=relayIP, 15/16/17=relay ports, 18=relayRegion, 19=matchMembers,
20=options, 21=totalPlayerPoolCount. Token and identity values are not retained
in this report.

`3075DD0` copies incoming Info into service+0xD8 only for result 0. A nonzero
result reaches `3074100`. That function routes result 11 into stop/error
handling at `30732B0`, independently of either profile ban bit or saved expiry.
The UI reads the incoming event expiry at +0x170 to display remaining time.
Consequently clearing saved Info+0x158 cannot turn a refused server poll into
an accepted one.

## Dodge, real connection loss and ScarToolkit

Both recovered STK builds use Relic RVA `76D030`. In the newly supplied
recovered_sln, button `12D7F0` calls wrapper `12AE00`, which calls `12AA80`.
The wrapper's other operations reset STK's own UI data. Its 10-second button
throttle is separate from matchmaking penalties. The older recovered wrapper
EB990 uses the same Relic function.

STK source evidence:

- `AOE4_ScarToolKIT/src/attach/sub_7FF67FFDAA80_0x7ff67ffdaa80.c:77`
- `AOE4_ScarToolKIT/src/decrypt/sub_7FF67FFDAE00_0x7ff67ffdae00.c:33`
- `AOE4_ScarToolKIT/src/attach/sub_7FF67FFDD7F0_0x7ff67ffdd7f0.c:887`
- `AOE4_ScarToolKIT/src/runtime/sub_7FF67FEB2670_0x7ff67feb2670.c:13`

Relic 76D030 sets session state 5, conditionally posts a match result through
vtable+0x120, and sends Leave packet type 31 through `3010520 -> 30354C0`.
Type 31 has no disconnect-reason payload. It does not read the extra RDX string
"ScarToolkit". Our wrapper now uses the actual one-argument signature.

Neighbour 76D140 is a different Disconnect path. Its ordinary reason 0 becomes
1000 via `300BE60 -> 300C300`; DisconnectAsync `300B740 -> 30381E0` uses peer
packets 7/8 and then closes transport. Real relay/host loss at `30393F0` uses
reason 2 and separate cleanup. These peer reason fields are not a demonstrated
trusted server waiver. Replacing the reason with 2 or suppressing a local popup
would not establish that a server accepted search before the deadline.

Ordinary CancelSearch `137FC90 / 15BA480 -> 306DBC0` has activity, party and
player-state checks. It schedules stoppolling with commit 0. Match start uses
commit 1. Cancelling a permitted search is not evidence of penalty-free exit
from a match already acknowledged by updateStatus.

The existing Network Monitor hooks target WinHTTP/WinINet/libHttpClient
exports. The inspected automatch HTTP transport uses libcurl, and Dodge's
Leave notification is a separate peer/party packet. No Skip coupling or
automatch-specific bypass was found in those monitor rules.

## Implemented client corrections

- Fresh human IDs from the current party/UI lobby; full uint64, not a cached
  displayed roster or a truncated profile ID.
- Direct fresh party ProfileInfo targets for every human participant. Clear
  only known automatch kind 4 using compare/exchange. Keep other kinds and the
  shared deadline. The layout is documented in
  `2026-09-30-lobby-ban-target-layout.md`.
- Re-resolve exact address plus full ID before each party-mask write; reject
  moved vectors, old sessions, transient reads and former participants.
- Include all current participants when scanning profile models; do not stop
  at the first banned model. Revalidate model/account/membership before mask
  and cached-property writes, including the cache-only path.
- Preserve the empty-result retry interval. Trigger a new scan on membership
  change, and prevent an old worker result from delaying that request by
  overwriting its deadline.
- Verify the complete evaluator instruction sequence, not just a displacement
  somewhere in its first bytes. Report local clearing without claiming server
  acceptance.

## Checks and limits

The MSVC adversarial client tests pass (invalid layouts/identities, full-width
IDs, membership loss, sign-out after CAS, contested updates and party-vector
relocation). The response decoder passes four tests, including the actual
captured refusal and updateStatus countdown. The new read-only membership
wrappers separately passed 19 ID and 15 target contract cases with mocked
read helpers. The final Release|x64 build completed with exit code 0 and
produced `internal/x64/Release/InternalInjector.dll`. Final review confirmed
the stale-worker publication fix and the roster-transition status fix;
`git diff --check` reported no whitespace errors.

These checks validate client code and captured response interpretation. They
do not prove server-penalty skipping. A final read followed by CAS still has a
lifetime window without the game's object mutex/reference ownership; repeated
resolution reduces that window but does not make it an atomic transaction.

The newly built DLL is separate from the older DLL already loaded by the
running game. No second injection or debugger attach was performed. A working
server bypass still requires an accepted search before an independently
observed unexpired deadline, and a penalty-free Dodge requires a live exit
followed by immediate accepted search. Neither outcome was observed here.
