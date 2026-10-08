# 2026-09-26 — Present thread DEVICE_HUNG then Relic AV `0x3AD6A86`

Session from overlay log `Documents\AOE4HSettings\Logs\aoe4_internal.prev.log`. Boot of that Relic `00:40:38`, death `01:30:59`. Relic base `0x7FF690AB0000`. New Relic **17196** started `01:31:56` (host stayed up).

## Sequence

| Time | What |
|---|---|
| 01:30:56 | Match still live: AI French, `simTick=23336`, window tid **27356** |
| 01:30:59.202 | `[PRESENT] device-dead` `0x887A0006` DXGI_ERROR_DEVICE_HUNG, reason same |
| 01:30:59.203 | DRED `hr=0x887A0004` **nodes=0** (no GPU breadcrumb) |
| 01:30:59.205 | Present returned `0x887A0005` DXGI_ERROR_DEVICE_REMOVED, `1680x1050` |
| 01:30:59.208 | VEH `0xC0000005` write to `av_addr=0` rip=`0x7FF694586A86` **rva=`0x3AD6A86`** tid **27384** (Present, not the window thread) |
| 01:30:59 | `nvlddmkm` event **153** |
| 01:31:05 | WER LiveKernelEvent **141** dumps `WATCHDOG-20260926-0130.dmp` and `WATCHDOG-20260926-0131.dmp` |

Registers: `rdi=0x887A0006` still the hung HRESULT. `scar_tid=0` `in_call=0`. `last_native=army relock scan` is a stale breadcrumb, same as [cycle 8g](2026-09-13-hv-cycle8g-freeze-then-41.md) and the 16:09 note in `AI_SESSION_HANDOFF.md`.

No `[PRESENT] stalled` / `gpu_fault` in the seconds before this death. No Event **41**. Patch Game AUTO was not in this path (follow-up inject `01:32:49` still reports `slots=3`).

Earlier the same night: `nvlddmkm` 153 at `00:36:17` and Kernel-Power reboot `00:36:47` (`WATCHDOG-20260926-0036.dmp`). That one reset the host. This `01:30` one only killed Relic.
