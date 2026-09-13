# Debian 13 Chart-Aware Preview — 13 September 2026

Refreshed **Debian 13 amd64 testing installer**, based on upstream OpenCPN 5.14.0.
This is a focused distribution, not the broader Core-Hardening developer bundle.
It is a prerelease for desktop testing - not certified for navigational safety.

Weather Routing **1.17.5.0** adds bounded recovery around continental obstructions, actionable land/depth prerequisite errors, and visible progress for ordinary computations. The progress window identifies each route and its current search stage, counters and worker-update age; Hide keeps work running, and Stop explicitly cancels it. Failed headless runs no longer present provisional geometry or arrival times as completed results. GPX exports handle names containing slashes. Existing safety enforcement, weather fallback, resource ceilings and earlier fixes are retained. xGRIB **0.2.5.2**, Environmental GRIB Generator **0.1.8** and all other component pins are retained.
The existing release URL is retained. Installing the newer package with APT upgrades the preview without removing its separate profile.

## Install

Download the `.deb` and matching `.sha256` release assets into one directory:

```sh
sha256sum --check opencpn-chart-aware-preview_5.14.0+chartaware.20260913.1_amd64.deb.sha256
sudo apt install ./opencpn-chart-aware-preview_5.14.0+chartaware.20260913.1_amd64.deb
```

Close existing OpenCPN instances, then open **OpenCPN Chart-Aware Preview** from the application menu. Use your ordinary desktop account, not sudo. The download is approximately 202 MiB. The application payload is approximately 551 MiB, plus
any Debian dependencies APT needs to install.

The first-run assistant offers fresh settings or a verified backup and independent copy of an existing profile. **Isolated mode is recommended.** Optional replacement supports Debian/APT installations, requires separate confirmation, and first saves the exact original packages for rollback. Original settings are not removed or shared. Imported connections are disabled until reviewed. Plugin binaries and rebuildable caches are not imported. Purchased charts are not backed up by this assistant. See [the installation and recovery guide](https://github.com/pob220/OpenCPN-Chart-Aware/blob/1998158f52b76a0575522428e3759a36db74b5dd/distribution/INSTALL.md).

## Included

- OpenCPN 5.14.0 with chart/depth safety services, semantic-provider support and focused installation/profile-isolation changes
- Weather Routing **1.17.5.0**, including the destination-completion fix and clearer diagnostics, alongside the earlier chart-policy, longitude-validation, weather-coverage and timeout fixes
- xGRIB **0.2.5.2**, Environmental GRIB Generator **0.1.8** and its runtime
- Updated Climatology with dataset **ocpn-climatology-2026.2**
- Polar **1.2.38.0**
- Modified o-charts semantic provider with the pinned official **2.2.1** helper

The five supplied plugins are enabled - native GRIB is disabled initially.
Additional compatible plugins use OpenCPN's normal plugin manager and separate installation folders. Software rendering is the default. OpenGL can be selected explicitly. `opencpn-chart-aware --software` provides a recovery launch.
**No Vulkan experiment or added external-control service is included.** 
(An optional enhanced graphics rendering variant remains separate follow-up work.)

## Verification performed

The uploaded binary passed [GitHub Actions run 34752762849](https://github.com/pob220/OpenCPN-Chart-Aware/actions/runs/34752762849), building in Debian 13 and testing outside the compiler image:

- Core chart/depth tests: **14 passed**
- Weather Routing tests: **238 passed**
- xGRIB/generator tests: **27 passed**, plus functional merge/reader checks
- Climatology tests: **3 passed**; packaged dataset manifest hashes verified
- Profile setup tests: **8 passed**
- Dependency-only Debian 13 APT installation and real GUI startup/clean shutdown
- All five plugins loaded and deinitialized. Weather Routing initialised its chart-safety host. Native GRIB remained disabled
- Software default, explicit OpenGL under Mesa/Xvfb, and software recovery checked
- Ordinary `~/.opencpn` remained absent during isolated GUI tests
- Installed xGRIB helper merged synthetic weather/current GRIBs successfully
- Coexistence with Debian OpenCPN, profile import, confirmed APT replacement, checksum-verified recovery, exact original package restoration and reinstall preserved both profiles.

Component pins and vendor SHA-256 hashes are in the `components.json` release asset and [source manifest](https://github.com/pob220/OpenCPN-Chart-Aware/blob/1998158f52b76a0575522428e3759a36db74b5dd/distribution/components.json). The binary core revision is `1998158f52b76a0575522428e3759a36db74b5dd`, also the package assembly revision.
Weather Routing is pinned to `39a8f88e2fa2528f603b113443e446b22ba7e481`; xGRIB to `f5e1ea1019f37af4d8d8e951f43213e8d122f96d`, and its generator to `bf650d8960423461f607f9d96edb257e1092a7b9`.
The downloaded installer was additionally checked against its checksum and its embedded version/source manifest; the attached `components.json` is that embedded manifest. Test reports accompany the release. The original preview tag name is retained for a stable download link. The revisions above identify the new binaries.

Installer SHA-256: `73d5d726b9b5a72aabe86c258d089e09fa7970340729cb0b12544aa039fff2e8`.

## Still requires real desktop testing

No licensed charts, entitlements, credentials or semantic atlas are distributed.
The o-charts provider exports and helper startup were checked, but **licensed chart display, semantic access and atlas construction on a real authorized Debian 13 machine have not yet been validated with this installer**. Real GPU drivers, TPM/dongles and navigation hardware also require testing. Mesa/Xvfb is not proof that a particular physical GPU works.

Use your own legitimately licensed charts. Confirm chart display and depth-aware route rejection on a small known area before broader testing. Chart-safety service availability alone does not prove chart coverage or that a route is safe.
Weather/current downloads require network access and any provider-specific setup.
Third-party Debian 13 plugin catalogue availability is outside this bundle's control. Do not replace the modified o-charts provider with an ordinary catalogue build while testing semantic routing.

## Routing validation and remaining limits

Native Linux and Debian 12 testing passed all **238 tests**. Controlled Provincetown–Lizard routes with land detection, the Nicholson 35 polar, a 15-day ECMWF forecast, offline tidal/seasonal currents and Climatology wind fallback completed at 100% effort with 3-hour/10-degree and 6-hour/20-degree settings. The 0.5-degree forecast with 3-hour/10-degree settings exhausted 100%, then completed at the 150% tier when allowed 200%. More effort can help; it does not guarantee completion. These concurrent measurements are functional tests, not controlled speed benchmarks or navigation recommendations.

Five existing no-land Atlantic routings and the forecast/Climatology handoff control preserved their geometry exactly. The CM93 Vava’u control also matched 1.17.4; depth, missing-coverage, unsupported-host and land-endpoint controls behaved as expected. Quinton’s exact saved island case remains unavailable, so these controls do not establish the cause of his earlier reported land crossing. Physical graphics drivers, all chart providers and every reported routing case have not been qualified.
