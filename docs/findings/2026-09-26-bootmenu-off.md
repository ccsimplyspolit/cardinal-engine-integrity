# 2026-09-26 — boot menu off, straight into Windows 11

User: the Windows bootloader asks every startup whether to run a memory check or enter Windows.

Live `{bootmgr}` before the change:

- `displaybootmenu Yes`
- `timeout 10`
- `default {current}` = Windows 11 (`\WINDOWS\system32\winload.efi` on `C:`)
- `displayorder` is only `{current}`
- `toolsdisplayorder {memdiag}` = Windows Memory Diagnostic (`\EFI\Microsoft\Boot\memtest.efi`, description `Windows Memory Diagnostic`)

That forced menu is the prompt. Tab selects the memory tester. It is not HVCI / Memory Integrity (`HypervisorEnforcedCodeIntegrity\Enabled=0` on this boot). Firmware `{fwbootmgr}` timeout stays 1s and the first entry is still `{bootmgr}`.

Applied elevated:

- `bcdedit /set {bootmgr} displaybootmenu No`
- `bcdedit /timeout 0`

Verified `{bootmgr}`: `displaybootmenu No`, `timeout 0`, `default {current}`. `{memdiag}` remains a tool, not a boot entry.

Next boot should enter Windows 11 with no menu. WinRE is Shift+Restart from the sign-in screen. Do not set `displaybootmenu Yes` again unless asked.
