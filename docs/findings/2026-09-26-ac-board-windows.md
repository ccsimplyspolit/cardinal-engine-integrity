# 2026-09-26 — anti-cheat vs this board / Windows

Host inventory only. Boot `2026-09-26T00:37:32`. `HypervisorPresent=False` (same boot as [HV launch refused](2026-09-26-hv-launch-refused-event41.md)).

## Board the PCI tree actually is

| Source | Value |
|---|---|
| CPU | AMD Ryzen 9 7950X, Family 25 Model 97 Stepping 2, CPUID `00A60F12`, socket AM5 |
| SMBIOS baseboard | ASUSTeK `ROG CROSSHAIR X670E HERO` Rev 1.xx |
| PCI | AMD `1022` Promontory 21 (`43F4`/`43F5`/`43F6`/`43F7`), PSP 11.0 `1649`, FCH `790E` rev `51`. Subsystem on PSP / USB / root ports: **`1043:8877`** (ASUS) |
| SMBIOS type 0/1 | BIOS `1.0.2` dated `2021-04-09`; system product `MS-7C72F`; family `B463S885Z9`; SKU `A089S348O7` |

`1.0.2` / April 2021 is not an X670E HERO firmware (board is 2022+; public ASUS versions are `34xx`–`40xx`). `MS-7Cxx` is an MSI product-id shape. PCI vendor `1043` and the baseboard string agree on ASUS AM5; the other SMBIOS strings do not.

### Raw table (same boot, 3721 bytes, SMBIOS 3.6)

The kernel table is one firmware image, not two boards. `mssmbios.sys` is the normal publisher. No second SMBIOS filter driver is loaded, and `HypervisorPresent` is false, so this boot is not rewriting the table in the guest.

What still identifies the Crosshair X670E Hero firmware:

- Type 40 string: `AGESA!V9 ComboAm5PI 1.3.0.1b Patch A` (public Hero BIOS **3901**, 2026-06-30; not **4003** / 1.3.0.1d from 2026-09-22)
- Type 40 entry `YEAR` = `0x07E6` (2022). Type 0 numeric BIOS revision bytes are **3.13**; extended ROM size **32 MB**
- Type 40 labels include ASUS-side tokens `ROG`, `Mordor 1.11`, `PRODUCT_LINE`, `PRODUCT_SKU`, `FEATURES` (names of the entries, not the system product)
- Ports/slots that match this board and not a generic AMI image: `USB4_EC1/2`, `SATA6G_E12`, `W_FLOW`, `W_PUMP+`, `AIO_PUMP`, `PCIEX16_1/2`, `M.2_1`–`M.2_4`, `ADD_GEN2_*`, `OSC_SENSE`
- Onboard: `Nuvoton NCT6799D-R`, `Intel I225 2.5G LAN`, `PROM21`, `ASM1061`
- Type 2 product left as `ROG CROSSHAIR X670E HERO`, version `Rev 1.xx` (stock ASUS text), board type motherboard
- UUID last six bytes `58 11 22 AB A3 03` match the I225 instance tail `581122…ABA303` (`SUBSYS_87D21043`). UUID was not replaced with a random MSI identity
- PCI: 14 functions `1043:8877` (root, PSP 11.0, USB, SMBus). I225 is `1043:87D2`. ASM1061 is `1043:858D`. The RTX 5080 is a separate MSI card (`1462:5313`), not `MS-7C72F`

Fields that were rewritten (what `msinfo32` shows):

| Structure | Field | Value | Why it is not this firmware |
|---|---|---|---|
| Type 0 | BIOS version string | `1.0.2` | Numeric revision is 3.13; AGESA is the 3901-generation string |
| Type 0 | Release date string | `04/09/2021` | Type 40 year is 2022; AGESA Patch A is a 2026 drop. X670E did not exist in April 2021 |
| Type 1 | Product | `MS-7C72F` | MSI-shaped id. Manufacturer byte still says `ASUS` |
| Type 1 | Serial | `1980111632998` | 13 digits; not the 15-digit baseboard serial |
| Type 1 | SKU / Family | `A089S348O7` / `B463S885Z9` | Same generator: letter, 3 digits, letter, 3 digits, letter, digit |
| Type 11 | OEM string 3 | `BOURBON` | Other OEM slots and the chassis strings are AMI `Default string` |

Type 2 serial `220707901402934` does not use that generator (15 digits, `2207…`) and was left next to the real product name. Chassis manufacturer/version/serial/asset are `Default string`, which ASUS often ships unfilled; that part alone is not the edit.

So the DMI string slots Windows prints first (BIOS version, date, system model, SKU, family, one OEM string) were overwritten in the firmware table. The binary fields, AGESA string, port map, and baseboard product were not. A usermode hook would not change `MSSmBios_RawSMBiosTables`.

### 4003 staged, not flashed (2026-09-26)

Official latest is BIOS **4003** (2026/09/22), AGESA ComboAM5 PI **1.3.0.1d**. Zip `ROG-CROSSHAIR-X670E-HERO-ASUS-4003.ZIP` from `dlcdnets.asus.com`, SHA-256 `9637F489BD24D2A102F0F59459E8A487675D4F44DAA2DB815678B580500C0AF9` (matches the ASUS API). Extracted CAP `33558528` bytes, SHA-256 `366DF18915A660DC971E1BA4120A922FF8E9CE7E2B843F10BD39AAB736068A71`. `BIOSRenamer.exe` from that zip produced `CX670EH.CAP`. Copies: `Desktop\ASUS-BIOS-4003\CX670EH.CAP` and `D:\CX670EH.CAP`.

The CAP does not contain `1.0.2`, `MS-7C72F`, or `BOURBON`. It does contain `ROG CROSSHAIR X670E HERO`. UEFI variables `SmbiosScratchBuffer` / entry-point tables under `{4b3082a3-80c6-4d7e-9cd0-583917265df1}` are 8 bytes, not the string table. No `DmiVar` variable. The edited strings sit in the DMI region a normal ASUS flash keeps, so 4003 will move AGESA to 1.3.0.1d and can leave `1.0.2` / `MS-7C72F` / `BOURBON` in place.

BitLocker is off on C: and D: (`manage-bde`, elevated). No USB disk is attached, so the rear Flashback button cannot run. Flash was not started: EZ Flash needs the firmware screen. Local `Desktop\ASUS-BIOS-3902\CX670EH.CAP` is a different image (CAP SHA-256 `A401AEAD4A6EA0BBD451A66627F995094B5471A6FB8BF87A774B86375049A7C0`), consistent with the running AGESA 1.3.0.1b Patch A (3901/3902), not with 4003.

Public Hero BIOS (station-drivers, page touched 2026-09-22): **4003** (2026-09-22) AGESA ComboAM5 PI **1.3.0.1d**; **3901** beta (2026-06-30) 1.3.0.1b Patch A adds Granite Ridge TSME; **3513** (2026-01-30) Pre-1.3.0.0 “for better security”; **3603** (2026-03-18) fixes a BitLocker recovery prompt. ASUS’s own FPS-launch note still says kernel anti-cheats want Secure Boot plus fTPM 2.0.

## Windows

`systeminfo`: Windows 11 Pro Insider Preview **10.0.26340** build **26340**. That is experimental **26H2** enablement **KB5124114** (2026-09-11), which expands automatic Memory Integrity (HVCI) onto eligible PCs and keeps an existing off choice. Kernel file `ntoskrnl.exe` is **10.0.26100.9482**, mtime 2026-09-13 — expected for a 26H2 enablement package on the 26100 Germanium kernel (`BuildLabEx` `26100.6.amd64fre.ge_release_flt.260716-1700`).

Also installed 2026-09-13: KB5124108 (Security), KB5126054, KB5122776 (`26100.9071`). Retail September cumulative is KB5124008 (26100.9445 / 26200.9445). Preview KB5124010 (2026-09-22) goes to 26100.9550 / 26200.9550 / 26300.9550 — this box is still UBR **9482**.

October 2026 quality updates are scheduled to turn Memory Integrity on where it was never configured. This machine already has it off.

## Features those drivers look at

| Feature | This boot |
|---|---|
| Secure Boot | `UEFISecureBootEnabled=0`. DeviceGuard available bits `1,3,5,6,7,8` — bit 2 (Secure Boot) absent |
| TPM | `Win32_Tpm` returned no instance |
| VBS / HVCI | VBS status 0. `HypervisorEnforcedCodeIntegrity\Enabled=0` |
| Kernel CET | `KernelShadowStacks\Enabled=0` |
| Vulnerable-driver blocklist | `VulnerableDriverBlocklistEnable=0` |
| Code integrity | `CodeIntegrityPolicyEnforcementStatus=1` (audit) |

## Drivers on disk

| Driver | When | Notes |
|---|---|---|
| `BEDaisy.sys` | 2026-09-24 23:11, 39 777 008 bytes | WHQL, Microsoft HW Compatibility Publisher, valid. `BEService` **Disabled / Stopped**. Same-day `BEService.exe` and `BEService_activematter.exe`. Older leftovers: `BEService_eft.exe` 2025-12-13, `BEService_pubg.exe` 2025-11-10 |
| `EasyAntiCheat_EOS.sys` | 2026-08-02 20:59, 24 050 664 bytes | EAC Oy cert valid, **expires 2026-10-29**. Service Disabled / Stopped |
| `xhunter1.sys` | file 2025-12-19, version **2023.12.7.78** | Wellbia System Guard. Signer cert **expired 2025-08-20** (timestamp still makes Authenticode Valid). `C:\WINDOWS\xhunter1.sys`, start Manual, Stopped |
| `vgk.sys` / FACEIT | not installed | |

No vendor publishes a BE/EAC changelog for these exact files. Public trail around them:

- DayZ ticket DZG-859 (2026-09-20): `BEDaisy.sys` dated **2026-09-17** then bugcheck `0x7E` at `BEDaisy+0x35364`. Local file is seven days newer (09-24). No newer public note.
- BattlEye FAQ: Hardware-enforced Stack Protection still blocks driver load (error 1275) until a Windows unblock; their own fix is not enough. CET is off here, so that block is not the current state.
- EAC + the same CET feature still reported broken on Epic’s side as of 2026-08-22.
- VRChat dumps (July–August 2026): `EasyAntiCheat_EOS.sys` in a perf-interrupt stack walk, `MEMORY_MANAGEMENT`, on AM5 ASUS (X870E) with VBS on. Local EOS file date is 2026-08-02, inside that window. VBS is off here.
- Retail August KB5121003 (26100.9168 / 26200.9168) tightened kernel handle checks and took down games plus some anti-cheat paths (`inpoutx64.sys` was the named third-party driver). This kernel file is newer than that UBR.
- Vanguard On-Demand (public write-up current as of 2026-09-13) stays boot-resident unless the box is Windows 11 **25H2+** with Secure Boot, TPM 2.0, VBS, HVCI, and IOMMU all on. `vgk` is not on this machine. Secure Boot, TPM, VBS, and HVCI are off, so that bar is not met.

## UnknownCheats (2026-09-26 search)

No thread names this board (`X670E HERO` / `1043:8877`) or build `26340` / `26100.9482`. No post matches local `BEDaisy.sys` 2026-09-24 or `xhunter1.sys` 2023.12.7.78.

What does match this Windows:

- [EAC rolling out HVCI requirement](https://www.unknowncheats.me/forum/anti-cheat-bypass/723572-eac-rolling-hvci-requirement.html): selective “HVCI required to play” on Fortnite / Apex / Rust, mostly Windows 11, called out as possibly tied to Insider builds. HVCI is off on this boot.
- FACEIT and Vanguard threads still treat TPM 2.0 and Secure Boot as launch requirements. Both are off here.
- A February 2026 25H2 thread says EAC’s kernel PFN / `EPROCESS` layout changed on 24H2 and later (reports from about October 2025). That is a Windows-branch note, not a motherboard one, and not tested against 26H2 `26340` on that forum.
