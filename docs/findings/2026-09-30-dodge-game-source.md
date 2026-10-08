# 2026-09-30 — Dodge against the game source

> **Correction (30.09, evening):** the service behind `[0x84C8F08]` vtbl+0xF8 is the RLink **party** service (root+0x17F0, vtable 0x6538EC8), not Automatch2. Its vtbl+0x1C0, `sub_3010520`, sends the one-byte Leave packet. See [2026-09-30-dodge-stk-parity.md](2026-09-30-dodge-stk-parity.md).

The owner reports that Dodge now brings a matchmaking restriction and asked
whether a commit broke it. This note checks the dodge against the
decompiled game in the repo (`reversed/`,
`internal/SCAR_ANALYSIS/90_INTERNAL_CALLS/native/`). It is a cloud session:
what the server answers is **LOCAL-ONLY**.

## What 0x76D030 does (16.3)

`reversed/00700000/sub_76D030_0x76D030.c`, confirmed against the listing
in `native/0076D030.md`:

1. `session+0x38 = 5`.
2. If the match service at `[0x7B41E28]+0x330` is live, it calls
   `session vtbl+0x120` and posts the `MatchResultPosted` event.
3. It **always** ends in `jmp [vtbl+0x1C0]` on the Automatch2 service
   (`[0x84C8F08] vtbl+0xF8`), with `rdx = session+0x828` (the match id).
   This is the leave report the server answers with the restriction.

It is `MatchSetup`'s virtual at slot `+0x10`. The `MatchSetup` code around it
(`0x76C220`, `0x76C7F0` = `~MatchSetup`, `0x7994D0`, `0x636950`) holds it in
that slot. It is the game's own leave, so the report and its restriction
come with any caller.

## The three changes since 20.09, checked

| Change | Commit | Verdict from the source |
|---|---|---|
| `"ScarToolkit"` dropped from `rdx` | `08ef7f7337` | **No effect.** `rdx` is never read before it is written: the first uses are writes at `0x76d0b7`, `0x76d0d9` and `0x76d11a`, and on the one-time init path `Init_thread_header` clobbers it first. Both variants make the same call. |
| Target from the session vector with a match-id check | `7fb9e20f12` | **Matches the game.** `0x7B41DA0` / `0x7B41DA8` are begin / end of a vector of session pointers. `sub_829020` reads `*begin` only when `begin != end`, and `sub_828550` also checks `session+56`. The 20.09 probing reaches the same session in a lobby (slot0's "vtable" is heap, so `*slot0` is taken), but with an empty vector it read a freed session. |
| Cooldown from 8 s to 1 s | `02f6cacf5b` | **Real risk.** `0x76D030` has no guard, so a second press on the same session sends a **second leave report** for the same match. |

## Changed

- Current Dodge: `ResolveDodgeTarget` refuses a session whose state
  (`+0x38`) is already 5 ("Dodge: already left this lobby."). That makes
  one leave report per session, whatever the cooldown.
- Dodge 2 (first variant, `b00f478cd0`) stays the 20.09 code unchanged, for
  the owner's A/B test.

Tests: `test_lobby_dodge_v1.py`. Checked with a MinGW syntax check only.

## What the source says about the restriction

Both buttons call the same leave. By the source, a restriction that follows a
dodge is the server's rule for leaving a found match, not a client
regression. The one client-side way to double it was the second report,
fixed above. The off-by-default "Leave through Disconnect" switch
(`0x76D140`) calls service `vtbl+0xF0` with a `"> MatchSetup::Disconnect >"`
reason instead of `vtbl+0x1C0`. Whether the server scores that differently is
**LOCAL-ONLY**.

## LOCAL-ONLY

1. **Leave report counts.** Press Dodge twice within a second in one lobby.
   There must be one `[LOBBY] Dodge UI-thread ok` line, then
   `already left (state 5)`.
2. **Dodge vs Dodge 2.** One press each, in two lobbies: the restriction
   (result 11, duration) should be the same. If it is not, the source above
   is missing something.

## Add a computer, from the same source

`reversed/00800000/sub_84D210_0x84D210.c` is `sub_84D210(matchId, slot,
difficulty, personality)`. The game's own add-computer,
`reversed/00F00000/sub_FC9790_0xFC9790.c`, passes these arguments:

| Argument | Value |
|---|---|
| match id | `session+2088` (0x828, the same field Dodge reports) |
| slot | the row's party slot index. It indexes the 528-byte slot records (`v56[39] + 528*slot`), the ones the lobby reader walks. |
| difficulty | capped at 6 |
| personality | `*(*(session+2048)+720) - 301619579` |

`personality == 0` or `difficulty == 127` takes the branch that adds no AI.
The 28.09 call passed match id -2, which the match lookup refuses.

The overlay now makes the same call: the live session (non-empty vector,
match id, not already left), the first Open slot from the lobby model, and
the same personality formula. 0x84D210 does not check that the slot is open,
so the slot comes from the model and only the host may add. The row's team
and civ calls (`sub_84CBE0`, `sub_84AD30`, `sub_84BDC0`) are not made. It is
posted to the Relic UI thread only: the old Present-thread fallback is gone.

**LOCAL-ONLY:** as host of a custom lobby, press Add a computer.

1. A computer appears in the first open slot at the chosen difficulty. The log
   has `[LOBBY] Add AI ok ... slot=N diff=D pers=P`.
2. Check its team and civ. If they are not the lobby defaults, the follow-up
   calls are needed.

## Live result: Disconnect is penalized too; the second Dodge is removed

The owner pressed the second Dodge with "Leave through Disconnect" on, so the
call went through `0x76D140` (MatchSetup::Disconnect). It drew a temporary
matchmaking restriction all the same. With the 30.09 07:00 leave-report
dodge, both client ways out of a found match are now known to be scored:

- the leave report (`0x76D030` → Automatch2 `vtbl+0x1C0`);
- the peer disconnect (`0x76D140` → `vtbl+0xF0`).

The second Dodge, its Disconnect switch and its message
(`WM_APP + 0x5360`) are removed. Dodge 2 (first variant) is left. It makes
the same leave report, so expect the same restriction from it.

What the source shows about a leave without a penalty:

- **Before a match is found**, the game's own Cancel search
  (`Automatch2StopPollingAsync`) stops polling. Nothing has been matched yet,
  and there is nothing to leave.
- **After `AutomatchMatched`**, the server has created the match. The
  restriction is its answer, and the 07:00 sweep found no client state that
  holds it.
- **Custom lobbies** carry no automatch restriction.

## Live result: Dodge 2 works; it is the Dodge now

The owner, 30.09: of the A/B pair, Dodge 2 (first variant, the 20.09 code) is
the one that works. The live-session rewrite (`0c00f3dd92`) and the three
server-penalty variants (`3d859bd25b`) were reverted (`bd79e8d7c5`,
`ef2f53410f`). Dodge 2 is now the only button, "Leave lobby (Dodge)", on the
Skip search cooldown row. Its code is unchanged: the slot probing, `0x76D030`
with `"ScarToolkit"` in `rdx`, the 8 s cooldown. The V1 function names stay;
only the label, the tooltip, the status line and the `[LOBBY] Dodge` log tag
changed.
