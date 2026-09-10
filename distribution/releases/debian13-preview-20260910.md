# Debian 13 Chart-Aware Preview — 10 September 2026

First **Debian 13 amd64 testing installer**, based on upstream OpenCPN 5.14.0.
This is a focused distribution, not the broader Core-Hardening developer bundle.
It is a prerelease for desktop testing, not a navigational safety certification.

## Install

Download the `.deb` and matching `.sha256` release assets into one directory:

```sh
sha256sum --check opencpn-chart-aware-preview_5.14.0+chartaware.20260910.2_amd64.deb.sha256
sudo apt install ./opencpn-chart-aware-preview_5.14.0+chartaware.20260910.2_amd64.deb
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
- Weather Routing **1.17.1.0**, including the route-table lifetime fix.
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

The uploaded binary was built in Debian 13 and tested outside the compiler image:

- Core chart/depth tests: **14 passed**.
- Weather Routing tests: **222 passed**.
- xGRIB/generator tests: **24 passed**, plus functional merge/reader checks.
- Climatology tests: **3 passed**; packaged dataset manifest hashes verified.
- Profile setup tests: **8 passed**.
- Dependency-only Debian 13 APT installation and real GUI startup/clean shutdown.
- All five plugins loaded and deinitialized; Weather Routing reported full
  chart-safety service availability; native GRIB remained disabled.
- Software default, explicit OpenGL under Mesa/Xvfb, and software recovery checked.
- Ordinary `~/.opencpn` remained absent during isolated GUI tests.
- Installed xGRIB helper merged synthetic weather/current GRIBs successfully.
- Coexistence with Debian OpenCPN, profile import, confirmed APT replacement,
  checksum-verified recovery, exact original package restoration and reinstall
  preserved both profiles.

Component pins and vendor SHA-256 hashes are in the `components.json` release
asset and [source manifest](https://github.com/pob220/OpenCPN-Chart-Aware/blob/main/distribution/components.json). The binary core revision is
`0180420679673ab0543220deb8c0ad08b65ea491`; package assembly revision is
`20f65a938122172cd6d148821da0938881e8d8da`. Later changes to the release tag are
qualification scripts/documentation, not unrecorded changes to those binaries.
Test reports accompany the release. The GitHub workflow separately rebuilds and
qualifies the stack; its current status must not be confused with these local
container results.

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
