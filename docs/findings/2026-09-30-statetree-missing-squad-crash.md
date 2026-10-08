# Crash: StateTree condition reads a squad that is already gone

Fourth occurrence of one crash, and the first one read this far. 30 Sep 14:46:20,
mid-match with the AI session live.

## What the dump says

`release_16_3_0_rtm_x64RFC95D83.dmp`, and three older ones with the identical
signature: 13 Sep 15:12, 13 Sep 23:34, 14 Sep 01:09. Every one of them:

```
code=0xC0000005  read at 0x58   #00 RelicCardinal.exe+0x2A45959
                                #01 RelicCardinal.exe+0x38BC10D
```

Today's thread was 23520, a worker thread — the stack ends in the CRT thread
bootstrap (`0x3B1E250` → `0x3B1EB40` → `0x3B1F270`), not in the sim or UI thread.
Frames `0x38BBFA0` / `0x36414C0` repeat four times: a StateTree walk, each node
evaluated through its vtable. `sub_2A5C880` two frames below names the system —
it builds a `std::function` over `StateTree::IStateController`.

## The instruction and why it faults

`sub_2A45930`, disassembled from the dump (the on-disk `.text` is encrypted):

```
0x2A45946  mov  edx, [rbx+0x10]     ; the node's squad id
0x2A45949  cmp  edx, -1
0x2A4594C  je   0x2A45987           ; unresolvable -> return 4
0x2A45951  call 0x2924350           ; find that id in the owner's lists
0x2A45956  mov  r10, rax
0x2A45959  mov  ecx, [rax+0x58]     ; <-- AV, rax = 0
```

`sub_2924350` walks two lists (`owner[531]..owner[532]`, then
`owner[534]..owner[535]`) for an entry whose `+8` equals the id, and **returns 0
when neither holds it**. The caller never checks. So a state-tree node holding
the id of a squad that died between evaluations reads offset `0x58` off null.

The function already knows that answer: both earlier guards — a null owner and
`id == -1` — jump to `mov al, 4` at `0x2A45987`. Only the lookup result is left
unguarded.

## Why it lands on us

Nothing here is our code: the null read is Relic's, on Relic's thread. What we
do is feed that state tree a lot of short-lived ids. The half second before the
crash, `warnings.log` shows 27 locks in a burst —
`[STK] AI_LockSquad spawn sid=50800 … sid=50826`, 14:46:18.367 → 14:46:18.882 —
and our log has `ai_lock_army_relock`, `ai_sel_release` and
`stamp lock flags live-stack=89 already=71 ai-owned=1` in the same seconds. The
more squads are locked to the AI and die under it, the likelier this window is.

`last_native=army relock scan` in the crash block is the usual lie: that crumb is
rewritten every ~400 ms and names itself at any late crash.

## The fix

A fourth VEH recovery beside the three that already exist
(`TryRecoverStateTreeMissingSquad`, after the RA handler and the other three).
It fires only on: access violation, **read**, fault address exactly `0x58`,
`rax == 0`, RIP exactly at `0x2A45959`, and the byte patterns matching both at
the faulting instruction (`8B 48 58 83 E9 02 83 F9 01`) and at the resume point
(`B0 04 48 83 C4 20 5B C3`). It then sets RIP to `0x2A45987` — the game's own
"cannot resolve this reference" exit, which returns 4 through the same epilogue,
so rsp and rbx unwind exactly as they would have.

No memory is written, no Relic code is patched, and any other fault keeps
crashing as before. The log records `[RECOVER] StateTree squad gone` on the first
two hits and then every 1024th.

Not verified in a live match yet: the next AI session with heavy squad churn is
the test, and the line to look for is that `[RECOVER]` one.
