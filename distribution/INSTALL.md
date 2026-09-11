# Debian 12 and Debian 13 installation

This is a testing preview, not an official OpenCPN release or a substitute for
checking a passage against current charts and conditions. Initially amd64 only.

## Install

Download the qualified `.deb` for your Debian version and its SHA-256 file from this repository's releases.
Debian 12 (bookworm) packages carry a `+deb12` version suffix. Debian 13
(trixie) packages must not be installed on Debian 12 by upgrading its system libraries.
In the download directory, verify the checksum, then install the exact file:

```
sha256sum --check opencpn-chart-aware-preview_VERSION_amd64.deb.sha256
sudo apt install ./opencpn-chart-aware-preview_VERSION_amd64.deb
```

APT installs the declared dependencies for the package's Debian version. Internet access is needed for
dependencies not already installed. Start **OpenCPN Chart-Aware Preview** from
the application menu, as your ordinary desktop user (never with sudo).

The first-run assistant offers fresh settings or importing an existing native
or Flatpak profile. Close every OpenCPN instance first. Import preserves the
original files, creates a checksum-verified backup of personal settings/navigation
state, and creates a separate working copy. The backup manifest lists excluded
binary-plugin directories, symbolic links and rebuildable caches. It is NOT a
backup of your purchased charts or your entire home directory. Chart paths remain
references to the existing files; missing/moved paths must be corrected in Options.

Weather Routing, xGRIB, Climatology, Polar and modified o-charts are enabled.
Native GRIB is installed but disabled initially. Software rendering is the default;
OpenGL is an explicit setup option and remains available in OpenCPN Options.
Imported Vulkan settings do not enable Vulkan. The standard package contains no
Vulkan implementation or external-control API/server.

For safety, imported input/output connections are initially disabled. The original
connection settings remain in the backup. Review and recreate the connections you
need in Options; do not enable outputs to an autopilot just to test routing.

## Separate profiles and ordinary plugin installation

- Program and bundled resources: `/usr/lib/opencpn-chart-aware/`
- Preview profile: `~/.local/share/opencpn-chart-aware/profile/`
- Profile backups: `~/.local/share/opencpn-chart-aware/backup-*/`
- Additional plugins: `profile/plugins/{lib,bin,share}/`

Use OpenCPN's normal plugin manager for additional plugins compatible with your Debian version.
Its install destinations and search paths are isolated, not just its config file.
Do not copy your old `.so` files into the new installation. Catalog availability of
third-party plugins is outside this distribution's control. Updates to bundled
plugins must be qualified with the core; installing an ordinary o-charts update
over the modified provider can remove semantic routing support.

## Optional replacement of an existing APT installation

Isolated installation is recommended. The assistant can open a replacement
confirmation terminal, or after setup and closing OpenCPN run:

```
opencpn-chart-aware-replace
```

This supports Debian/APT installations only. It refuses manual installations,
missing originals, and an APT plan which would remove unrelated packages. Before
replacement it downloads and verifies the exact installed OpenCPN/opencpn-data
packages into a private `package-recovery-*` directory. If those versions are no
longer obtainable, it stops without removing anything. It asks for `REPLACE`
confirmation before downloading recovery packages, then uses sudo/APT for a
separately confirmed package transaction. No purge is used.

Replacement installs the conventional `opencpn` command, but still uses the preview
profile copy. The original profile is left untouched. Follow the saved recovery
directory's README to reinstall the original packages; new preview routes do not
automatically appear in the original profile (export/import GPX explicitly).

## o-charts and routing checks

No charts, entitlements, credentials or semantic atlas are bundled. Use charts
licensed to this machine and the officially supplied o-charts helper/runtime.
The helper is redistributed unchanged apart from its ELF runtime search path;
the plugin is rebuilt with the chart-safety provider. Machine identity and HOME
are not altered. Dongle/TPM permissions may require the normal o-charts setup on
the tester's system; the installer does not change group memberships silently.

Open a licensed chart and verify it displays, then confirm Weather Routing reports
enhanced chart-safety availability. Build a small atlas and test a known route with
minimum charted depth, including a route which must be rejected. A plugin being
loaded is not proof of licensed semantic access. Missing/unknown depth must not be
treated as safe. Compare cold-cache and warm-cache behaviour and restart OpenCPN.

## Recovery, upgrades, removal

`opencpn-chart-aware --software` backs up the preview configuration and switches
it to software rendering. A desktop action provides the same recovery path.

Upgrade by installing a newer qualified `.deb`; setup does not re-import or reset
an existing profile. Close OpenCPN first. Removing the application with APT does
not delete personal profiles/backups. If replacement mode was used, restore its
original packages as documented before expecting the ordinary command to work.

`opencpn-chart-aware --diagnostics` prints pinned component/build information
without dumping private configuration or o-charts credentials. Include this with
a concise reproduction. Do not publish licensed charts, credentials or atlas data.

## Qualification boundary

Release notes must distinguish automatic tests, clean Debian install/GUI-smoke
checks, and real licensed-chart tests. Do not interpret container smoke tests as
validation of your physical GPU, dongle/TPM, navigation hardware or chart license.
Experimental Vulkan packaging and graphical handling of unsupported replacement
types are not part of the initial standard package.
