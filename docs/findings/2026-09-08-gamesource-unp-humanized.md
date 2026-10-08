# 2026-09-08 — gamesource_unp_humanized

User: `unpacked_static` is not human-readable; make `gamesource_unp_humanized`.

## What shipped

Not a second 534k Hex-Rays. Classified overlay of unpack-disk:

| Path | Role |
|---|---|
| `AOE4HOOK/gamesource_unp_humanized/named/` | 66 files; Hex-Rays (or disasm) only if static == live 60644 unreloc |
| `…/LEFTOVER.md` | dest0 leftover map |
| `…/INDEX.md` `RECIPE.md` `LAYERS.md` | navigation |
| exporter | `gamesource/tools/Export-UnpHumanized.py` |
| CLI | `python -m unpacker humanize` / `Run-ExportUnpHumanized.ps1` |

Preferred ImageBase `0x140000000`. RVA only. ADR:
[ADR-005](../decisions/ADR-005-gamesource-unp-humanized.md).

## Numbers (this build)

unreloc compare of `.text` vs 60644 `memory.bin`:

- leftover **651 472 B** (RA band 604 159, outside 47 313)
- **2636** runs; first at `0x679533`
- named catalog overlap **0 B**
- **66 / 66** named RVAs `static_match` (incl. Watcher, 7AB0, Dispatcher, crypto)

So the named RA cluster is valid C for unpacked_static. Leftover is other dest0
spans, not “these functions still encrypted”.

## Do not

- Treat leftover as missing compact XOR
- Replace `gamesource/` runtime IDB with this tree
- Plant Watcher / 7AB0 / Enqueue because named C exists
