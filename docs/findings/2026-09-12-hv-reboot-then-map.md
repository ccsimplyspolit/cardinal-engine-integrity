# 2026-09-12 planned reboot then map 16:50

User: reboot + launch, **no autostart**.

This boot still has TSC-hide ELF (15:21, leftover=135). Cannot map query+protect+nop5 on top of SVME. Planned reboot clears leftover.

- No schtasks / RunOnce / HostPrep hook
- zpp_loader.sys 16:50:15 (1046528 B) stays on disk
- cycle-state.json: 
eady_to_launch, launch_authorized=true
- After desktop: user says запускай -> docs/Start-ZppLoader.ps1 then Steam -dev -nodbg -notrap
- Relic is not first VMRUN
- Do not inject overlay for the HV ping; hold --apply after Relic titled window
