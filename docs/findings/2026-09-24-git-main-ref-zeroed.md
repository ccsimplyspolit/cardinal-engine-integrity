# 2026-09-24 — AOE4HOOK git: refs/heads/main zeroed

Симптом: `fatal: your current branch appears to be broken`. Auth SourceLink: «Недопустимая ссылка» (нули).

## Что сломано

| Ref | Содержимое | mtime |
|---|---|---|
| `.git/refs/heads/main` | 41 байт `00` | 23:13:27 |
| `.git/refs/remotes/origin/main` | 41 байт `00` | 23:13:31 |
| `.git/refs/remotes/origin/HEAD` | 30 байт `00` | 23:13 |

`git fsck`: `badRefContent` / `invalid sha1 pointer 0000…0000` на этих трёх. Остальные heads (`stable`, `НУЖЕН-ГИПЕРВИЗОР`) OK. `aoe4-hv` OK (`amd` → `07e9cac`). У `hh\` корня `.git` нет (два отдельных репо).

## Что цело

- Objects: tip из reflog `b2bd7cc604` («anal 2», 23:13:27) читается.
- `ORIG_HEAD` = `8742a761fb` (старше).
- Remote жив: `git ls-remote origin refs/heads/main` → `7b82789110` («24.09 evening match…»).
- `b2bd7cc` — предок remote tip (`merge-base --is-ancestor` local→remote = 0). Локальный tip отстаёт от origin.

Индекс раздулся (~57 MB) и `git status` показывает всё как `A` — следствие битого HEAD, не отдельной катастрофы дерева.

## Починено (23:36)

1. Удалены битые loose-ref файлы (нули); `update-ref` отказывался на broken ref.
2. Записан `refs/heads/main` → `b2bd7cc604` (reflog tip «anal 2»).
3. `origin/HEAD` → `ref: refs/remotes/origin/main`.
4. `git fetch` (forced update packed `85df17e3` → `7b82789110`).
5. `git merge --ff-only origin/main` → HEAD `7b82789110`.
6. Удалён stale `REBASE_HEAD` (13.09).

`main` синхронен с `origin/main`. Локальные незакоммиченные правки docs/SCAR/titlehide остались.
