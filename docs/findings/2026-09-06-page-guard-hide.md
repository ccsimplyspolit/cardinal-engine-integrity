# 2026-09-06 — PAGE_GUARD as a hide for injector writes?

User: maybe PAGE_GUARD hides hooks from RA.

## Verdict

PAGE_GUARD **can** hide a *read* of **one page** if we own first-chance VEH
and restore a shadow, then TF + re-arm. It does **not** give `slots=0`,
does **not** replace FlushArm heartbeat, and on **this** Relic it already
failed in the ways that matter for RA `.text`.

## What the mechanism is

```
VirtualProtect(page, PAGE_EXECUTE_READ|PAGE_GUARD)
RA read / CPU fetch → STATUS_GUARD_PAGE_VIOLATION
VEH: show original (shadow) or allow execute → Trap Flag → re-arm
```

Hasher `0x3E57050` raw-loads the **source** before memcpy. A guard on the
hooked page *would* fire on that load — in theory.

## What already happened here

| Try | Result |
|---|---|
| KiUser steal + IntegrityCloak PAGE_GUARD | Relic **owns** the KiUser slot for UD2 (`0xC000001D`). Guard armed, **hits=0** via KiUser alone. Process-kill class. Engine Start = **shadow only**, `cloakGuard=0` |
| VEH first-chance | MapHack uses this (`AddVectoredExceptionHandler(1)`). Comment: KiUser alone had hits=0 |
| PAGE_GUARD on Relic integrity AOB `0x3E77BD2` | **kills** the process (not even memcpy) |
| PAGE_GUARD on RA `.text` | comment in engine: **slots=3** |
| CRT `memcpy` 14-byte cloak (not PAGE_GUARD) | BugCheck **`0x10E`** / nvwgf2umx — [bsod](2026-09-06-bsod.md) |

Relic itself plants `PAGE_EXECUTE|PAGE_GUARD` (`0x110`) on its pages
(crack `Engine::Start`). A second guard on the same page is a fight with
their UD2 path.

## What PAGE_GUARD cannot cover

| Surface | Why |
|---|---|
| SNAP heap clones | memcmp heap vs live; guard on `.text` does not update the clone. After first copy they already have hooked bytes if they read while unguarded |
| 7AB0 switch / 77E8 | not a page-read of your hook; IAT pack from opcode path |
| WW slots | GetWindowText / path, not `.text` guard |
| FlushArm expire | deadlines, not pages — [heartbeat](2026-09-06-flusharm-heartbeat.md) |
| One-shot race | guard clears on first access; second thread sees hooked bytes |

## If we ever try again (narrow)

1. Guard **only** the 4 KiB of **our** hook, never RA `0x3DD0000–0x3F90000`
2. First-chance **VEH**, never steal KiUser
3. Shadow = bytes **before** WPM
4. On guard: if RIP is Hasher/Walker → serve shadow; if RIP is our trampoline → execute
5. TF re-arm every hit. No CRT splice. No `AOE4H_RA_CLOAK`
6. Lab `plan` already `safe` (outside SNAP∪RA) — then PAGE_GUARD is optional insurance, not the emu

## Lab this turn (no KiUser, no CRT)

`ra_text_cloak.cpp`: first-chance VEH, one page, dest0 **`0x6AC153`** (outside RA,
52920 leftover sample). Probe copies live→orig=hook (no patch). Reader
(RIP off-page) memcpy orig; execute (RIP on-page) leaves bytes; TF re-arm.

Debug → **Dev: Relic .text PAGE_GUARD (Hasher probe)**.
`EngineWriteRelicText` + `AOE4H_RA_TEXT_CLOAK=1` arms the written span.

Do not arm together with IntegrityCloak KiUser. Do not probe RA pages.

Do not arm Debug IntegrityCloak / Relic `.text` guard on a hold PID.
