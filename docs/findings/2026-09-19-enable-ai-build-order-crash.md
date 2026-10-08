# Enable AI: build-order store write fault

The 20:59:30 crash happens during `AiBuildOrderStoreReset`, before index or
document JSON is read. The build-order store had been re-enabled in the working
tree. In the shipped Release image its mutable aggregate `g_doc` was placed in
`.rdata`.

Evidence from the matching 20:52:44 DLL and linker map:

- Overlay base: `0x7FFF44330000`.
- Faulting instruction: RVA `0x27186B`, `memcpy_repmovs+0xB`.
- Write target: `0x7FFF445BA170`, RVA `0x28A170`, exactly `g_doc` in `.rdata`.
- The Present exception handler catches the access violation outside the store.
  The raw SRW exclusive lock remains held. The following AI session reaches a
  store reader and blocks; the 20:59:35 watchdog reports `ui.scripts` stalled.
- A host executable compiling the actual store with `/O2 /GL /MT /LTCG`
  reproduces exit code `0xC0000005` at its initial reset, without a game process.

The fix stores the document in a `unique_ptr`, parses directly into heap storage,
and resets ownership instead of copying a large empty aggregate into image data.
Scoped read/write locks also release on C++ exceptions during string copies.
They do not claim to recover arbitrary SEH faults. Explicit reset clears both
retry timers so an immediate reload does not spend three seconds with no index.
The UTF-8 path conversion reserves space for its terminating null explicitly.

Validation:

- `test_ai_build_order_store.cpp`, using Release whole-program optimization:
  initial reset, real JSON bind/copy, live targets, 30 reset/reload cycles with a
  concurrent reader, final reset, missing civilization, and malformed document.
  All pass. The test is included in `tests/adversarial/run_host.ps1` with `-Ltcg`.
- Existing `test_ai_build_order.cpp` parser/resolver tests pass.
- `python tests/adversarial/test_ai_build_order_store_image.py internal/x64/Release/InternalInjector.dll`
  fails on the original DLL and passes on the rebuilt DLL: document ownership,
  live targets and mutex are now in writable `.data`.
- Full Release DLL rebuild and Standalone packaging pass. The executable's
  embedded payload was compared against the rebuilt DLL and its hash validated.

Original DLL/map/log and build logs are preserved in
`K:\aoe4_dlc\hh\dumps\enable_ai_20260919`. Live match verification remains pending;
no game process was running during validation.
