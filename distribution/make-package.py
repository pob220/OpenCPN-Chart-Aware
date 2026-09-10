#!/usr/bin/python3
"""Assemble the complete Debian 13 application and explicit replacement bridge."""
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PREFIX = Path("usr/lib/opencpn-chart-aware")


def write(path, text, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    path.chmod(mode)


def dependencies(root):
    elf = []
    for path in root.rglob("*"):
        if path.is_file() and not path.is_symlink():
            with path.open("rb") as stream:
                if stream.read(4) == b"\x7fELF":
                    elf.append(path)
    prefix = root / PREFIX
    directories = [prefix / 'lib/opencpn', prefix / 'lib', prefix / 'bin']
    xgrib = prefix / 'share/opencpn/plugins/xgrib_pi'
    packages = {"python3", "python3-tk", "sudo", "xterm", "librsvg2-common", "ca-certificates", "libwxgtk-webview3.2-1t64"}
    checked = set()
    for path in elf:
        search = ([xgrib / 'runtime/lib'] if xgrib in path.parents else []) + directories
        env = dict(os.environ, LD_LIBRARY_PATH=":".join(map(str, search)))
        info = subprocess.run(["ldd", str(path)], text=True, capture_output=True, env=env)
        if "not found" in info.stdout:
            raise RuntimeError(f"Missing dependency in {path}:\n{info.stdout}")
        for line in info.stdout.splitlines():
            words = line.split()
            library = next((Path(w) for w in words if w.startswith("/")), None)
            if not library or root in library.parents or library in checked:
                continue
            checked.add(library)
            owner = subprocess.run(["dpkg-query", "-S", str(library.resolve())], capture_output=True, text=True)
            if owner.returncode:
                owner = subprocess.run(["dpkg-query", "-S", str(library)], capture_output=True, text=True, check=True)
            owners = [line.split(": ", 1)[0].split(":", 1)[0]
                      for line in owner.stdout.splitlines()
                      if re.match(r"^[a-z0-9][a-z0-9+.-]*(?::[a-z0-9-]+)?: /", line)]
            if not owners:
                raise RuntimeError(f"Cannot identify Debian owner of {library}: {owner.stdout}")
            packages.update(owners)
    return sorted(packages)


def main(work):
    if subprocess.check_output(["dpkg", "--print-architecture"], text=True).strip() != "amd64":
        raise RuntimeError("Initial vendor runtime pins are amd64-only.")
    version = os.environ.get("PREVIEW_VERSION", "5.14.0+chartaware.20260910.2")
    root = work / "deb-root"
    if root.exists():
        raise RuntimeError(f"Refusing to overwrite package staging: {root}")
    prefix = root / PREFIX
    # Only the declared installation prefix is package payload, never build
    # directories accidentally created by third-party install scripts.
    shutil.copytree(work / "stage" / PREFIX, prefix, symlinks=True)
    shutil.copytree(work / "plugin-stage" / PREFIX, prefix, dirs_exist_ok=True, symlinks=True)
    # Absolute install RPATHs are fine for the fixed private prefix; use
    # relative provider/helper RPATHs for their bundled companion libraries.
    runtime_files = [prefix / "lib/opencpn/libo-charts_pi.so", prefix / "bin/oexserverd"]
    runtime_files.extend(p for p in (prefix / "lib/opencpn").glob("libtss2*.so*") if not p.is_symlink())
    for file in runtime_files:
        subprocess.run(["patchelf", "--set-rpath", "$ORIGIN:$ORIGIN/../lib/opencpn", str(file)], check=True)
    required = ["weather_routing", "xgrib", "climatology", "polar", "o-charts", "grib"]
    for name in required:
        if not (prefix / f"lib/opencpn/lib{name}_pi.so").is_file():
            raise RuntimeError(f"Required plugin missing: {name}")
    climate = prefix / "share/opencpn/plugins/climatology_pi/data"
    dataset = json.loads((climate / "dataset-manifest.json").read_text())
    if dataset["dataset_version"] != "ocpn-climatology-2026.2" or not dataset["outputs"]:
        raise RuntimeError("Unexpected or empty Climatology dataset manifest")
    for entry in dataset["outputs"]:
        datafile = climate / entry["file"]
        if climate.resolve() not in datafile.resolve().parents:
            raise RuntimeError("Invalid Climatology manifest path")
        with datafile.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != entry["sha256"]:
                raise RuntimeError(f"Climatology data checksum mismatch: {entry['file']}")
    symbols = subprocess.check_output(["nm", "-D", str(prefix / "lib/opencpn/libo-charts_pi.so")], text=True)
    if "OCPN_PluginChartSafetyGridV1" not in symbols or "OCPN_PluginChartSafetyIdentityV1" not in symbols:
        raise RuntimeError("o-charts is missing its semantic provider exports")
    core_symbols = subprocess.check_output(["nm", "-D", str(prefix / "bin/opencpn")], text=True)
    for symbol in ("PlugIn_CheckSegmentSafety", "PlugIn_GetSegmentSafetyChartCoverageTiles", "PlugIn_RegisterSegmentSafetyTileCache"):
        if symbol not in core_symbols:
            raise RuntimeError(f"Core chart-safety export missing: {symbol}")
    doc = prefix / "share/opencpn-chart-aware"
    doc.mkdir(parents=True, exist_ok=True)
    fixtures = doc / "qualification-fixtures"
    fixtures.mkdir(exist_ok=True)
    for name in ("wind-known.grb2", "current-differing.grb"):
        shutil.copy2(work / "logs/xgrib-functional/fixtures" / name, fixtures / name)
    write(fixtures / "README.txt", "Synthetic xGRIB test data, not a forecast. Generated by the pinned xGRIB merge tests.\n")
    for name in ("preview.py", "replace.py", "components.json", "INSTALL.md"):
        shutil.copy2(HERE / name, doc / name)
    source_revision = subprocess.check_output(["git", "-C", str(HERE.parent), "rev-parse", "HEAD"], text=True).strip()
    manifest = json.loads((doc / "components.json").read_text())
    core_revision = (work / "logs/core-source-commit.txt").read_text().strip()
    manifest.update(distribution_revision=source_revision, core_revision=core_revision, package_version=version, target="debian13-amd64", renderer="software/OpenGL; no Vulkan")
    (doc / "components.json").write_text(json.dumps(manifest, indent=2))
    write(root / "usr/bin/opencpn-chart-aware", "#!/bin/sh\nexec /usr/bin/python3 /usr/lib/opencpn-chart-aware/share/opencpn-chart-aware/preview.py \"$@\"\n", 0o755)
    write(root / "usr/bin/opencpn-chart-aware-replace", "#!/bin/sh\nexec /usr/bin/python3 /usr/lib/opencpn-chart-aware/share/opencpn-chart-aware/replace.py \"$@\"\n", 0o755)
    desktop = root / "usr/share/applications"
    desktop.mkdir(parents=True, exist_ok=True)
    shutil.copy2(HERE / "opencpn-chart-aware.desktop", desktop)
    icons = list((prefix / "share/icons").rglob("opencpn.png"))
    if icons:
        icon = root / "usr/share/icons/hicolor/48x48/apps/opencpn-chart-aware.png"
        icon.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(icons[0], icon)
    bridge = work / "replacement-root"
    write(bridge / "DEBIAN/control", f"Package: opencpn-chart-aware-replacement\nVersion: {version}\nArchitecture: all\nMaintainer: Paul OBrien <leblanc_leblanc@hotmail.com>\nDepends: opencpn-chart-aware-preview (>= 5.14.0)\nConflicts: opencpn, opencpn-data\nReplaces: opencpn, opencpn-data\nSection: misc\nPriority: optional\nDescription: Explicit APT replacement bridge for OpenCPN Chart-Aware\n Installs the conventional command after a separately confirmed replacement.\n")
    write(bridge / "usr/bin/opencpn", "#!/bin/sh\nexec /usr/bin/opencpn-chart-aware \"$@\"\n", 0o755)
    subprocess.run(["dpkg-deb", "--root-owner-group", "--build", str(bridge), str(doc / "opencpn-chart-aware-replacement.deb")], check=True)
    deps = dependencies(root)
    write(root / "DEBIAN/control", f"Package: opencpn-chart-aware-preview\nVersion: {version}\nArchitecture: amd64\nMaintainer: Paul OBrien <leblanc_leblanc@hotmail.com>\nDepends: {', '.join(deps)}\nSection: misc\nPriority: optional\nHomepage: https://github.com/pob220/OpenCPN-Chart-Aware\nDescription: Stable-based OpenCPN with chart-aware Weather Routing\n Includes Weather Routing, xGRIB, Climatology 2026.2, Polar and the modified\n o-charts provider. Uses an independent user profile. Charts are not included.\n")
    copyright_dir = root / "usr/share/doc/opencpn-chart-aware-preview"
    copyright_dir.mkdir(parents=True, exist_ok=True)
    write(copyright_dir / "copyright", "OpenCPN: GPL-2.0-or-later; Weather Routing, xGRIB and other bundled components retain their respective licenses.\nSee /usr/lib/opencpn-chart-aware/share/opencpn-chart-aware/licenses and the pinned source repositories in components.json.\nThe o-charts README permits redistribution of its closed-source helper/runtime; no chart data or entitlements are included.\n")
    licenses = doc / "licenses"
    licenses.mkdir(exist_ok=True)
    for license_file in HERE.parent.glob("COPYING.*"):
        shutil.copy2(license_file, licenses / license_file.name)
    for name in ("weather_routing", "xgrib", "climatology", "ocharts", "polar"):
        target = licenses / name
        target.mkdir(exist_ok=True)
        for pattern in ("COPYING*", "LICENSE*", "README*"):
            for notice in (work / "inputs" / name).glob(pattern):
                if notice.is_file():
                    shutil.copy2(notice, target / notice.name)
    shutil.copy2(HERE / "INSTALL.md", copyright_dir / "README.md")
    out = work / "packages"
    out.mkdir(exist_ok=True)
    package = out / f"opencpn-chart-aware-preview_{version}_amd64.deb"
    subprocess.run(["dpkg-deb", "--root-owner-group", "-Zzstd", "--build", str(root), str(package)], check=True)
    with package.open("rb") as stream:
        checksum = hashlib.file_digest(stream, "sha256").hexdigest()
    write(Path(str(package) + ".sha256"), f"{checksum}  {package.name}\n")
    print(package)


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
