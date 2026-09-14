# Debian 13 Chart-Aware Preview — 15 September 2026

Refreshed **Debian 13 amd64 testing installer**, based on upstream OpenCPN 5.14.0. This is a focused distribution, not the broader Core-Hardening developer bundle. It is a prerelease for desktop testing and is not certified for navigational safety.

Weather Routing **1.17.9.0** includes two selectable native C++ engines. **Main remains the default**, and upgrading preserves existing route and last-used settings. **Quick** is a separate bounded beam-search engine with independent tuning and a configurable 256 MiB default per-route search-storage ceiling. It shares Main's physical propagation and independent final validation, but its more aggressive pruning can miss a feasible or faster route that Main finds.

Each engine now has a bounded **GRIB timeline cache** shared across a departure-time batch. It allocates frames only as required, admits the requested limit only when physical-memory safeguards pass, and releases the cache after the batch. Fresh defaults are 512 MiB for Main and 64 MiB for Quick; saved configurations are preserved.

Chart-aware preparation now shows exact tile progress for each pass, keeps the window responsive and makes **Stop all computations** cancel at the next tile boundary. Routes requiring positive minimum charted depth validate their endpoint tiles first. In the Niue–Vava'u reproduction, this reduced an authoritative missing-depth-coverage rejection from about 44 minutes after 4,074 wider tiles to 2.069 seconds after the two endpoint tiles on the development machine. This is earlier prerequisite validation, not a claimed successful-route speedup.

Advanced now offers all five GSHHG 2.3.7 shoreline levels from 0 — Crude through 4 — Full, bundled for offline use. Main starts at Full on a fresh install; Quick starts at Crude and each remembers its choice. With chart safety enabled and enforced in this preview, chart/depth evidence remains authoritative and the control becomes a separately saved, editable Scout shoreline resolution, initially Crude. Main also gains a bounded final-arrival allowance for routes that exhaust normal work close to the destination. The Advanced page has balanced columns and a separate Cyclone avoidance group while preserving all existing controls and values.

Main can also retry a fully land-rejected long-step layer at the minimum routing step, subject to strict layer and generated-state ceilings. The ordinary path is unchanged when it advances, both sides of an obstruction remain eligible, and active geometry, boundary or cyclone limits disable this guidance. Max Diverted Course is now identified as a hard route-geometry limit independent of Max Search Angle, including an actionable failure diagnostic when a narrower diverted-course limit may exclude the sampled detour.

xGRIB **0.2.5.2**, Environmental GRIB Generator **0.1.8** and all other component pins are retained. The existing release URL is retained. Installing the newer package with APT upgrades the preview without removing its separate profile.

## Install

Download the `.deb` and matching `.sha256` release assets into one directory:

```sh
sha256sum --check opencpn-chart-aware-preview_5.14.0+chartaware.20260915.1_amd64.deb.sha256
sudo apt install ./opencpn-chart-aware-preview_5.14.0+chartaware.20260915.1_amd64.deb
```

Close existing OpenCPN instances, then open **OpenCPN Chart-Aware Preview** from the application menu. Use your ordinary desktop account, not sudo. The download is approximately 274 MiB. The application payload is approximately 624 MiB, plus any Debian dependencies APT needs to install.

The first-run assistant offers fresh settings or a verified backup and independent copy of an existing profile. **Isolated mode is recommended.** Optional replacement supports Debian/APT installations, requires separate confirmation, and first saves the exact original packages for rollback. Original settings are not removed or shared. Imported connections are disabled until reviewed. Plugin binaries and rebuildable caches are not imported. Purchased charts are not backed up by this assistant. See [the installation and recovery guide](https://github.com/pob220/OpenCPN-Chart-Aware/blob/f9ed43e1b3bede8050388523ef9cc762f2cf099c/distribution/INSTALL.md).

## Included

- OpenCPN 5.14.0 with chart/depth safety services, semantic-provider support and focused installation/profile-isolation changes
- Weather Routing **1.17.9.0**, including Main and Quick engines, selectable shoreline detail, preserved configuration, a bounded GRIB timeline cache, responsive cancellable chart preparation, endpoint-first depth validation, chart-aware scouting and improved Main final-arrival handling
- xGRIB **0.2.5.2**, Environmental GRIB Generator **0.1.8** and its runtime
- Updated Climatology with dataset **ocpn-climatology-2026.2**
- Polar **1.2.38.0**
- Modified o-charts semantic provider with the pinned official **2.2.1** helper

The five supplied plugins are enabled; native GRIB is disabled initially. Additional compatible plugins use OpenCPN's normal plugin manager and separate installation folders. Software rendering is the default. OpenGL can be selected explicitly. `opencpn-chart-aware --software` provides a recovery launch. No Vulkan experiment or added external-control service is included.

## Verification performed

The exact run, test counts and installer checksum are added here after the pinned candidate passes its Debian 13 build, dependency-only install, plugin lifecycle and GUI qualification.

Component pins and vendor SHA-256 hashes are in the attached `components.json`. The qualified package assembly revision is recorded after the candidate passes. Weather Routing is pinned to `e5975b7bbd57eb4d2ca95b0dbea810e20605bdf1`; xGRIB to `f5e1ea1019f37af4d8d8e951f43213e8d122f96d`, and its generator to `bf650d8960423461f607f9d96edb257e1092a7b9`.

The downloaded installer was independently checked against its checksum and embedded version/source manifest. All five GSHHG archives were decompressed and checked against the compressed and uncompressed hashes in their embedded manifest. Test reports accompany the release. The original preview tag is retained for a stable download link.

The installer SHA-256 is added after qualification.

## Routing evidence and limits

In controlled development runs of the same Quick policy, a completed Provincetown–Lizard case using Main at 6h/20° took 324.780 seconds and peaked at 1,594.4 MiB process RSS; Quick completed in 69.476–77.886 seconds and peaked at 557.7–557.8 MiB. The 96 MiB and 256 MiB Quick settings produced the same independently validated route and used 0.368 MiB of tracked search storage. These are observations on one Linux machine under controlled inputs, not guaranteed speed or memory figures. Quick's budget applies only to tracked search storage and is not a cap on total OpenCPN memory.

Main remains the broader solver. Quick can miss a feasible passage, useful departure window or faster route because it does not run Main's full recovery search. The 1.17.9 regression set covers configuration migration, independent engine settings, bounded memory/work exhaustion, GRIB cache admission and sharing, authoritative chart rejection, endpoint-first depth validation, chart-preparation progress and cancellation, coastal egress, all five offline shoreline levels and preservation of the earlier Atlantic controls. These Linux results do not establish Windows 32-bit runtime compatibility.

## Still requires real desktop testing

No licensed charts, entitlements, credentials or semantic atlas are distributed. The o-charts provider exports and helper startup were checked, but licensed chart display, semantic access and atlas construction on a real authorized Debian 13 machine have not yet been validated with this installer. Real GPU drivers, TPM/dongles and navigation hardware also require testing. Mesa/Xvfb is not proof that a particular physical GPU works.

Use your own legitimately licensed charts. Confirm chart display and depth-aware route rejection on a small known area before broader testing. Chart-safety service availability alone does not prove chart coverage or that a route is safe. Weather/current downloads require network access and any provider-specific setup. Do not replace the modified o-charts provider with an ordinary catalogue build while testing semantic routing.
