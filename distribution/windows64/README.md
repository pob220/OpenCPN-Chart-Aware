# Windows x64 Preview build

Status: the complete native Windows x64 bundle passed its automated runtime
gate on 14 September 2026, at source revision
`17bbfab37a8c911400ec56295c9475b2c590a626`.
See [Windows qualification run 34800864270](https://github.com/pob220/OpenCPN-Chart-Aware/actions/runs/34800864270)
for the Preview ZIP and build evidence. CI artifacts are retained for 14 days.

Source branch: `preview/windows-x64`, based on the focused OpenCPN 5.14
chart-aware distribution at `e356754`. The ordinary working installation is not
used as a build or installation destination.

The build uses Visual Studio 2022 x64, wxWidgets 3.2.8 x64 (SHA-256-pinned
upstream SDK archives), and a pinned vcpkg source revision with a release-only
x64 triplet. No legacy x86 support bundle is used in the enabled core paths.
Legacy CrashRpt is disabled and the Preview notes disclose this. Pointer
truncation warnings are errors in the core and plugin builds. MSVC runtime
libraries are staged from the native compiler's redistributable directory.
curl uses its native Windows Schannel backend. The SDK and staged runtime
must each pass an HTTPS request with peer and hostname verification enabled;
the check removes any inherited TLS-backend override. OpenSSL remains a
separate dependency for the core components which use it directly.

Run on a native Windows builder with Python 3.12, Git, CMake, 7-Zip, GNU gettext
and the MSVC x64 tools environment:

```
python distribution/windows64/build.py dependencies
python distribution/windows64/build.py core
python distribution/windows64/fetch_plugins.py
python distribution/windows64/build_plugins.py
python distribution/windows64/stage_data.py
```

The workflow runs `smoke.ps1` on a disposable Windows runner, then `package.py`
to create an extract-and-run Preview ZIP. It does not publish a GitHub release
or upload plugins to a catalogue. The package gate requires all six plugins,
the x64 generator, verified datasets, the chart-safety core connection, and
unchanged ordinary-profile sentinel files. The smoke test checks actual loaded
modules with the development SDK removed from PATH and retains a screenshot.
It exercises software rendering; this does not qualify real graphics drivers,
navigation devices, or routing against real charts.

The Preview core uses `%LOCALAPPDATA%\OpenCPN-64bit-Preview\profile` through
Windows' known-folder API. Its wxStandardPaths user/config paths and managed
plugin location are redirected into that profile. Imported legacy plugin path
overrides are ignored. `--configdir` and portable mode are rejected by this
Preview build so ordinary OpenCPN state cannot be selected through those flags.
The title shows `64-bit Preview`. The automated runtime gate passed. Sentinel
checks cover the normal roaming, local, and shared OpenCPN profile folders;
broader filesystem write tracing and simultaneous real-installation testing
remain useful tester checks.

`components-candidate.json` pins the six plugin sources used in the tested bundle.
Polar 1.2.38.0 is explicitly confirmed by the user. OfflineTides uses
the later published alpha3 source, which already has Windows x86 build history.
The modified o-charts provider/runtime needs separate Windows x64 investigation
for licensed-chart support.

`build_plugins.py` makes disposable copies of the pinned inputs with their own
Git metadata. It replaces the selected API's legacy x86 import library with
the newly compiled x64 `opencpn.lib`, honors the Preview staging prefix, and
records the overlays. Celestial and OfflineTides use the bundled read-only data
when private data have not been selected. These overlays do not add a new tide
API or tide-adjusted under-keel-clearance policy.
The xWeatherRouting overlay selects the SDK's x64 zlib and matching test DLL.
Climatology's legacy `snprintf` compatibility macros are restricted to old MSVC.
Celestial tests reuse the core's native GoogleTest libraries and headers.

The ZIP includes the full-resolution GSHHG shoreline archive, all 52 Climatology
2026.2 dataset files, the authenticated OfflineTides global runtime package,
DE440s, lunar orientation and LOLA eclipse data. Source revisions, dataset
checksums and licences accompany the package. No ordinary profile is imported.
The six Preview plugins are enabled on a clean first run and retain the usual
enable/disable controls in Options. Bundled plugins remain listed after being
disabled even though they are not catalog installations.

Local checks completed on 13 September 2026: eight architecture-gate tests pass,
covering x86/ARM64 rejection, a nested wrong-architecture DLL, malformed images,
and a core missing large-address-awareness. All 16 DLLs extracted from the pinned
wxWidgets x64 runtime archive pass the PE32+/AMD64 checks. This is dependency
verification, not an OpenCPN build or GUI result. The 52 Climatology files and
full-resolution shoreline archive also pass their pinned checksum checks.
Windows CI has compiled and staged the native core and all six plugin DLLs.
All 85 registered core tests pass, including the chart-depth and chart-safety
service tests, together with the generator's 6 tests, xWeatherRouting's 258
tests, xGRIB's 19 tests and Climatology's 3 test groups. Celestial passes both
CTest groups; its main suite passes 177 tests and skips its three opt-in UI
tests. Polar 1.2.38.0 and OfflineTides compile and install.
All 140 staged native images pass the AMD64 gate, and all 58 operational dataset
files pass their checksum checks. Plugin source checkouts preserve repository
line endings so text datasets retain their published hashes.

The complete runtime test starts with no plugin enablement entries and confirms
all six bundled plugins are enabled by default. It also verifies xWeatherRouting
resolves its installed icon/data directory, the chart-aware core connection,
the authenticated OfflineTides dataset, native HTTPS verification,
the packaged xGRIB generator and console ABI, rejection of ordinary-profile
overrides, unchanged ordinary-profile sentinels, and clean GUI shutdown.
Only the six named Preview plugins are additionally allowed in the application
plugin folder; normal compatibility and enable/disable checks still apply.
The screenshot and runtime logs are retained in the CI build-evidence artifact.

Modern x64 Windows supplies up to 128 TB of user-mode virtual address space to a
large-address-aware x64 process. A 32-bit process has 2 GB by default or up to
4 GB on 64-bit Windows when large-address-aware. RAM and system commit remain
practical allocation constraints; 64-bit alone does not promise a speedup.
See https://learn.microsoft.com/en-us/windows/win32/memory/memory-limits-for-windows-releases.
