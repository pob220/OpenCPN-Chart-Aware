#!/usr/bin/python3
"""Unprivileged first-run setup and launcher for OpenCPN Chart-Aware.

Never changes HOME, follows imported symlinks, or writes the source profile.
System package replacement is a separate APT transaction, not profile import.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

PREFIX = Path("/usr/lib/opencpn-chart-aware")
BUNDLED = ("weather_routing", "xgrib", "climatology", "polar", "o-charts")


def state_root():
    return Path.home() / ".local/share/opencpn-chart-aware"


def candidates():
    home = Path.home()
    paths = [home / ".opencpn", home / ".var/app/org.opencpn.OpenCPN/config/opencpn"]
    return [p for p in paths if (p / "opencpn.conf").is_file()]


def check_stopped():
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit():
            continue
        try:
            if (proc / "comm").read_text().strip() == "opencpn":
                raise RuntimeError("Please close all OpenCPN instances before setup or recovery.")
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def config_updates(text, updates):
    """Preserve wxFileConfig values/comments; replace all duplicate target keys."""
    section = ""
    lines = []
    for line in text.splitlines():
        match = re.fullmatch(r"\s*\[(.*)\]\s*", line)
        if match:
            section = match[1].lstrip("/")
        key = line.split("=", 1)[0].strip() if "=" in line else None
        if key and (section, key) in updates:
            continue
        lines.append(line)
    for (section, key), value in updates.items():
        lines.extend([f"[{section}]", f"{key}={value}"])
    return "\n".join(lines) + "\n"


def initial_config(text, renderer):
    updates = {("Settings", "OpenGL"): "1" if renderer == "opengl" else "0",
               ("Settings/GlobalState", "AllowArbitrarySystemPlugins"): "1",
               ("Settings", "RendererBackend"): "opengl-legacy" if renderer == "opengl" else "software",
               ("Settings/NMEADataSource", "DataConnections"): "",
               ("PlugIns/WeatherRouting", "UseExperimentalChartSafety"): "1",
               ("PlugIns/WeatherRouting", "EnforceExperimentalChartSafety"): "1",
               ("PlugIns/WeatherRouting", "ChartSafetyAtlasEnabled"): "1",
               ("PlugIns/WeatherRouting", "ChartSafetyAtlasCompletedIdentity"): ""}
    for section in re.findall(r"^\[/?(PlugIns/[^\]]+\.so)\]", text, re.M):
        updates[(section, "bEnabled")] = "0"
    for name in BUNDLED:
        updates[(f"PlugIns/lib{name}_pi.so", "bEnabled")] = "1"
    updates[("PlugIns/libgrib_pi.so", "bEnabled")] = "0"
    return config_updates(text, updates)


def inventory(source):
    """Snapshot personal state, excluding binaries and rebuildable large caches."""
    excluded = {"SENC", "senc", "raster_texture_cache", "cache", "charts"}
    files, skipped = [], []
    for directory, dirs, names in os.walk(source, followlinks=False):
        parent = Path(directory)
        for name in list(dirs):
            item = parent / name
            installed_plugin_dir = parent.name == "plugins" and name in {"lib", "lib64", "bin", "share", "install_data"}
            if item.is_symlink() or name in excluded or "atlas" in name.lower() or installed_plugin_dir:
                skipped.append(str(item.relative_to(source)))
                dirs.remove(name)
        for name in names:
            item = parent / name
            info = item.lstat()
            if (not stat.S_ISREG(info.st_mode) or name.endswith((".so", ".cache", ".log"))
                    or name == "chartlist.dat"):
                skipped.append(str(item.relative_to(source)))
            else:
                files.append(item.relative_to(source))
    return files, skipped


def initialize(root, source=None, renderer="software"):
    check_stopped()
    root = root.resolve()
    if source:
        source = source.resolve()
        if not (source / "opencpn.conf").is_file() or (source / "opencpn.conf").is_symlink():
            raise RuntimeError("Choose an OpenCPN profile containing a regular opencpn.conf file.")
        if source == root or source in root.parents or root in source.parents:
            raise RuntimeError("Source and destination profiles must not overlap.")
    root.mkdir(parents=True, mode=0o700, exist_ok=True)
    os.chmod(root, 0o700)
    profile = root / "profile"
    if profile.exists():
        raise RuntimeError("A preview profile already exists; it will not be overwritten.")
    backup = None
    files, skipped = [], []
    if source:
        files, skipped = inventory(source)
        size = sum((source / p).stat().st_size for p in files)
        if shutil.disk_usage(root).free < 2 * size + 100 * 1024 * 1024:
            raise RuntimeError("Not enough disk space for a verified backup and profile copy.")
        backup = root / ("backup-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ"))
        backup.mkdir(mode=0o700)
        checksums = {}
        for relative in files:
            src, dest = source / relative, backup / relative
            # Source must remain a regular file throughout the snapshot.
            if src.is_symlink() or not src.is_file():
                raise RuntimeError("Source profile changed during backup; close OpenCPN and retry.")
            dest.parent.mkdir(parents=True, exist_ok=True)
            before = digest(src)
            shutil.copy2(src, dest)
            if digest(dest) != before or digest(src) != before:
                raise RuntimeError(f"Backup verification failed: {relative}")
            checksums[str(relative)] = before
        (backup / "backup-manifest.json").write_text(json.dumps({
            "source": str(source), "sha256": checksums, "excluded": skipped}, indent=2))
    # Only publish a complete new profile. Failed staging/backup remains
    # recoverable for inspection; never remove user data in an error handler.
    staging = Path(tempfile.mkdtemp(prefix="setup-", dir=root))
    for relative in files:
        dest = staging / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup / relative, dest)
    config = staging / "opencpn.conf"
    text = config.read_text() if config.exists() else ""
    config.write_text(initial_config(text, renderer))
    for child in ("plugins/lib/opencpn", "plugins/bin", "plugins/share/opencpn/plugins"):
        (staging / child).mkdir(parents=True, exist_ok=True)
    (staging / "preview-setup.json").write_text(json.dumps({
        "schema": 1, "source": str(source) if source else None,
        "backup": str(backup) if backup else None, "excluded": skipped,
        "connections_disabled_on_import": True, "renderer": renderer}, indent=2))
    staging.rename(profile)
    return profile


def setup_dialog(root):
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    window = tk.Tk()
    window.title("OpenCPN Chart-Aware — first-run setup")
    frame = ttk.Frame(window, padding=20)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text="Stable-based OpenCPN with chart/depth-aware routing", font=("", 14)).pack(anchor="w")
    ttk.Label(frame, text="Your existing OpenCPN and its profile will remain unchanged.\n"
              "Import makes a verified backup and an independent copy.\n"
              "Connections are disabled initially; review them before enabling.\n"
              "Chart files and licensed chart access remain user-supplied.").pack(anchor="w", pady=12)
    source = tk.StringVar(value="")
    ttk.Radiobutton(frame, text="Start with a fresh configuration", variable=source, value="").pack(anchor="w")
    for candidate in candidates():
        ttk.Radiobutton(frame, text=f"Import settings from {candidate}", variable=source, value=str(candidate)).pack(anchor="w")
    def choose():
        chosen = filedialog.askdirectory(title="Choose profile containing opencpn.conf")
        if chosen:
            source.set(chosen)
    ttk.Button(frame, text="Choose another profile…", command=choose).pack(anchor="w", pady=5)
    ttk.Label(frame, textvariable=source, wraplength=650).pack(anchor="w")
    renderer = tk.StringVar(value="software")
    mode = tk.StringVar(value="isolated")
    ttk.Label(frame, text="Installation mode:").pack(anchor="w", pady=(12, 2))
    ttk.Radiobutton(frame, text="Keep existing OpenCPN — isolated preview (recommended)", variable=mode, value="isolated").pack(anchor="w")
    ttk.Radiobutton(frame, text="Replace Debian/APT OpenCPN after backup (opens confirmation terminal)", variable=mode, value="replace").pack(anchor="w")
    ttk.Label(frame, text="Rendering (can be changed later in OpenCPN):").pack(anchor="w", pady=(12, 2))
    ttk.Radiobutton(frame, text="Software — conservative default", variable=renderer, value="software").pack(anchor="w")
    ttk.Radiobutton(frame, text="OpenGL", variable=renderer, value="opengl").pack(anchor="w")
    ttk.Label(frame, text="This standard build contains no Vulkan experiment or external-control service.\n"
              "APT replacement is an advanced, separately confirmed operation;\n"
              "see the included installation guide.", wraplength=650).pack(anchor="w", pady=12)
    result = []
    def create():
        try:
            profile = initialize(root, Path(source.get()) if source.get() else None, renderer.get())
            if mode.get() == "replace":
                subprocess.Popen(["x-terminal-emulator", "-e", "python3", str(PREFIX / "share/opencpn-chart-aware/replace.py")])
                messagebox.showinfo("Profile created", "Complete the separately confirmed replacement in the terminal, then start OpenCPN Chart-Aware from the menu. If replacement is cancelled, the isolated installation remains usable.")
            else:
                result.append(profile)
        except Exception as exc:
            messagebox.showerror("Setup not completed", str(exc))
            return
        window.destroy()
    ttk.Button(frame, text="Create profile and continue", command=create).pack(anchor="e")
    window.mainloop()
    return result[0] if result else None


def launch(profile, args):
    env = os.environ.copy()
    # Remove developer/test overrides that could defeat the installed stack.
    for key in list(env):
        if key.startswith(("WR_HEADLESS_", "OPENCPN_EXTERNAL_CONTROL")):
            del env[key]
    env.update(OPENCPN_CHART_AWARE_PROFILE=str(profile), OPENCPN_CHART_AWARE_PREFIX=str(PREFIX))
    env["OPENCPN_PLUGIN_DIRS"] = f"{profile}/plugins/lib/opencpn:{PREFIX}/lib/opencpn"
    env["PATH"] = f"{profile}/plugins/bin:{PREFIX}/bin:" + env.get("PATH", "/usr/bin:/bin")
    env["XDG_DATA_DIRS"] = f"{profile}/plugins/share:{PREFIX}/share:/usr/local/share:/usr/share"
    # Do not replace HOME: o-charts uses the real user's licensed environment.
    os.execve(PREFIX / "bin/opencpn", [str(PREFIX / "bin/opencpn"), "--configdir=" + str(profile), *args], env)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--initialize", action="store_true")
    parser.add_argument("--import-profile", type=Path)
    parser.add_argument("--software", action="store_true")
    parser.add_argument("--diagnostics", action="store_true")
    options, extra = parser.parse_known_args()
    if os.geteuid() == 0:
        parser.error("Run as your desktop user, never with sudo.")
    os.umask(0o077)
    root = state_root()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (root / "launcher.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        profile = root / "profile"
        if options.diagnostics:
            print((PREFIX / "share/opencpn-chart-aware/components.json").read_text())
            print("Bundled plugin files:", sorted(p.name for p in (PREFIX / "lib/opencpn").glob("*pi.so")))
            print("Profile initialized:", profile.exists())
            return
        if options.initialize or options.import_profile:
            print(initialize(root, options.import_profile))
            return
        if not profile.exists():
            profile = setup_dialog(root)
            if profile is None:
                return
        if not (profile / "preview-setup.json").is_file():
            raise RuntimeError("An unrecognized preview profile exists; preserving it without changes. See the installation guide.")
        if options.software:
            check_stopped()
            config = profile / "opencpn.conf"
            backup = profile / ("opencpn.conf.before-software-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ"))
            shutil.copy2(config, backup)
            config.write_text(config_updates(config.read_text(), {("Settings", "OpenGL"): "0", ("Settings", "RendererBackend"): "software"}))
        if any(a.startswith(("--configdir", "--portable", "-c", "-p")) for a in extra):
            parser.error("Profile overrides are not supported by the isolated launcher.")
        launch(profile, extra)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, BlockingIOError) as exc:
        print(f"OpenCPN Chart-Aware: {exc}", file=sys.stderr)
        sys.exit(1)
