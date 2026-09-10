# OpenCPN Chart-Aware Preview

A focused Debian 13 installer for chart/depth-aware Weather Routing, based on
upstream **OpenCPN 5.14.0**, not the broader Core-Hardening developer bundle.

**Development in progress. Do not assume an installer is qualified until a release
explicitly records its test results.**

The stack includes Weather Routing 1.17.1, xGRIB 0.2.4.1 (Generator 0.1.7),
Climatology dataset 2026.2, Polar and the modified o-charts semantic provider.
Native GRIB is disabled by default. Additional compatible plugins use the normal
OpenCPN plugin manager, with independent installation folders.

- [Install, import, replacement and recovery](distribution/INSTALL.md)
- [Exact component source revisions and vendor checksums](distribution/components.json)
- [Build and scope](distribution/DEVELOPMENT.md)

The standard variant has software/OpenGL rendering, no Vulkan experiment, and no
external-control service. A separate optional experimental-graphics variant is a
follow-up, not silently included in this build.

No licensed charts, credentials, machine-specific data or personal settings are
stored in this repository or distributed in packages. This is experimental passage
planning software; routes require independent checks and are not guaranteed safe.

Upstream history and licenses are retained. The original upstream README is
available as [README](README).
