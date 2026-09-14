# Debian 13 Chart-Aware Preview — 14 September 2026

Refreshed **Debian 13 amd64 testing installer**, based on upstream OpenCPN 5.14.0. This is a focused distribution, not the broader Core-Hardening developer bundle. It is a prerelease for desktop testing and is not certified for navigational safety.

Weather Routing **1.17.7.0** includes two selectable native C++ engines. **Main remains the default**, and upgrading preserves existing route and last-used settings. **Quick** is a separate bounded beam-search engine with independent tuning and a configurable 256 MiB default per-route search-storage ceiling. It shares Main's physical propagation and independent final validation, but its more aggressive pruning can miss a feasible or faster route that Main finds.

Advanced now offers all five GSHHG 2.3.7 shoreline levels from 0 — Crude through 4 — Full, bundled for offline use. Main starts at Full on a fresh install; Quick starts at Crude and each remembers its choice. With chart safety enabled and enforced in this preview, chart/depth evidence remains authoritative and the control becomes a separately saved, editable Scout shoreline resolution, initially Crude. Main also gains a bounded final-arrival allowance for routes that exhaust normal work close to the destination. The Advanced page has balanced columns and a separate Cyclone avoidance group while preserving all existing controls and values.

xGRIB **0.2.5.2**, Environmental GRIB Generator **0.1.8** and all other component pins are retained. The existing release URL is retained. Installing the newer package with APT upgrades the preview without removing its separate profile.

## Install

Download the `.deb` and matching `.sha256` release assets into one directory:

```sh
sha256sum --check opencpn-chart-aware-preview_5.14.0+chartaware.20260914.1_amd64.deb.sha256
sudo apt install ./opencpn-chart-aware-preview_5.14.0+chartaware.20260914.1_amd64.deb
```

Close existing OpenCPN instances, then open **OpenCPN Chart-Aware Preview** from the application menu. Use your ordinary desktop account, not sudo. The download is approximately 274 MiB. The application payload is approximately 624 MiB, plus any Debian dependencies APT needs to install.

The first-run assistant offers fresh settings or a verified backup and independent copy of an existing profile. **Isolated mode is recommended.** Optional replacement supports Debian/APT installations, requires separate confirmation, and first saves the exact original packages for rollback. Original settings are not removed or shared. Imported connections are disabled until reviewed. Plugin binaries and rebuildable caches are not imported. Purchased charts are not backed up by this assistant. See [the installation and recovery guide](https://github.com/pob220/OpenCPN-Chart-Aware/blob/f9ed43e1b3bede8050388523ef9cc762f2cf099c/distribution/INSTALL.md).

## Included

- OpenCPN 5.14.0 with chart/depth safety services, semantic-provider support and focused installation/profile-isolation changes
- Weather Routing **1.17.7.0**, including Main and Quick engines, selectable shoreline detail, preserved configuration, chart-aware scouting and improved Main final-arrival handling
- xGRIB **0.2.5.2**, Environmental GRIB Generator **0.1.8** and its runtime
- Updated Climatology with dataset **ocpn-climatology-2026.2**
- Polar **1.2.38.0**
- Modified o-charts semantic provider with the pinned official **2.2.1** helper

The five supplied plugins are enabled; native GRIB is disabled initially. Additional compatible plugins use OpenCPN's normal plugin manager and separate installation folders. Software rendering is the default. OpenGL can be selected explicitly. `opencpn-chart-aware --software` provides a recovery launch. No Vulkan experiment or added external-control service is included.

## Verification performed

The uploaded binary passed [GitHub Actions run 34828693694](https://github.com/pob220/OpenCPN-Chart-Aware/actions/runs/34828693694), building in Debian 13 and testing outside the compiler image:

- Core chart/depth tests: **14 passed**
- Weather Routing tests: **287 passed**
- xGRIB/generator tests: **27 passed**, plus functional merge/reader checks
- Climatology tests: **3 passed**; packaged dataset manifest hashes verified
- Profile setup tests: **8 passed**
- Dependency-only Debian 13 APT installation and real GUI startup/clean shutdown
- All five plugins loaded and deinitialized; Weather Routing initialised its chart-safety host and native GRIB remained disabled
- Software default, explicit OpenGL under Mesa/Xvfb, and software recovery checked
- Ordinary `~/.opencpn` remained absent during isolated GUI tests
- Installed xGRIB helper merged synthetic weather/current GRIBs successfully
- Coexistence with Debian OpenCPN, profile import, confirmed APT replacement, checksum-verified recovery, exact original package restoration and reinstall preserved both profiles

Component pins and vendor SHA-256 hashes are in the attached `components.json` and [source manifest](https://github.com/pob220/OpenCPN-Chart-Aware/blob/f9ed43e1b3bede8050388523ef9cc762f2cf099c/distribution/components.json). The binary core and package assembly revision is `f9ed43e1b3bede8050388523ef9cc762f2cf099c`. Weather Routing is pinned to `15c1369b6fbd71715dac598688c1b733a6e4fe7b`; xGRIB to `f5e1ea1019f37af4d8d8e951f43213e8d122f96d`, and its generator to `bf650d8960423461f607f9d96edb257e1092a7b9`.

The downloaded installer was independently checked against its checksum and embedded version/source manifest. All five GSHHG archives were decompressed and checked against the compressed and uncompressed hashes in their embedded manifest. Test reports accompany the release. The original preview tag is retained for a stable download link.

Installer SHA-256: `db417789c152924b521209422460f9e0aab694452d17270818034a76da6dbfb4`.

## Routing evidence and limits

In controlled development runs of the same Quick policy, a completed Provincetown–Lizard case using Main at 6h/20° took 324.780 seconds and peaked at 1,594.4 MiB process RSS; Quick completed in 69.476–77.886 seconds and peaked at 557.7–557.8 MiB. The 96 MiB and 256 MiB Quick settings produced the same independently validated route and used 0.368 MiB of tracked search storage. These are observations on one Linux machine under controlled inputs, not guaranteed speed or memory figures. Quick's budget applies only to tracked search storage and is not a cap on total OpenCPN memory.

Main remains the broader solver. Quick can miss a feasible passage, useful departure window or faster route because it does not run Main's full recovery search. The 1.17.7 regression set covers configuration migration, independent engine settings, bounded memory/work exhaustion, authoritative chart rejection, coastal egress, cancellation, all five offline shoreline levels and preservation of the earlier Atlantic controls. These Linux results do not establish Windows 32-bit runtime compatibility.

## Still requires real desktop testing

No licensed charts, entitlements, credentials or semantic atlas are distributed. The o-charts provider exports and helper startup were checked, but licensed chart display, semantic access and atlas construction on a real authorized Debian 13 machine have not yet been validated with this installer. Real GPU drivers, TPM/dongles and navigation hardware also require testing. Mesa/Xvfb is not proof that a particular physical GPU works.

Use your own legitimately licensed charts. Confirm chart display and depth-aware route rejection on a small known area before broader testing. Chart-safety service availability alone does not prove chart coverage or that a route is safe. Weather/current downloads require network access and any provider-specific setup. Do not replace the modified o-charts provider with an ordinary catalogue build while testing semantic routing.
