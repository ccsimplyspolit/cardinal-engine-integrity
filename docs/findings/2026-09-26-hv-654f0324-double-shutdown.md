# 2026-09-26 — `654F0324` load_ok, then two unexpected shutdowns

No bugcheck code. `CrashDumpEnabled=0`. `C:\Windows\Minidump` empty.
`MEMORY.DMP` is still 2026-09-12. BlueScreenView: `minidump_count=0`.

## Timeline

| Time | Evidence |
|---|---|
| 14:20:27 | `kdu` map sys `654F0324` (1 125 888). `userdtb_off=0`. `stage=load_ok`. |
| 14:20:28–14:23:32 | `hitch-host.log` `vmcall_skip`, `irql=0`, ISR near 0. Watcher ends. Not the crash. |
| 14:24:21 | ping `pong`. Relic not running yet. |
| 14:26 | Hold PID 20756, base `0x7ff76b3f0000`, `slots=0`, then `RA_Enqueue` `status=10` `aux=0`. Script kills Relic. Overlay: RPM err 299. |
| 14:30 | Second hold PID 35828, same base, same `status=10`. Script kills Relic. |
| 14:31:04 | Unexpected shutdown. Event 41 14:32:42. Boot 14:32:38 `ping=ping_err`. |
| 14:35:49 | Second unexpected shutdown. No new `kdu` (`zpp_loader.log` still 14:20:27). Event 41 14:37:36. Boot 14:37:32 `ping=ping_err`. |

Captures: `aoe4-hv/docs/_bsod/crash-20260926-143306`, `crash-20260926-143759`.

## Hold

`stealth_arm` returned `hook_failed` on the first site (`0x3DD2550`) before any site was counted. An MZ probe on the image base still got `status=10` (`debug-239639.log`). That probe was reverted. Do not remap `654F0324`.

New sys `437D3D07` (1 126 400 bytes, 14:46) is built and not mapped. On a failed arm, mailbox `aux` is `stealth_fail` instead of 0: 3 PE layout, 5 GPA walk, 9 identity split, 13 insn cover, 16 insn boundary, 17 NPT walk. `launch_authorized` stays false.
