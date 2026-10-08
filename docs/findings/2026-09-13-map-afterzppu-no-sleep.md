# Map-AfterZppu was slow because of sleeps, not kdu (2026-09-13)

Mailbox ops 1–12 unchanged. **Do not map.** Event **41** `20:49:03`
(Cycle 8g TDR) is still the stop. This is a wall-time fix for the map
script, not a hang fix.

## Point

`Start-Process -Wait` on `Map-AfterZppu.ps1` only waits for the child
to exit. The child used to sit for ~1–3 min **before/after** `kdu`:

| Wait | Where | What it did |
|---|---|---|
| WaitAlive up to 12 s | `Start-ZppHitchWatcher -WaitAliveSec 12` | Poll `hitch-host.log` for `i=0` before `kdu`. First `Get-Counter` in `Watch-ZppHitch.ps1` can stall the file. |
| 12 × 1 s `KeDelay` | `zpp_hitch_watch` in `windows_loader` DriverEntry | `kdu -map` does not return until DriverEntry finishes. |
| Poll up to 50 s | `Map-AfterZppu` / `Start-ZppLoader` after mapper | `Start-Sleep 200ms` until `load_ok` / `hitch_watch_end`. `Start-ZppLoader` waited on `hitch_watch_end` even after `load_ok`. |

`-Seconds 90` on the hitch watcher was **background** duration, not a
parent sleep. Outer `-Wait` is ExitCode.

## Change (source)

- `Start-ZppHitchWatcher` default `WaitAliveSec=0` (spawn, return).
- `Map-AfterZppu.ps1` / `Start-ZppLoader.ps1`: no 50 s poll, no
  `Start-Sleep` around `kdu`. Read `zpp_loader.log` once after mapper.
- `zpp_hitch_watch`: one snapshot, `hitch_watch_begin` /
  `hitch_watch_end` still logged. Host `Watch-ZppHitch.ps1` still
  samples DPC/ISR in the background (`Sleep 1` there does **not**
  block Map-AfterZppu).
- Leftover `sc stop ZppLoader` no longer sleeps 1 s.

## Not this

- Not permission to map. Gate **21**, `launch_authorized=false`.
- Not a Present QPC / DXGI TDR fix. Do not remap `7B5C8989`.
- Disk `zpp_loader.sys` stays the 8g corpse until a later rebuild;
  the 12 s `KeDelay` is gone in **source**. Rebuild when the next
  authorized image is built — do not map a hitch-stripped 8g clone
  as if 8g were fixed.
