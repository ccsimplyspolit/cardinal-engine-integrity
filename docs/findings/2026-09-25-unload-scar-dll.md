# 2026-09-25 — UNLOAD и anti-tamper

Кнопка **UNLOAD** останавливает SCAR и снимает оверлей. Образ уходит через `NtUnmapViewOfSection` со страницы **вне** DLL.

Не делается, потому что это как раз то, что видит RA:

| Шаг | Почему нет |
|---|---|
| PEB relink + `FreeLibrary` / `LdrUnloadDll` | Модуль снова в InLoadOrder / Toolhelp. Integrity `0x56FD3C0` (`RA_Integrity_Dispatcher`) паковал лишний образ и чужой указатель. `LdrLockLoaderLock` на живом обходе списков — гонка. Имена после unlink стёрты: в списке была бы безымянная запись. |
| Запись Relic `.text` на выходе | Hasher `0x3E57050` читает байты до memcpy. `UnpatchLatch3` и `RestoreAllInlinePatches` (neutralize) — вторая запись. На UNLOAD они пропускаются. Выход процесса по-прежнему их восстанавливает. |

Снимается то, что иначе прыгнет в снятый образ, и это не байты Relic `.text`: vtable DXGI, WndProc, слот SimWorld::Tick, VEH, PAGE_GUARD наших страниц. KiUser в ntdll `.data` возвращается только если слот был наш (по умолчанию Relic держит его сам). user32 body восстанавливается только если Patch Game его ставил — jmp целится в stub этой DLL; дефолт `bodies=0`, записи нет.

PEB остаётся отлинкованным. AVL base-index ntdll не трогаем: смещение на 26H2 не зафиксировано, правка дерева загрузчика сама по себе tamper.
