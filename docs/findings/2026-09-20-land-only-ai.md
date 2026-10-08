# Unconditional land-only AI

The previous water gate required both water-lane and island probes to succeed,
and deliberately allowed island naval production. The user's current policy is
to prohibit all AI water production on every map, including islands.

The shared `ai_land_only.h` script replaces 13 naval scoring hooks with a zero
list before executing their original placement/production factories. It covers
docks, fishing/trade/transport boats, combat ships and naval research. If the
Lua scorer factory is absent, an empty Relic MultiplyList scores zero. The
policy does not probe map type and cannot fail open due to a missing island API.

Both initial session scoring and runtime installer version 59 install this
same script last. Every AI mode installs scoring before enabling Relic think.
Apply and personality/difficulty invalidation reassert the policy, including
the same-generation Apply path. The naval strategic intention and emitted dock
desire are zero. Water items are filtered from build-order target lists and AI
builder queue serialization; saved user profiles are not rewritten.

This changes AI decisions through the existing SCAR flow. It does not patch
Relic code, alter executable page protections, or introduce native availability
calls. Existing ships, completed docks and previously accepted construction or
production commands are not destroyed or cancelled by this change. The source
change does not replace a DLL already loaded into a running match.

Validation:

- Six Lua execution tests, including the actual extracted Relic scoring file,
  missing factories, invalid/missing map answers, reinstall and land-hook
  preservation: pass.
- Build-order C++ tests, including exclusion of docks/boats/naval research and
  preservation of land targets: pass.
- AI handover 133 tests, ElGate six tests and scoring inventory seven tests:
  pass.
- Release x64 InternalInjector build: pass.
- Broader C++ AI math suite: the pre-existing `fast_age keeps food exactly twice
  gold despite stock relief` failure remains. All changed naval expectations
  pass. No live match behavior is claimed as tested.
