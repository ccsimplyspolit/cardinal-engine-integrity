# Skip search cooldown: the target narrowed away from the live response

The user reports that this used to work by default and stopped. That is a real
regression in what the switch writes, and it is fixed here. It does not make the
server accept a search; see
[the HTTP evidence](2026-09-30-automatch-http-and-dodge.md).

## What changed between the versions

`840c840cf9` (3 Sep) cleared two client targets:

- the cached `IsAutomatchBanned` byte in profile models (`+0xCC8`), and
- the deadline at `+0x158` in **every** object whose vtable was the Automatch2
  Info vtable `0x6292E40`, found by a shallow pointer walk from the app pointer
  (`0x7B41E28`) and the RLink root (`0x84C8F08`), depth 1, up to 8 objects.

The 29 Sep rewrite (`7fb9e20f12`, then `3a71425fb2`) replaced that walk with the
exact ownership chain: root `+0x17C0` → service `+0xD8`, the Info **embedded in
the service**. That chain is correct for the saved Info and wrong as a target:
`sub_3075DD0` copies a response Info into `service+0xD8` **only when the result
is 0**. While a refusal is current the saved copy still reads `-1`, so the switch
inspected it, classified it as "no local cooldown" and wrote nothing at all.

The deadline the client actually holds during a penalty is in the Info the
response parser `sub_31AA7B0` filled — a separate heap object from the same ctor
`0x862F50` with the same vtable. The 3 Sep walk reached objects like that one.
The 29 Sep chain cannot.

## The fix

The private read/write sweep that already looks for profile models now also
collects Info objects, in the same pass:

- A candidate is a qword equal to `image + 0x6292E40` at offset 0 of the object;
  only that ctor writes it, so a freed and reused block fails the test.
- Each pass re-reads `+0x30` (result) and `+0x158` (deadline), and clears only a
  deadline that is a plausible future Unix time, through the same aligned
  compare/exchange on committed read/write data. Zero, `-1`, expired values and
  values outside 2001…2100 are left alone.
- Profile models still need a known roster; Info objects do not, and a dodge
  drops the lobby before the deadline arrives, so the sweep now runs for Info
  objects even when no roster is readable.
- A refusal with no Info in hand re-arms exactly one sweep, on the transition —
  not on every 400 ms pass.

`tests/adversarial/build_lobby_search_cooldown.cmd` covers the new policy:
cleared live deadline, wrong vtable, `0` / `-1` / expired / out-of-range values,
a deadline rewritten between the two reads, and a half-readable object.

## What it does not establish

The 30 Sep capture shows the penalty is a server deadline returned in the
polling response (`result 11` plus a Unix expiry), and a search accepted only
after it passed. Clearing client Info changes what this client believes and
displays. Whether the Search gate opens and whether the next poll is accepted is
for a live test, and success after the deadline naturally expires does not count.

Lines to read after a dodge:

- `[LOBBY] Skip search CD info=… expiry=… result=… in=Ns` — a live deadline was
  found during the sweep.
- `[LOBBY] Skip search CD scan done models=… banned=… infos=… live=… roster=…`
- `[LOBBY] Skip search CD info cleared=… kept=… was=… left=…` — the write.
- `[LOBBY] Skip search CD state=… lastError=… result=…` — the service's own view,
  still reporting the last refusal independently of any write.

## Live result, 30 Sep 07:00

Dodged out of a found match with the switch on, build `fa4d571889` injected.

- 07:00:49 `Dodge UI-thread ok obj=…33336CB0 match=253847536`.
- 07:00:56 the next poll: `state=10` (ServerRejected), `lastError=11`. The game
  showed "temporary matchmaking restriction, 7:51 left".
- 07:00:57 the sweep the dodge re-arms: `models=2 banned=0 infos=1 live=0
  scanned=1997 MiB`.

One Info object in ~2 GB of private read/write memory — the copy embedded in
the service — and it carries no deadline. **The remaining time is in no Info
object at all.** The client formats it once per refusal from the transient
response event (`sub_85AEB0` case 11, event+0x170) into a dialog string and
keeps nothing; two screenshots minutes apart show two separate dialogs, not one
counting down.

With `banKinds=0x0`, the saved Info at `-1`, and every Search press reaching the
server (`lastError=0` then `11` at 07:00:15, 07:00:17, 07:00:56), this penalty
has no client-side state to clear. The widened target stays correct for a
deadline that is stored, and it changes nothing for this one.

A second defect did show up and is fixed: the re-arm condition tested the number
of known Info objects, and one dead Info always exists, so after a refusal the
next sweep stayed five minutes away. It now tests whether any known Info carries
a live deadline, and re-arms at most once every 30 s.
