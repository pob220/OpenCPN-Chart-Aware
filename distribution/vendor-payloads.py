#!/usr/bin/python3
"""Install checksum-pinned Polar and official o-charts runtime; replace provider."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main(work):
    manifest = json.loads((Path(__file__).parent / "components.json").read_text())
    target = work / "plugin-stage/usr/lib/opencpn-chart-aware"
    for name in ("polar", "ocharts"):
        archive = work / "inputs" / ("polar.tar.gz" if name == "polar" else "ocharts-official.tar.gz")
        expected = manifest[name]["sha256" if name == "polar" else "official_runtime_sha256"]
        with archive.open("rb") as stream:
            assert hashlib.file_digest(stream, "sha256").hexdigest() == expected
        with tempfile.TemporaryDirectory(dir=work) as directory:
            root = Path(directory)
            # These vendor archives were verified against immutable SHA-256
            # pins above. Debian 12's Python lacks tarfile extraction filters;
            # use GNU tar, retaining its default path traversal protections.
            subprocess.run(["tar", "--extract", "--gzip", "--file", str(archive),
                            "--directory", str(root), "--no-same-owner",
                            "--no-same-permissions"], check=True)
            roots = [p for p in root.iterdir() if p.is_dir()]
            assert len(roots) == 1
            payload = roots[0] / "usr/local" if name == "polar" else roots[0]
            # Runtime only, no vendor static libraries or build headers.
            for folder in ("bin", "lib/opencpn", "share"):
                src = payload / folder
                if src.is_dir():
                    shutil.copytree(src, target / folder, dirs_exist_ok=True, symlinks=True)
    built = work / "plugin-build/ocharts"
    shutil.copy2(built / "libo-charts_pi.so", target / "lib/opencpn/libo-charts_pi.so")
    for subdir in ("tpm2-tss-install/lib", "libmnl-install/lib", "json-c-install/lib"):
        for library in (built / subdir).glob("*.so*"):
            dest = target / "lib/opencpn" / library.name
            if not dest.exists():
                shutil.copy2(library, dest, follow_symlinks=False)
    assert (target / "bin/oexserverd").is_file()
    assert (target / "lib/opencpn/libtss2-esys.so").exists()
    notices = target / "share/opencpn-chart-aware/licenses/ocharts"
    notices.mkdir(parents=True, exist_ok=True)
    for name in ("README.md", "COPYING.gplv2"):
        shutil.copy2(work / "inputs/ocharts" / name, notices / name)


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
