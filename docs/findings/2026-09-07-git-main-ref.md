# 2026-09-07 22:08 — broken `refs/heads/main`

Git Desktop: `cannot lock ref 'refs/heads/main': reference broken`. Same NUL-ref as Aoe4Auth `Microsoft.Build.Tasks.Git`.

`.git/HEAD` was fine (`ref: refs/heads/main`). `.git/refs/heads/main` was **41 zero bytes**. Only broken loose ref. `origin/main` + reflog tip = `384cdc1cda781f8da1d1297e836071551dffcb12`.

Fix: deleted the NUL file, `git update-ref refs/heads/main 384cdc1c…`. `HEAD` / `main` / `origin/main` match. No reset, no push, no commit.