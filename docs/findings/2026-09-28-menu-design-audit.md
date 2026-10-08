# 2026-09-28 — design audit of the menu and the HUD against mockup v3

Request: "check the whole AOE4HOOK design and fix the problems". The yardstick is
[MENU_REDESIGN.md](../design/MENU_REDESIGN.md) (mockup v3 and its one-style rules table).

## Method

- The real pages were rendered offscreen (`tests\ui_preview\build_ui_pages.cmd`, a `/DUI_PREVIEW_HOST`
  DLL) in four variants: RU 1000 px, EN 1000 px, RU 760 px (rail) and RU 1400 px (wide). That makes 21 pages
  plus the HUD gallery, cut into native-resolution tiles.
- 15 reviewers covered page groups, the shell and widgets, the HUD, two language passes, the responsive pass
  and a code-rule sweep. Every finding was then re-checked by an independent verifier against the pixels and
  the code. Result: **229 findings, 226 confirmed** (177 in full, 49 partly), 20 of them high severity.
- The fixes went in shared layer → pages (one agent per set of files) → HUD → translations. Then a build,
  renders of all variants, `build_ui_preview.cmd` (22 checks) and `run_host.ps1`.

## Main causes (shared layer)

| Problem | Cause | Now |
| --- | --- | --- |
| Russian labels cut off («Добавить ИИ» → «Добавить», «Выключит») | button widths sized for the English words | `UiButton` / `UiPrimaryButton` widen a fixed width to fit the translation when the row has room |
| Long hints vanished (the desync warning on AI BOT, Macro's reasons, the Offline intro) | `UiHint` over 72 characters became the tooltip of the previous item: the zero-width spacer after a card title, or someone else's control | one line with an ellipsis, the full text on hover; never hooked onto the previous item |
| RU and EN showed different sets of hints | the 72-character limit counted the translation | the line is always there, only its length differs |
| Disabled primary button unreadable (1.4:1) | dark AccentInk on a faded accent | drawn as a secondary button when disabled |
| A toggle sat 3–5 px above the buttons in its row | the row was 22 px (track) against 28 px frames | centred on the height of its line |
| Card frame cut through the text line above it | card top = cursor − 10 px | the card starts below the previous line |
| No two columns on a wide window; on Offline a table broke the cards and the label-left rows | automatic cards were one flow only | card flow: the split is measured per page from the previous frame and allowed only where the ImGui stacks match the first section; `UiCardColumnBreak()` sets the split by hand |
| Controls in a card start at different x, rows 40/44 px | combo `clamp(avail*0.5)`, slider 168 + chip | one control column, 36 px rows, chip ≥ 58 px, stable while dragging |
| Statuses as grey pills or checkbox squares, colour literals | UiBadge / UiOkMark with IM_COL32 | tokens, tone 5 (warn), text baseline; a check mark instead of a box |
| A dark swatch looked like an empty checkbox | 16×16 ColorButton | a colour well with an inner ring |
| Subtitle cut with nothing to read it whole | TextFit up to the status block | runs up to the III button, full text on hover |
| The selected nav row was out of view | NavList did not scroll | a new selection opens its group and scrolls into view |

New API: `UiSectionLabelToggle` (the card's main switch in its title), `UiDependentBegin/End` (dependent rows),
`UiCardColumnBreak`, `UiDisabledReason` (lock + reason), `UiTooltipWrapped`, `UiBadge` tone 5. Rules table
updated in MENU_REDESIGN.md.

## Pages, HUD, translations

- Pages: 163 findings fixed in full, 44 in part, 34 needed no change, 8 skipped with a reason (detailed per id
  in the pass report). Examples:
  - Memory: label-left rows.
  - Send to SCAR: master switch in the card title, dimmed body.
  - ESP / Radar: Enable in the card title, dependent rows.
  - Macro: reasons next to the controls.
  - Offline: cards in two columns, no table.
  - Patch Game / Network: statuses as stripes, empty table state.
  - Settings: colour rows.
  - Log: the live log no longer shrinks to one line.
- HUD: default positions no longer overlap. `HudStackY` / `HudAlertSlot` stack the alerts under the map tracker.
  One plate `HudPanelStylePush/Pop` and one shadow `HudShadowText`. One title pattern
  `HudAlertTitle(key, count)`. Panel titles and alerts are translated. The macro HUD sits on the common plate.
  World labels no longer draw over the menu.
- Translations: about 900 new pairs and about 220 edited ones. Rules for them:
  - address the user formally («вы»);
  - ratusha / krestyanin throughout;
  - SCAR in upper case;
  - units с / мс / px;
  - slider value formats are translated too.

## Left for later (needs other files or a decision)

- A level parameter for `DrawSubTabRow`: on Macro the two tab rows look the same.
- A shared `UiInputInt` and `UiTableHeadersRow` for labelled number fields and table headers.
- The footer's "Save" does not save `hotkeys.ini`, and the "saved" status ignores keybindings; a hotkeys dirty
  flag is needed.
- The Files loader force-grows the window to 1320×900; it needs a clamp to the screen.
- The lobby players table on Memory (another session owns it): the empty state and its horizontal scroll, row
  colour as status, the untranslated `snapshot.status`.
- Russian-only strings in `ai_enemy_intel.cpp` (`hudRu`) and `ai_planner.cpp` (eco reasons) show untranslated
  in the EN HUD.
- About 72 statuses in `g_statusText` are put together with `sprintf` and are not translated.
- The spearman and horseman icons need cleaning (background tile and stray pixels).
- A toggle as "label left, switch right" like the mockup: it goes against the approved rules table and was not
  changed.
