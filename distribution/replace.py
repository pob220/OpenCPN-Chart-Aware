#!/usr/bin/python3
"""Explicit, reversible replacement of a Debian-packaged OpenCPN only."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

from preview import PREFIX, check_stopped, state_root


def installed():
    result = {}
    for name in ("opencpn", "opencpn-data"):
        query = subprocess.run(["dpkg-query", "-W", "-f=${Status}\t${Version}", name], capture_output=True, text=True)
        if query.returncode == 0 and query.stdout.startswith("install ok installed\t"):
            result[name] = query.stdout.split("\t", 1)[1]
    return result


def main():
    if os.geteuid() == 0:
        raise RuntimeError("Run this as your desktop user; sudo is requested only for APT.")
    check_stopped()
    if not (state_root() / "profile/preview-setup.json").is_file():
        raise RuntimeError("Complete profile setup first, then close OpenCPN before replacement.")
    packages = installed()
    if "opencpn" not in packages:
        raise RuntimeError("Replacement currently supports Debian/APT OpenCPN only. Use isolated mode for Flatpak or manual installations.")
    executable = shutil.which("opencpn")
    if executable and Path(executable).resolve() != Path("/usr/bin/opencpn").resolve():
        raise RuntimeError("A manually installed OpenCPN takes precedence in PATH; use isolated mode.")
    bridge = PREFIX / "share/opencpn-chart-aware/opencpn-chart-aware-replacement.deb"
    simulation = subprocess.run(["apt-get", "--simulate", "install", str(bridge)], capture_output=True, text=True, check=True)
    removals = {line.split()[1].split(":")[0] for line in simulation.stdout.splitlines() if line.startswith("Remv ")}
    if removals - {"opencpn", "opencpn-data"}:
        raise RuntimeError("APT would remove additional packages; replacement stopped. Use isolated mode.\n" + simulation.stdout)
    print(simulation.stdout)
    print("The existing profile is NOT deleted or shared. The preview keeps its independent copy.")
    print("Exact original .deb packages will be saved before APT changes anything.")
    if input("Type REPLACE to continue: ") != "REPLACE":
        return
    recovery = state_root() / ("package-recovery-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ"))
    recovery.mkdir(mode=0o700)
    for name, version in packages.items():
        subprocess.run(["apt-get", "download", f"{name}={version}"], cwd=recovery, check=True)
    verified = {}
    for archive in recovery.glob("*.deb"):
        fields = subprocess.check_output(["dpkg-deb", "-f", str(archive), "Package", "Version"], text=True)
        fields = dict(line.split(": ", 1) for line in fields.splitlines())
        if packages.get(fields["Package"]) != fields["Version"]:
            raise RuntimeError("Original package archive verification failed; replacement stopped.")
        with archive.open("rb") as stream:
            verified[archive.name] = hashlib.file_digest(stream, "sha256").hexdigest()
    if len(verified) != len(packages):
        raise RuntimeError("Not all original packages were saved; replacement stopped.")
    (recovery / "recovery.json").write_text(json.dumps({"packages": packages, "sha256": verified}, indent=2))
    (recovery / "README.txt").write_text(
        "Original user configuration was left untouched.\n"
        "Close OpenCPN before restoring. Verify recovery.json checksums.\n"
        "Run sudo apt remove opencpn-chart-aware-replacement\n"
        "Then, from THIS directory, run sudo apt install ./*.deb\n"
        "The preview application/profile can remain installed separately.\n")
    check_stopped()
    subprocess.run(["sudo", "apt", "install", str(bridge)], check=True)
    print(f"Replacement completed. Recovery packages: {recovery}")
    print("Start OpenCPN Chart-Aware from the application menu.")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError, EOFError) as exc:
        print(f"Replacement stopped: {exc}", file=sys.stderr)
        sys.exit(1)
