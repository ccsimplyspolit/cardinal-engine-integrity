# 2026-09-12 planned reboot + full HV verify

User: ????? ? ???????? ?????. Canon:
aoe4-hv/docs/_bsod/090912-planned-reboot-verify.md,
aoe4-hv/docs/planned-reboot.json.

SVM live from 17:50 (query=8). Reboot, then map sys **17:59:55**, then
query explorer ? Relic ? `hold --apply` ? `prove --sec 60` with x64dbg.exe
OPEN, no attach, no WindowWatch. Goal `verdict=hv_hold`.

If this chat restores on the **same** boot `17:32:28`, do not map and do not
reboot twice. If `LastBootUpTime` is newer and dump is still 091226-10187,
map � this was not a hang.
