# KickCtor arm aux=5 while the page is committed

2026-09-26, boot `2026-09-26T14:57:05`, sys `437D3D07` (1 126 400, mtime 14:46:07). Ping `pong`. Relic PID **4820**, image `0x7ff69e5f0000`. Do not remap `654F0324`. Hasher arm and hasher protect were skipped.

## What the hold log showed

`docs/_bsod/cycle9-hold.txt` stamp `15:10:48`:

- `skip RA_Hasher 0x3E57050`
- `arm va=7ff6a23c2550 eax=0 status=0 sites=1` (Enqueue `0x3DD2550`)
- `arm va=7ff6a24591f4 eax=0 status=10 (aux=5)` (KickCtor `0x3E691F4`)
- `query cr3=83d1e3000` (DirectoryTableBase; `userdtb_off=0`)
- `hello cr3=5e28f4000` is the caller (`zpp_aoe4`) CR3, not Relic
- script stopped the file and did not retry

`stealth_fail` 5 is `guest_virtual_to_physical == 0` in `npt_stealth.cpp` (`refuse(5)`), before `identity_epte`. Enqueue on the same CR3 walked. `stealth_site_allowed` passed, so the PE header on that CR3 was readable.

## Page state after the failed arm

`docs/_bsod/kickctor-walk.txt` (PID 4820 still responding):

- window `slots=0 accum=0 flag=0` uninit/empty
- VirtualQuery both Enqueue `0x7ff6a23c2550` and KickCtor `0x7ff6a24591f4`: `state=0x1000` (MEM_COMMIT), `protect=0x20` (PAGE_EXECUTE_READ), RPM 16 bytes match the prologues (`44 89 4C 24 20` and `48 8B C4`)
- a later `query --va 0x7ff6a24591f4` got `mailbox no-reply rax=2`. Ping immediately after was still `pong` (15:18:14). That query is not a second stealth arm.

The KickCtor 4K is committed and executable in the process. The HV walk still returned 0 at arm time. Not a soft “page not loaded” result from RPM.

## Second arm, same result

`docs/_bsod/kickctor-arm.txt` stamp `15:19:23`, still PID 4820:

- `query cr3=83d1e3000` (probe VA was 0)
- `arm va=7ff6a24591f4 eax=0 status=10 (aux=5)`
- hitch `npf=139605 hashrec=0 sites=1 orig=0` (Enqueue only; hasher stayed off)
- window still `slots=0` uninit

`docs/_bsod/kickctor-query-va.txt` `15:23:01`: hello `mailbox no-reply rax=2` (`bad_buffer`). Window RPM still `slots=0` on PID 4820. No x64dbg.

`mailbox_resolve_target` does not probe the site VA on `stealth_arm` (that probe was status=8 after the first NX page). If neither DTB reads the VA it still keeps DirectoryTableBase. Enqueue PDE index 273 is in that DTB. KickCtor PDE index 274 is not, even though VirtualQuery shows the 4K committed and executable. A new sys cannot be mapped while this Relic is live and ping was `pong`.


`docs/_bsod/kickctor-query-va.txt` stamp `15:30:10`: `query --va 0x7ff6a24591f4` returned `status=8 cr3=0` (not_found). Plain query on this same boot returns `cr3=83d1e3000`. Hitch at that hello: `npf=213123 hashrec=0 sites=1`. No scanned KPROCESS DTB (`0x20..0x2000`, `ram_dtb` under 34 GiB) can read the KickCtor page. `userdtb_off=0`. WindowWatch and `zpp_at` still `slots=0`. Relic 4820 still responding.

## Working set is valid, walk still fails

`docs/_bsod/kickctor-ws.txt` stamp `15:35:16`. `K32QueryWorkingSetEx` on PID 4820:

- Enqueue `0x7ff6a23c2550` attr `0x5000201` valid=1, not a large page, `PAGE_EXECUTE_READ`
- KickCtor `0x7ff6a24591f4` same attr, valid=1, RPM `48 8B C4`

Immediate arm still `status=10 aux=5` on `cr3=83d1e3000`. Hitch `npf=234527 hashrec=0 sites=1`. The KickCtor 4K is in the process working set. `guest_virtual_to_physical` on DirectoryTableBase still returns 0. `query --va` of that page is `status=8`, so the KPROCESS scan also found no other DTB that can read it. x64dbg was not started. Do not kill Relic while the Enqueue site is armed. Do not map a new sys while ping is `pong`.

## New Relic 5172: header walk fails

PID **5172** started `15:49:57`, same image `0x7ff69e5f0000`, `slots=0`, responding. Hold `15:51:18`: Enqueue `arm va=7ff6a23c2550 status=10 aux=3` (`stealth_site_allowed` / PE layout). No site armed (`sites` stayed 0, `npf` frozen at 681287). Saved CR3 `0x51e39d000`.

`docs/_bsod/relic5172-probe.txt` `15:52:57`: `query --va` of the image base and of Enqueue both `status=8 cr3=0`. No scanned DTB reads this process's `.text`. RPM still sees the unpacked prologues. x64dbg was not started.

## Touch does not make the walk succeed

`docs/_bsod/relic5172-touch.txt` `15:55:03`, PID 5172 still responding. After RPM, both pages are working-set valid:

- image `0x7ff69e5f0000` attr `0x45008023` valid=1, bytes `4D 5A` (MZ)
- Enqueue `0x7ff6a23c2550` attr `0x5000201` valid=1, bytes `44 89 4C 24 20`

Immediate `query --va` of Enqueue is still `status=8`. Header query hello was `rax=2` (`bad_buffer`) and did not return a CR3. Residency is not why the walker misses this `.text`. `npf` still frozen at 681287, `sites=0`. No x64dbg.

Later the same PID was still responding with `slots=0` and about 860 s of CPU time, still with no NPT site. The high CPU is the game, not an Enqueue NPF loop. x64dbg stays off until a CR3 walk of `.text` succeeds.

## KPROCESS offsets on this ntoskrnl

`kd -z ntoskrnl.exe` with public symbols: `DirectoryTableBase` is `+0x028`, `UserDirectoryTableBase` is `+0x158`. Both sit inside the HV probe scan `0x20..0x2000`. The `status=8` miss is not an offset past the scan. `cdb` in this kit has no `-kl` (`Invalid switch 'k'`). `kd -kl` says local kernel debugging is disabled (`bcdedit -debug on` plus reboot). That reboot was not taken: SVM is still the mapped image and Relic 5172 was still `slots=0`.





Application Hang 1002 at `2026-09-26T15:45:12`: Windows closed `RelicCardinal.exe` 16.3.11308.0 because it stopped interacting. Boot stayed `14:57:05` (not wininit `0x50006`). Last hitch before that was `npf=301255 hashrec=0 sites=1` at 15:42, and the process was already `Responding=False` with about 3395 s of CPU. Slots were still 0. x64dbg was not started; the attach script at 15:47 found PID 4820 already gone. Enqueue NPF storm hung the UI. KickCtor was never armed.


`docs/_bsod/kickctor-query-enq.txt` stamp `15:42:07`. `query --va 0x7ff6a23c2550` (Enqueue, already NX) returned `status=0 cr3=83d1e3000` while hitch `npf=301255 hashrec=0 sites=1`. The same walker, during the Enqueue NPF storm, still translates Enqueue and still does not translate KickCtor (`status=8` at 15:30). Window still `slots=0` uninit on PID 4820. Copy-window saturation is not the failure. x64dbg was not started.



`AOE4HOOK\internal\x64\Release\WindowWatch.exe` at 15:27:17 attached PID 4820 base `0x7FF69E5F0000` (toolhelp) and printed `slots=0 accum=0 flag=0` uninit through 15:27:22. Same window as `zpp_at.py window`. RPM only, no inject. Relic still responding after the sample. `DllInjector.exe` was not started.
