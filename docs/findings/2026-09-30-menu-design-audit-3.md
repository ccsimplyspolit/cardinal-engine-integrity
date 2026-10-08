# 2026-09-30 — design audit 3: the panes the renders never showed

Request: "полностью проверь дизайн aoe4hook и исправь проблемы" — the third full pass, after
[the first audit](2026-09-28-menu-design-audit.md) (fdec50143f) and its second pass (42785a7a1e). The yardstick
is still [MENU_REDESIGN.md](../design/MENU_REDESIGN.md) and its one-style rules table.

## Method

- **Preview coverage.** The page renders drew only the first sub-tab of every page, so 21 panes had never been
  rendered by any audit: Radar (Observer, Map, Colors), ESP (Labels, Highlights, Colors), Macro (Units, Timing,
  Live in both lanes), AI BOT with the AI on (Session, Fine tuning, Build order), Offline (Combat, World,
  Crucible) and Network (Spoof, Deny, Allow rules). `ui_preview_host.cpp` now opens a pane by its English label
  (`PreviewPage::subTab`, read by `DrawSubTabRow`) and draws AI BOT as if the AI were on (`g_previewAiOn`), and
  `UI_PREVIEW_EXPAND=1` draws every accordion and `UiDetails` line open. 47 pages in six variants: RU / EN
  1000 px, RU 760 px, RU 1400 px, RU / EN 1000 px with everything open.
- **Two automatic checks** in the preview build, written next to the PNGs:
  - `i18n_miss.txt`: every Russian lookup that found no translation, per page (`UiPreviewNoteMiss`, called by
    `UiTr` / `UiTrVisible` / `UiTrCombo` in the preview build only).
  - `pages.log`, `layout in <page>` lines: the horizontal overflow ImGui itself measured — a window whose content
    is wider than the window (`overflow-x`, a row running past the card) and a table cell or header wider than
    its column (`column-clip`). Informational, not failures.
- A visual pass over every tile, fixes by file, then a re-render until both checks were clean apart from the
  items under "Left for later".

## Found and fixed

| Where | Problem | Now |
| --- | --- | --- |
| AI BOT › Fine tuning | The whole pane was still the pre-redesign stack of bordered boxes: its own label column (556 px against 670), the switches as box titles, 22 px buttons, "Save as" 119 px past the card, 18 commands under no card | Cards: Personality and economy, Templates, four cards whose switch is the card's main switch with the sliders dimmed, Age and population caps, Send to the AI (commands two to a row under one lock reason) |
| Network › Spoof / Deny / Allow rules | Host \| Path and Body \| Also require shared a row, so Path and Also require sat 342 px past the card: invisible and not editable | One field per labelled row; the id with a hint in the head row, Remove at the right; the caption that repeated the rewrite mode removed |
| Every two-column page (≥ 1060 px) | 12 px wider than the window: the column child reaches past the body so card frames are not clipped, and that edge counted as content (Shift+wheel slid the page) | `FlowCloseColumn` clamps the body's content width to the flow |
| Radar › Observer | The pane was hidden while the HUD was off, and the card title and the switch said the same words | The switch is the card's main switch; the pane shows dimmed |
| Radar › Display, Map | Outline, Opacity, Dots, Dot size, Player ESP size, Thickness and every Map-pane placement control changed settings without `ConfigMarkDirty` (the footer said Saved, nothing autosaved); the rows auto-place disables gave no reason | Marked dirty; a reason line where auto-place owns the row |
| ESP › Labels, Highlights, Colors | Nothing said ESP was off, the switches looked live | A lock line naming the Basic tab and the cards dimmed; the TC-zone card stays live (it draws without ESP) |
| ESP › TC zones | A full-width combo reading only "Overlay"; ring sliders did not mark dirty | A labelled "Rings" row; sliders mark dirty |
| AI BOT › Session | "Unit control" was a drawer bar between the tab row and the first card, outside every card | A card, open like Presets |
| AI BOT › Build order | No card, two primary full-width buttons, an English empty state | Two cards, plain buttons, the civ list with flags and names in the menu language |
| AI BOT, every pane | A Save button and an "Unsaved changes" line of its own (01.09, before the footer had Save) | Removed; the footer covers it |
| Macro › Live | The status lines ran 70 px past the card at 760 px; the why-line and the last action were English | Wrapped; the why-line is a status stripe (amber while blocked) in the menu language |
| Macro › HUD colours | Swatches right after their word, unlike every other colour row | `UiColorRow` (Settings' row, now shared; the night tint uses it too) |
| Memory › Lobby roster | Names and civs cut mid-glyph ("Zhu Xi's Leg", "Abbasid Dyr", "Открытый сл") | Cut on a whole glyph with an ellipsis, whole on hover (`UiTextEllipsis`, fitted captions) |
| Memory, AI BOT › Build order | Civ and rank names in English on a Russian page | `UiCivDisplayName` (the short names the ESP cards use), Russian rank names |
| Memory › Lobby actions | The two skip-cooldown statuses printed the same words twice | One line when they agree |
| Memory › Advanced | "lobby: unresolved" in English, lower-case status lines, "Доп. PBG" / "Принуд. PBG" while the hint said "Force PBG" | Translated and capitalised; the rows and the hint use the same full names |
| Memory › worst civ | The tooltips named a "Worst WR" column and a "Scan" button that no longer exist | "Weakest civ" and "Read lobby now" |
| Memory › Profile | The SteamID cut mid-digit in the half-width card | Ellipsis |
| Files | At 760 px Unload was pushed 14 px past the column | Wraps under the other two when the words do not fit |
| Debug › Status | The FOWCTRL1 address line ran 370 px past the card | Wrapped |
| Translations | 57 new pairs, 7 edited: the MP Pause card, the header status tooltips, Live MCP states, the macro why-lines, Fine tuning card titles and more | `gen_ui_i18n.py` is still the source; it reproduces `ui_i18n.cpp` byte for byte |

New shared API: `UiTextEllipsis`, `UiColorRow`, `UiCivDisplayName`. The rules table in MENU_REDESIGN.md has
rows for them.

## Left for later (needs another file owner, a live check or a decision)

- In English mode the ESP world labels, the hover card and unit names are still Russian (`esp.cpp`,
  `unit_profile.cpp`), as are `ai_enemy_intel.cpp` `hudRu` and the `ai_planner.cpp` eco reasons.
- Send to SCAR: the "Scar feed: … Format: …" tooltips are English developer documentation.
- Macro: the bind table shows raw action ids (`train_villager`, `pick_next_barracks`, …).
- Memory: Dodge and Add a computer stay enabled out of a lobby. Gating them needs a live check of the snapshot
  flags — Dodge was verified live on 30.09 and a wrong flag would block it.
- Memory: the MP Pause HTTP tooltip and the Profile spoof cards are being rewritten in another session and
  were not touched (their XP boost status still reads "выкл").
- Camera: the night layer's settings are not saved to config at all; the Minimum and Maximum sliders have
  different ranges, so the Maximum thumb can sit left of the Minimum one.
- AI BOT: the "Unit scoring" drawer is raw developer telemetry.
- Memory: with the Change civ column shown, ImGui shortens the "Weakest civ" header with an ellipsis at 1000 px.
