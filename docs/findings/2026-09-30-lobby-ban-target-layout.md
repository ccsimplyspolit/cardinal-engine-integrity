# Current lobby client ban targets, Relic 16.3.11308

The full lobby record contains a `ProfileInfo` at `SlotInfo + 8`. Its ban
fields have the same layout that `PlayerProfileModel::IsAutomatchBanned`
evaluates. These are client data; the findings do not establish that changing
them removes a server matchmaking penalty.

| Field | ProfileInfo / model account | 528-byte SlotInfo record |
| --- | --- | --- |
| Relic profile ID, uint64 | +0 | +8 |
| banInfo.level, int32 bit mask | +0x110 | +0x118 |
| banInfo.expiryDate, int64 | +0x138 | +0x140 |

## Runtime reverse evidence

All RVAs refer to the saved runtime image with image base
`0x7FF7A5500000`; they are not offsets in the protected Steam executable.

- ProfileInfo parser, RVA 2F1CAA0
  passes `profile + 272` to BanInfo parser `2F1EEB0`.
- BanInfo parser, RVA 2F1EEB0
  reads `level` at `banInfo + 0`; expiryDate
  is an int64 at `banInfo + 40`. Thus ProfileInfo offsets are 272 and 312.
- SlotInfo assignment, RVA 663270
  calls ProfileInfo assignment `666D60(dst + 8, src + 8)`.
- ProfileInfo assignment, RVA 666D60
  copies int32 `+272` and int64 `+312`, confirming the embedded record layout.
- RVA `30746E0` walks records in steps of 528, selects by full uint64
  `record + 8`, and calls `666D60(destination + 8, record + 8)`.
- IsAutomatchBanned evaluator, RVA 10D6310
  calls `10CB470(model.account, 4)`; the getter
  evaluates `mask & kind`, then the deadline at `+312`.

The login parser `30ABD20` exposes a different wire response shape. Its
`banLevel` / `banSeconds` offsets must not be substituted for this ProfileInfo
layout.

The validator `8575C0` first obtains a MatchInfo copy through the MatchService,
then checks every 528-byte record with `byte(record + 280) & 0x15`. Any match
returns validation reason 512. This checks bits 1, 4 and 16. Clearing bit 4 in
one player's model does not by itself update every participant's party record,
and does not clear the other two kinds.

## Read-only APIs

`NativeOverridesReadLobbyProfileIds` obtains full uint64 human IDs from the
current party, with a freshly resolved UI model fallback only when there is no
party. It does not use the displayed roster, which contains cached uint32 IDs.

`NativeOverridesReadLobbyBanTargets` returns `{profileId, accountAddress}`
from current **party records only**. `accountAddress = record + 8`; a UI copy
is never returned as a writable party target. The implementation:

1. Resolves the current session, its positive match ID and known session class;
   requires configuring or starting state (1 or 2).
2. Resolves the matching party through the existing root/service reader, bounds
   its vector to at most 16 records and copies it with `ReadPartyLobby`.
3. Includes human slots with positive full uint64 IDs; excludes AI, closed,
   open and observer/pending slots. Checks record index and exact address.
4. Rechecks session pointer, session vector, match ID, state, party identity,
   party vector bounds and the copied record bytes before publishing targets.
5. Returns false/count zero on a transitional read or insufficient capacity.

Neither wrapper acquires `g_mutex` / `g_skipCdLock`, invokes a Relic native
function, or writes game memory. A returned target is a stable observation at
the time of the read, not a lifetime guarantee. A writer must re-resolve the
**exact address and full profile ID** immediately before its operation and use
compare/exchange for the expected mask; checking only membership by ID is
insufficient after a vector relocation.

## Validation limit

The exact production wrappers compiled with MSVC `/W4 /WX` and passed 19 ID
API and 15 party-target API contract cases using mocked read helpers. Cases
covered full-width IDs, source preference, deduplication for IDs, all copies
for targets, session/source/vector replacements, transient data, unchanged
output on failure, nonhuman exclusion and output capacity. This validates the
wrapper contracts and failure behavior. It is not a live game or server test.
