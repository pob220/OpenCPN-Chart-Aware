# Debian 13 Chart-Aware Preview — 11 September 2026

Refreshed **Debian 13 amd64 testing installer**, based on upstream OpenCPN 5.14.0.
This is a focused distribution, not the broader Core-Hardening developer bundle.
It is a prerelease for desktop testing, not a navigational safety certification.

This refresh updates Weather Routing to **1.17.2.0**, fixing Climatology wind-atlas
initialization and longitude differences in course calculations, while retaining
the route-table lifetime fix. Other bundled plugin and core-code pins are unchanged.
The existing release URL is retained. Installing the newer package with APT upgrades
the preview without removing its separate profile.

## Install

Download the `.deb` and matching `.sha256` release assets into one directory:

```sh
sha256sum --check opencpn-chart-aware-preview_5.14.0+chartaware.20260911.1_amd64.deb.sha256
sudo apt install ./opencpn-chart-aware-preview_5.14.0+chartaware.20260911.1_amd64.deb
```

Close existing OpenCPN instances, then open **OpenCPN Chart-Aware Preview** from
the application menu. Use your ordinary desktop account, not sudo. The download
is approximately 202 MiB; the application payload is approximately 632 MiB, plus
any Debian dependencies APT needs to install.

The first-run assistant offers fresh settings or a verified backup and independent
copy of an existing profile. **Isolated mode is recommended.** Optional replacement
supports Debian/APT installations, requires separate confirmation, and first saves
the exact original packages for rollback. Original settings are not removed or
shared. Imported connections are disabled until reviewed; plugin binaries and
rebuildable caches are not imported. Purchased charts are not backed up by this
assistant. See [the installation and recovery guide](https://github.com/pob220/OpenCPN-Chart-Aware/blob/main/distribution/INSTALL.md).

## Included

- OpenCPN 5.14.0 with chart/depth safety services, semantic-provider support and
  focused installation/profile-isolation changes.
- Weather Routing **1.17.2.0**, including the Climatology/longitude corrections and route-table lifetime fix.
- xGRIB **0.2.4.1**, Environmental GRIB Generator **0.1.7** and its runtime.
- Updated Climatology with dataset **ocpn-climatology-2026.2**.
- Polar **1.2.38.0**.
- Modified o-charts semantic provider with the pinned official **2.2.1** helper.

The five supplied plugins are enabled; native GRIB is disabled initially.
Additional compatible plugins use OpenCPN's normal plugin manager and separate
installation folders. Software rendering is the default. OpenGL can be selected
explicitly; `opencpn-chart-aware --software` provides a recovery launch.
**No Vulkan experiment or added external-control service is included.** An optional
experimental graphics variant remains separate follow-up work.

## Verification performed

The uploaded binary passed [GitHub Actions run 34582785496](https://github.com/pob220/OpenCPN-Chart-Aware/actions/runs/34582785496), building in Debian 13 and testing outside the compiler image:

- Core chart/depth tests: **14 passed**.
- Weather Routing tests: **222 passed**.
- xGRIB/generator tests: **24 passed**, plus functional merge/reader checks.
- Climatology tests: **3 passed**; packaged dataset manifest hashes verified.
- Profile setup tests: **8 passed**.
- Dependency-only Debian 13 APT installation and real GUI startup/clean shutdown.
- All five plugins loaded and deinitialized; Weather Routing initialized its
  chart-safety host; native GRIB remained disabled.
- Software default, explicit OpenGL under Mesa/Xvfb, and software recovery checked.
- Ordinary `~/.opencpn` remained absent during isolated GUI tests.
- Installed xGRIB helper merged synthetic weather/current GRIBs successfully.
- Coexistence with Debian OpenCPN, profile import, confirmed APT replacement,
  checksum-verified recovery, exact original package restoration and reinstall
  preserved both profiles.

Component pins and vendor SHA-256 hashes are in the `components.json` release
asset and [source manifest](https://github.com/pob220/OpenCPN-Chart-Aware/blob/main/distribution/components.json). The binary core revision is
`123c39d858fca6ef1fb46e8b0e6cd45782c95fe4`, also the package assembly revision.
Weather Routing is pinned to `49036e934a4102d8426819f92f3cc5f61ead717f`.
The downloaded installer was additionally checked against its checksum and its
embedded version/source manifest; the attached `components.json` is that embedded
manifest. Test reports accompany the release. The original preview tag name is
retained for a stable download link; the revisions above identify the new binaries.

Installer SHA-256: `d2fb05a3f9274d00448253592bc246408228fcfbf1276d73ad3624295a9c7f9c`.

## Still requires real desktop testing

No licensed charts, entitlements, credentials or semantic atlas are distributed.
The o-charts provider exports and helper startup were checked, but **licensed
chart display, semantic access and atlas construction on a real authorized Debian
13 machine have not yet been validated with this installer**. Real GPU drivers,
TPM/dongles and navigation hardware also require testing. Mesa/Xvfb is not proof
that a particular physical GPU works.

Use your own legitimately licensed charts. Confirm chart display and depth-aware
route rejection on a small known area before broader testing. Chart-safety service
availability alone does not prove chart coverage or that a route is safe.
Weather/current downloads require network access and any provider-specific setup.
Third-party Debian 13 plugin catalogue availability is outside this bundle's
control. Do not replace the modified o-charts provider with an ordinary catalogue
build while testing semantic routing.
