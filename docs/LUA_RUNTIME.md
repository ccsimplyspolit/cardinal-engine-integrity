# Lua in the game, in the tools and in the tests

**Conclusion: the SCAR VM of RelicCardinal 16.3.11308.0 is Lua 5.3, sandboxed.
Confidence: high** — two independent sources agree, one from the binary and
one from a live match. Everything the overlay sends (embedded C++ literals,
`sdk/` scripts, user Files) runs on that VM.

Several documents said "Lua 5.1" until 2026-09-27; that was never measured.
The code was already written for both (`WrapScarCompileSafe` tries
`loadstring`, then `load`), so nothing broke, but the tests ran on lupa's
default Lua 5.5 and proved nothing about the game.

## Evidence

| # | Source | What it shows |
|---|---|---|
| 1 | `reversed/03D00000/sub_3D17E50_0x3D17E50.c` (Hex-Rays export, image base `0x7ff7a5500000`, RVA `0x3D17E50`) | `luaopen_base`: registers `_G`, then interns `"Lua 5.3"` through the string cache indexed `% 0x35` (`STRINGCACHE_N = 53`, new in 5.3) and stores it as `_VERSION`. The tag `\| 0x40` is 5.3's collectable bit |
| 2 | `sdk/scar/vm_census.json` (`dump_vm.scar` run in a 16.3.11308.0 match, read back from `warnings.log`) | `_VERSION = "Lua 5.3"`. Present: `utf8` (6 keys), `table` (7: the 5.3 set with `move` / `pack` / `unpack`), `coroutine`, `string` (18), `math` (25), `load`, `loadfile`, `rawlen`, `select`, `xpcall`. Absent: `loadstring`, `setfenv`, `getfenv`, global `unpack`, `module`, `bit32`, `io`, `os`, `debug`, `package`, `require`, `dofile`, `jit`. Constants carry the integer / float subtype (660 integer, 7 float) |

Limits of the evidence: the census lists what `dump_vm` enumerated in that
session; which two of the 27 standard `math` keys are missing is not
recorded (only counts per table). Relic may patch the interpreter in ways a
census does not show.

## What follows for scripts the overlay sends

1. **They must compile and run on 5.3.** The host tests now run the shipped
   scripts on `lupa.lua53` (`tests/adversarial/game_lua.py`);
   `test_scar_compile.py` compiles every `sdk` script on 5.3.
2. **No `io`, `os`, `debug`, `package`.** Every `io.open` in
   `stk_lua_lock.cpp` sits behind `type(io) == "table"` and never runs in the
   game: those files (`aoe4_scar_last.txt`, `aoe4_*_pending_*.txt`, the army
   clock) are written by nobody. The live Lua → C++ channel is `print` into
   `warnings.log`, tailed by `scar.cpp` (see `docs/SCRIPT_BRIDGE_CONTRACT.md`).
3. **`loadstring` is absent.** `WrapScarCompileSafe` falls back to `load`.
4. **Numbers have two subtypes.** A literal `3` is an integer, `3.0` a
   float. `tostring(3.0)` is `"3.0"`, not `"3"`; `string.format('%d', 2.5)`
   raises "number has no integer representation"; `t[1.0]` and `t[1]` are
   the same key. A Lua line that C++ reads with `%d` / `strtoul` must print
   an integer (`string.format('%d', math.floor(x))`, or a value that is an
   integer already). `math.floor` returns an integer when it fits.
5. **Integers are 64-bit.** `string.format('%d', token)` prints a 32-bit
   unsigned token unchanged; the 31-bit mask on the age token
   (`ai_runtime.cpp`) is not needed on 5.3 and is kept only because it is
   harmless.
6. **Engine enums are userdata, not numbers.** `OT_Neutral` is
   `OwnerType(3)`, `SCMD_Gather` is `SquadCommandType(105)`, `R_ENEMY` is
   `Relationship(1)`. `type(OT_Neutral) == 'number'` is always false; test
   `X ~= nil`. `AGE_DARK` and `PBG_*` are plain integers.
7. Limits worth remembering: 200 C levels (`too many C levels`), 200 locals
   per function, 255 upvalues.

Policy: keep writing the common 5.1 / 5.3 subset (no `goto`, `//`, bitwise
operators, `utf8`) unless a feature is needed; the game accepts them, but
nothing in the overlay needs them and user scripts copy what they see.

## Interpreters that are not the game

| Where | Lua | Used for |
|---|---|---|
| RelicCardinal SCAR VM | 5.3, sandboxed | everything above |
| `tests/adversarial/*.py` | `lupa.lua53` via `game_lua.py` | executing shipped scripts on mocks |
| `tools/test_*.py`, `tools/audit_parse_all.py` | `lupa.lua53` | the same |
| `tools/audit_ai_scoring.py` | none (lexer) | static inventory |
| Cheat Engine autorun | LuaJIT (5.1) | unrelated to the game (`docs/findings/2026-09-06-ce-lua-path.md`) |

A mock run proves the script's protocol and branches on 5.3 semantics, not
what a Relic native returns.
