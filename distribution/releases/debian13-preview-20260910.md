# Debian 13 Chart-Aware Preview — 12 September 2026

This preview branch refreshes Weather Routing to 1.17.4.0, xGRIB to 0.2.5.2
and Environmental GRIB Generator to 0.1.8. Routing preserves completed destination
connections at the search limit and identifies the running build in its log.
xGRIB and the generator add live offline size estimates, measured GRIB totals
and local comparison reports. Estimates are approximate.

Package version: `5.14.0+chartaware.20260912.2`, newer than the earlier 12 September
preview package. The isolated profile and installation/recovery process remain
unchanged. Exact component pins are in `distribution/components.json`.

Build, plugin tests and dependency-only Debian 13 installation/GUI/recovery
qualification must pass before replacing the published preview assets. Final
release notes will record the resulting run, hashes and known limitations.
