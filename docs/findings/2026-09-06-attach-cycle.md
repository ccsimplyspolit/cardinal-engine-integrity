# 2026-09-06 — standing attach cycle (post-0x10E, cloak off)

Safe cycle after BugCheck `0x10E`. CRT cloak stayed default-off. No `AOE4H_RA_CLOAK`, no `--ra-veh`, no PAGE_GUARD, no IDA MCP, no commit.

## Verdict

| Ask | Result |
|-----|--------|
| Injected after reboot? | **Yes once** — PID **37124**, 16:42:43 |
| `[RA] neutralize ON` | **Yes** `inline-ret+VEH+5byte` `veh=0` |
| `[RA] integrity cloak ON` | **Absent** — log has `[RA] integrity cloak OFF` |
| Slots | Window **uninit/empty** (`begin=0 end=0`) — no `slots=3` pack |
| Present ≥30s? | **No** — first Present then **BEX64 `0xC0000005` ~1 s** |
| x64dbg attach | **Not done** (process already dead; `:3000` down) |

Not the 16:19 cloak / VidMm `0x10E` path. Detail: [inject 37124 AV](2026-09-06-inject-37124-crash.md). BSOD: [0x10E CRT cloak](2026-09-06-bsod.md).

## 37124 (the only completed inject)

| Field | Value |
|-------|--------|
| PID | 37124 |
| Relic base | `0x7FF6F92A0000` (16.3.11308.0) |
| DLL then | `Release\InternalInjector.dll` 13 453 312 B, 16:40:36 |
| OverlayBoot | 16:42:43.012 |
| `-nodbg` | forced RVA `0x844B2ED` |
| Hide | `user32_body=3` Watcher titles |
| Neutralize | `d02c`/`f448` pass; enqueue/timerq fail; watcher+sibling `ret 1`; no kick stub |
| Cloak | CRT **OFF**. Engine `cloak=1 cloakGuard=0` is overlay `.text` shadow only |
| First Present | 16:42:43.748 DXGI12 ok, `present_hr=0`, no `[GPU] AV` |
| RA snapshot | `uninit/empty` 16:42:43.817 |
| Dead | 16:42:44 Event 1000; WER dump `RelicCardinal.exe.37124.dmp` |

## This agent after 37124 died

Relic was **DOWN** at 16:44. Steam **19688** still up. Newest DLL map timestamp **16:45:04** (`6a9d6e60`) — cloak-off rebuild, no MSBuild lock.

Tried relaunch:

1. Steam `-applaunch 1466860 -dev -nodbg` (pid 36652 resumed).
2. Frida `spawn` RelicCardinal `-dev -nodbg` → PID **37584** (Frida stayed attached — dirty; not the Steam-only path).
3. `DllInjector.exe` Frida-spawn **failed `0x000002E4`** (elevation required). `cmd start` launched so UAC can pop. Overlay log **did not** rotate — no second OverlayBoot.

Frida MCP then timed out on `RelicCardinal`. x64dbg HTTP not used.

## Blocked on

User: if a UAC prompt for `DllInjector.exe` is up, **approve it**. Prefer a **clean Steam** Relic (kill 37584 if it is the Frida-spawned one), then run:

`K:\aoe4_dlc\hh\AOE4HOOK\internal\x64\Release\DllInjector.exe`

(no extra args; default = neutralize + hide, not `--ra-veh`).

Success next time = neutralize ON, cloak OFF, slots stay 0 after x64dbg, Present ≥30s without BEX64.
