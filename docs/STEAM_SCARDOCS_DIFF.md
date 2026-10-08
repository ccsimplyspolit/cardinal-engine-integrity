# Steam scardocs vs repo audit

Steam path: `C:\Program Files (x86)\Steam\steamapps\common\Age of Empires IV\scardocs`

## Counts

| Source | Functions |
|--------|----------:|
| `html/function_list.htm` + `.api` | 2819 |
| catalog (functions.json + scardoc extras) | 4423 |
| `SIM_BLOCK` wrap | 1341 |

In Steam, missing from catalog: **0**
Wrap-class names not assigned in local_rules: **0**

## Steam class breakdown

- `safe_read`: 1001
- `safe_ui`: 575
- `sim_write`: 490
- `ai`: 408
- `campaign`: 121
- `sim_command`: 111
- `wrap_eventrule`: 30
- `wrap_fow_sim`: 26
- `wrap_timerule`: 26
- `network`: 8
- `runtime`: 7
- `wrap_proximity`: 7
- `overlay`: 5
- `safe_fow_ui`: 4
