# Always elevate (user 2026-09-13 17:18)

User: запускай **всё** под администратором. Medium-IL Cursor is not a
valid launch context.

Written into:

- `.cursor/rules/run-as-admin.mdc` (alwaysApply — full tool list)
- `.cursor/rules/aoe4-hv-bsod-gate.mdc` (Capture elevated)
- `.cursor/skills/aoe4-hv/SKILL.md` + `.agents/skills/aoe4-hv/SKILL.md`

Evidence this boot: unelevated `Get-ScheduledTask` / `schtasks` → Access
denied (looked like HostPrep missing); unelevated read of
`C:\Windows\Temp\zpp_loader.log` → Access denied. Register-HostPrep log
on K: already said registered 17:17:25.

Does not authorize map. Gate still 21. Cycle 3 sys still corpse.
