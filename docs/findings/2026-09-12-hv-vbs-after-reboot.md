# 2026-09-12 planned reboot 19:45 � VBS Running, do not map

Planned reboot after sys **19:23:33** mapwin. Newest dump still
`091226-10625-01.dmp` 18:28:48 (0x1AA) � not a new BSOD.

| | |
|---|---|
| LastBootUpTime | **2026-09-12T19:45:14** |
| HypervisorPresent | **True** |
| VBS | DeviceGuard status **2 Running**; systeminfo hypervisor detected |
| Relic | not running |
| ping | `ud` (no SVM � expected) |
| sys | `zpp_loader.sys` 1054720 B, 19:23:33 |

Do **not** KDU-map on this boot. Type-2 SVM on Windows HV = nested.

Root cause this boot: optional feature **HypervisorPlatform was Enabled**
(Windows Hypervisor Platform). BCD `hypervisorlaunchtype` was already Off.
Leftovers 19:50�19:53: disabled HypervisorPlatform (`RestartNeeded=True`),
DeviceGuard=0, HVCI=0, HvHost/vmic* Start=4. `hvservice` still Running until
reboot. VBS still status 2 until reboot � **do not map**.

Next: reboot, then map sys 19:23 only if `HypervisorPresent=False`.
