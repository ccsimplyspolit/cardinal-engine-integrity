# 2026-09-12 WindowWatch: empty then slots=3, x64dbg at 23:54

Same boot 21:25:38. SVM still map **23:18** (user-DTB sys 23:51 not mapped).
WindowWatch RPM only. Do not reuse these VAs.

## Pattern

Every Relic this evening: empty `slots=0` for a few minutes, then
`slots=3 accum=600 flag=1`, then `RPM 299` and a new PID.

| PID | base | empty until | slots=3 | died |
|---|---|---|---|---|
| 30636 | `0x7FF6BC390000` | 23:19:58 | 23:25:14 (~5m) | 23:27:26 |
| 50796 | `0x7FF762390000` | 23:27:41 | 23:32:37 (~5m) | 23:33:17 |
| 1704 | `0x7FF762390000` | 23:33:35 | 23:39:56 (~6m) | 23:40:31 |
| 50152 | `0x7FF6A0A80000` | 23:45:18 | 23:47:06 (~2m) | 23:50:19 |
| 42396 | `0x7FF6F9A20000` | 23:51:09 | **23:54:05** | after 23:57 |
| 42408 | live ~23:57:51 | empty at first attach | — | — |

PID **42396** flipped the same second x64dbg opened (**23:54:03** process,
**23:54:05** WW). Visible `x64dbg.exe` (MCP host path) is DualFlag, not
File?Attach. Packed AT also fills ~5–6 min even without dbg.

User plan: game ? HV hold apply while empty ? **then** debugger ? then
Attach. Close visible x64dbg before apply. Do not Attach until apply=0.
