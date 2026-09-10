# Build and provenance

Start from upstream `Release_5.14.0`, commit
`91f3b674366068a6ecd61a5e9aba204bba85f57e`. The chart-only series was replayed from
clean committed sources, not from a tester's working tree:

- `782eb7cc4b550e28eaa63318b169cf1dc599ddc6`: authoritative chart/depth services,
  including licensed provider batching, lifecycle and persistent-cache support.
- `f5c6ed4cb`: actual chart coverage planning.
- `060cc0273` and `3eefb6d4f`: atlas boundary performance.
- `00be12265`: stable provider identities.

Packaging adds opt-in Linux isolation for plugin discovery, resources, installer
metadata, and wxWidgets application data. Both core APIs and plugins using
wxStandardPaths directly use the separate profile. The launcher also preserves
the chosen software/OpenGL setting on first run and upgrades. Without the preview
launcher environment, upstream behaviour remains unchanged. HOME is never replaced.
Vulkan/external-control implementation changes are absent from the baseline.
The historical chart aggregate also includes the segment-safety diagnostic runner
and a developer glutil-path lookup improvement; these are visible in the diff.

## Debian 13 amd64

Use an empty dedicated work directory outside the checkout. Build in Debian 13:

```
docker build -t opencpn-chart-aware-builder:trixie -f distribution/Dockerfile distribution
python3 distribution/fetch-components.py /absolute/work/inputs
docker run --rm -v "$PWD:/src:ro" -v /absolute/work:/work \
  opencpn-chart-aware-builder:trixie bash /src/distribution/build-core.sh /work
docker run --rm -v "$PWD:/src:ro" -v /absolute/work:/work -e OCPN_TARGET=trixie \
  opencpn-chart-aware-builder:trixie bash /src/distribution/build-plugins.sh /work
docker run --rm -v "$PWD:/src:ro" -v /absolute/work:/work \
  opencpn-chart-aware-builder:trixie python3 /src/distribution/make-package.py /work
```

The container build user is UID 1000; make the work directory writable to that UID.
The scripts never install into the host system. Source pins live in components.json.
The o-charts README explicitly permits redistribution of the official helper and
companion library. Their original notices are retained. Polar is initially a pinned
vendor Debian 12 binary, requiring Debian 13 runtime qualification; the modified
o-charts provider and the other three plugins are built natively on Debian 13.

The package assembly fails for missing plugins/dependencies and records the build
revision/checksums. A separate clean Debian 13 runtime test must install the .deb
with APT; the compiler image is not evidence that package dependencies are complete.

Run setup unit tests with `python3 -m unittest discover -s distribution/tests -v`.
Tests must cover old-profile preservation, symlink exclusion, route-setting import,
renderer defaults, native-GRIB disabling, running-process checks and package rollback.

## Before a public installer release

1. Run core chart/depth tests and all component tests; reject zero-test reports.
2. Verify Climatology dataset manifest hashes and the o-charts semantic export.
3. Install on a clean Debian 13 runtime with declared dependencies only.
4. Exercise GUI startup, plugin initialization, xGRIB helper and software recovery.
5. Test installation alongside the Debian package, profile import, upgrade/remove,
   explicitly confirmed replacement and restoration of saved originals.
6. Test licensed o-charts on a real authorized machine; do not claim this from CI.
7. Publish source/provenance and checksums; state outstanding limitations clearly.

Inherited upstream CI workflows are preserved under `.github/upstream-workflows/`
but are not active for this distribution. Nothing uploads to upstream plugin catalogs.
