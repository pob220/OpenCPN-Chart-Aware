# Debian 13 Chart-Aware Preview — 12 September 2026

Refreshed **Debian 13 amd64 testing installer**, based on upstream OpenCPN 5.14.0.
This is a focused distribution, not the broader Core-Hardening developer bundle.
It is a prerelease for desktop testing - not certified for navigational safety.

This refresh updates Weather Routing to **1.17.3.0**, making chart-safety settings apply immediately, correcting mixed-longitude final checks, reporting missing GRIB endpoint coverage before search, and including preparation in single-route headless timeouts. The earlier Climatology, course-longitude and lifetime fixes are retained. Other bundled plugin and core-code pins are unchanged.
The existing release URL is retained. Installing the newer package with APT upgrades the preview without removing its separate profile.

## Install

Download the `.deb` and matching `.sha256` release assets into one directory:

```sh
sha256sum --check opencpn-chart-aware-preview_5.14.0+chartaware.20260912.1_amd64.deb.sha256
sudo apt install ./opencpn-chart-aware-preview_5.14.0+chartaware.20260912.1_amd64.deb
```

Close existing OpenCPN instances, then open **OpenCPN Chart-Aware Preview** from the application menu. Use your ordinary desktop account, not sudo. The download is approximately 202 MiB. The application payload is approximately 632 MiB, plus
any Debian dependencies APT needs to install.

The first-run assistant offers fresh settings or a verified backup and independent copy of an existing profile. **Isolated mode is recommended.** Optional replacement supports Debian/APT installations, requires separate confirmation, and first saves the exact original packages for rollback. Original settings are not removed or shared. Imported connections are disabled until reviewed. Plugin binaries and rebuildable caches are not imported. Purchased charts are not backed up by this assistant. See [the installation and recovery guide](https://github.com/pob220/OpenCPN-Chart-Aware/blob/50004562507d12deb5a2d9abee596cfade736f14/distribution/INSTALL.md).

## Included

- OpenCPN 5.14.0 with chart/depth safety services, semantic-provider support and focused installation/profile-isolation changes
- Weather Routing **1.17.3.0**, including the chart-policy, longitude-validation, weather-coverage and timeout fixes
- xGRIB **0.2.4.1**, Environmental GRIB Generator **0.1.7** and its runtime
- Updated Climatology with dataset **ocpn-climatology-2026.2**
- Polar **1.2.38.0**
- Modified o-charts semantic provider with the pinned official **2.2.1** helper

The five supplied plugins are enabled - native GRIB is disabled initially.
Additional compatible plugins use OpenCPN's normal plugin manager and separate installation folders. Software rendering is the default. OpenGL can be selected explicitly. `opencpn-chart-aware --software` provides a recovery launch.
**No Vulkan experiment or added external-control service is included.** 
(An optional enhanced graphics rendering variant remains separate follow-up work.)

## Verification performed

The uploaded binary passed [GitHub Actions run 34694130628](https://github.com/pob220/OpenCPN-Chart-Aware/actions/runs/34694130628), building in Debian 13 and testing outside the compiler image:

- Core chart/depth tests: **14 passed**
- Weather Routing tests: **230 passed**
- xGRIB/generator tests: **24 passed**, plus functional merge/reader checks
- Climatology tests: **3 passed**; packaged dataset manifest hashes verified
- Profile setup tests: **8 passed**
- Dependency-only Debian 13 APT installation and real GUI startup/clean shutdown
- All five plugins loaded and deinitialized. Weather Routing initialised its chart-safety host. Native GRIB remained disabled
- Software default, explicit OpenGL under Mesa/Xvfb, and software recovery checked
- Ordinary `~/.opencpn` remained absent during isolated GUI tests
- Installed xGRIB helper merged synthetic weather/current GRIBs successfully
- Coexistence with Debian OpenCPN, profile import, confirmed APT replacement, checksum-verified recovery, exact original package restoration and reinstall preserved both profiles.

Component pins and vendor SHA-256 hashes are in the `components.json` release asset and [source manifest](https://github.com/pob220/OpenCPN-Chart-Aware/blob/50004562507d12deb5a2d9abee596cfade736f14/distribution/components.json). The binary core revision is `50004562507d12deb5a2d9abee596cfade736f14`, also the package assembly revision.
Weather Routing is pinned to `c5801db79948435b5c2231b763c580cc1f5ddcf1`.
The downloaded installer was additionally checked against its checksum and its embedded version/source manifest; the attached `components.json` is that embedded manifest. Test reports accompany the release. The original preview tag name is retained for a stable download link. The revisions above identify the new binaries.

Installer SHA-256: `89f4abbf25d19966e7ce1343ea14717366425faa69baf9932f51b79bf74a0a0f`.

## Still requires real desktop testing

No licensed charts, entitlements, credentials or semantic atlas are distributed.
The o-charts provider exports and helper startup were checked, but **licensed chart display, semantic access and atlas construction on a real authorized Debian 13 machine have not yet been validated with this installer**. Real GPU drivers, TPM/dongles and navigation hardware also require testing. Mesa/Xvfb is not proof that a particular physical GPU works.

Use your own legitimately licensed charts. Confirm chart display and depth-aware route rejection on a small known area before broader testing. Chart-safety service availability alone does not prove chart coverage or that a route is safe.
Weather/current downloads require network access and any provider-specific setup.
Third-party Debian 13 plugin catalogue availability is outside this bundle's control. Do not replace the modified o-charts provider with an ordinary catalogue build while testing semantic routing.