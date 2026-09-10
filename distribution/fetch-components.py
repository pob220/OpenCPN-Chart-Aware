#!/usr/bin/python3
"""Fetch only the immutable sources and checksum-verified vendor artifacts."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import urllib.request


def fetch(work):
    manifest = json.loads((Path(__file__).parent / "components.json").read_text())
    work.mkdir(parents=True, exist_ok=True)
    for name in ("weather_routing", "xgrib", "climatology", "ocharts"):
        item = manifest[name]
        dest = work / name
        if not dest.exists():
            subprocess.run(["git", "clone", "--no-checkout", item["repository"], str(dest)], check=True)
        # Never change an existing dirty source checkout.
        if subprocess.check_output(["git", "-C", str(dest), "status", "--porcelain"]).strip():
            # A newly cloned --no-checkout repo has staged deletions: use a
            # bare HEAD test to distinguish it from a populated checkout.
            if (dest / "CMakeLists.txt").exists():
                raise RuntimeError(f"Dirty component: {dest}")
        subprocess.run(["git", "-C", str(dest), "checkout", "--detach", item["revision"]], check=True)
        subprocess.run(["git", "-C", str(dest), "submodule", "update", "--init", "--recursive"], check=True)
        actual = subprocess.check_output(["git", "-C", str(dest), "rev-parse", "HEAD"], text=True).strip()
        assert actual == item["revision"]
    generator = subprocess.check_output(["git", "-C", str(work / "xgrib/generator"), "rev-parse", "HEAD"], text=True).strip()
    assert generator == manifest["xgrib"]["generator_revision"]
    for name, url, digest in (
        ("polar.tar.gz", manifest["polar"]["url"], manifest["polar"]["sha256"]),
        ("ocharts-official.tar.gz", manifest["ocharts"]["official_runtime_url"], manifest["ocharts"]["official_runtime_sha256"]),
    ):
        dest = work / name
        if not dest.exists():
            with urllib.request.urlopen(url, timeout=120) as response, dest.open("xb") as target:
                while chunk := response.read(1024 * 1024):
                    target.write(chunk)
        with dest.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual != digest:
            raise RuntimeError(f"Checksum mismatch: {dest}")


if __name__ == "__main__":
    fetch(Path(sys.argv[1]).resolve())
