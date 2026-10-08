# 2026-09-26 — Cursor logon: one elevated window, no delay

Live autostart was task `Cursor-aoe4-hv`: AtLogOn, **RunLevel Limited**, **Delay PT10S**, action `cmd.exe /c Start-CursorAoe4Hv.cmd`. HKCU Run and both Startup copies of that cmd were present, StartupApproved first byte `0x03` (Explorer skips them). Log `aoe4-hv/docs/last-cursor-autostart.log` shows one `cmd-start` per boot, then `launching` and `retry launch` three seconds later.

`Start-CursorAoe4Hv.ps1` treated “no `MainWindowHandle`” as “not started”. Cursor’s Electron process stays at handle 0 for a few seconds, so every boot opened a second window. The 10s trigger delay is the late start. Limited is why the window was not admin.

The 2026-09-07 17:22 BSOD deleted the previous Highest task along with an empty Startup folder. That was session loss. It is not a reason to keep the Limited delayed task.

## Now

`Register-CursorLogonTask.ps1` (also section 3 of `Install-VmrunCycleHost.ps1`):

- removes user Startup, all-users StartUp, HKCU Run `Cursor-aoe4-hv`
- one task: `PC-ZFL31Q\sshunko`, Interactive, **Highest**, delay unset, priority 4
- hidden `Start-CursorAoe4Hv.ps1`
- script starts a second process only when no `Cursor` process exists

`Aoe4Hv-HostPrep` is unchanged.

Applied 2026-09-26 14:43: task Ready, user `PC-ZFL31Q\sshunko`, RunLevel Highest, Logon Interactive, Delay empty, priority 4, MultipleInstances IgnoreNew. HKCU Run and both Startup copies removed.
