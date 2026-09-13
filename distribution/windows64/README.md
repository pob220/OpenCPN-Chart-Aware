# Windows x64 Preview build

Status: initial source implementation, awaiting a native Windows compiler run.
This directory does not yet produce the complete tester installer.

Source branch: `preview/windows-x64`, based on the focused OpenCPN 5.14
chart-aware distribution at `e356754`. The ordinary working installation is not
used as a build or installation destination.

The first build uses Visual Studio 2022 x64, wxWidgets 3.2.8 x64 (SHA-256-pinned
upstream SDK archives), and a pinned vcpkg source revision with a release-only
x64 triplet. No legacy x86 support bundle is used in the enabled core paths.
Optional legacy CrashRpt is disabled for this initial compiler milestone; this
must be listed in Preview release notes if retained.

Run on a native Windows builder with Python 3.12, Git, CMake, 7-Zip and the
MSVC x64 tools environment:

```
python distribution/windows64/build.py dependencies
python distribution/windows64/build.py core
```

The workflow only creates internal build artifacts. It does not publish a
release or upload plugins to a catalogue. A complete six-plugin bundle and
installer remain required before a tester release.

The Preview core uses `%LOCALAPPDATA%\OpenCPN-64bit-Preview\profile` through
Windows' known-folder API. Its wxStandardPaths user/config paths and managed
plugin location are redirected into that profile. Imported legacy plugin path
overrides are ignored. `--configdir` and portable mode are rejected by this
Preview build so ordinary OpenCPN state cannot be selected through those flags.
The title shows `64-bit Preview`. These source changes still need Windows
runtime qualification, including write tracing and coexistence checks.

`components-candidate.json` pins six source candidates, not qualified binaries.
Polar's candidate is the existing 1.2.38.0 distribution source; establish the
intended updated Polars source before freezing the release. OfflineTides uses
the later published alpha3 source, which already has Windows x86 build history.
The modified o-charts provider/runtime needs separate Windows x64 investigation
for licensed-chart support.

Next required work after the first compiler run:

1. Resolve compiler/linker findings and inspect actual core exports and imports.
2. Build all six plugins against the same x64 core import library and wxWidgets
   SDK; replace bundled x86 API import libraries in their isolated build sources.
3. Stage xGRIB's generator and dependencies, all required datasets and licences,
   and verify each loaded/shipped native runtime image as AMD64.
4. Add the isolated per-user Preview installer, clean-machine dependency and
   plugin initialization tests, complete-stack chart-routing tests, and upgrade/
   uninstall/coexistence qualification. Keep normal OpenCPN state untouched.
5. Publish a tester candidate only after the complete bundle passes its gates.

Local checks completed on 13 September 2026: eight architecture-gate tests pass,
covering x86/ARM64 rejection, a nested wrong-architecture DLL, malformed images,
and a core missing large-address-awareness. All 16 DLLs extracted from the pinned
wxWidgets x64 runtime archive pass the PE32+/AMD64 checks. This is dependency
verification, not an OpenCPN build or GUI result.

Modern x64 Windows supplies up to 128 TB of user-mode virtual address space to a
large-address-aware x64 process. A 32-bit process has 2 GB by default or up to
4 GB on 64-bit Windows when large-address-aware. RAM and system commit remain
practical allocation constraints; 64-bit alone does not promise a speedup.
See https://learn.microsoft.com/en-us/windows/win32/memory/memory-limits-for-windows-releases.
