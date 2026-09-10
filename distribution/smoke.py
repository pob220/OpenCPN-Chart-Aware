#!/usr/bin/python3
"""Clean-container GUI smoke check. Does not assert licensed chart coverage."""
import configparser
import importlib.util
from pathlib import Path
import subprocess
import signal
import time
import sys

prefix = Path("/usr/lib/opencpn-chart-aware")
spec = importlib.util.spec_from_file_location("preview", prefix / "share/opencpn-chart-aware/preview.py")
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


def main():
    subprocess.run(["opencpn-chart-aware", "--initialize"], check=True)
    profile = preview.state_root() / "profile"
    conf = profile / "opencpn.conf"
    # Exercise the real launcher and acknowledge only its expected disclaimer.
    process = subprocess.Popen(["opencpn-chart-aware"], stdout=subprocess.DEVNULL)
    log = profile / "opencpn.log"
    started = False
    try:
        for _ in range(80):
            if process.poll() is not None:
                raise RuntimeError(f"OpenCPN exited during startup: {process.returncode}")
            text = log.read_text(errors="replace") if log.exists() else ""
            # Accept only the expected disclaimer, not arbitrary dialogs.
            windows = subprocess.run(["xdotool", "search", "--name", "OpenCPN.*(Warning|Disclaimer)|Welcome to OpenCPN"], capture_output=True, text=True)
            for window in windows.stdout.split():
                # The GTK HTML disclaimer has no default keyboard button.
                # Its affirmative button is the rightmost footer button.
                geometry = subprocess.check_output(["xdotool", "getwindowgeometry", "--shell", window], text=True)
                dimensions = dict(line.split("=", 1) for line in geometry.splitlines())
                subprocess.run(["xdotool", "mousemove", "--window", window,
                                str(int(dimensions["WIDTH"]) - 50),
                                str(int(dimensions["HEIGHT"]) - 25), "click", "1"], check=True)
            if "OpenCPN Initialized" in text and not windows.stdout.strip():
                # First-run notices are scheduled after initial frame creation.
                time.sleep(2)
                started = True
                break
            time.sleep(0.5)
        if not started:
            windows = subprocess.run(["xdotool", "search", "--name", ".", "getwindowname", "%@"], capture_output=True, text=True)
            raise RuntimeError("GUI did not initialize. " + windows.stdout + "\n" + (log.read_text(errors="replace")[-8000:] if log.exists() else "No log"))
        text = log.read_text(errors="replace")
        for plugin in preview.BUNDLED:
            if not any("PluginLoader: Loading PlugIn:" in line and f"lib{plugin}_pi.so" in line for line in text.splitlines()):
                raise RuntimeError(f"Plugin was not initialized: {plugin}")
        if "WeatherRouting chart safety:" not in text:
            raise RuntimeError("Weather Routing did not initialize its chart-safety host")
        if "Error loading shared library" in text or "undefined symbol" in text:
            raise RuntimeError("Plugin loader error in startup log")
        print("GUI initialized; all five bundled plugins discovered; chart-safety host initialized.")
    finally:
        if process.poll() is None:
            # OpenCPN's SIGUSR1 handler requests its normal Exit-button path.
            process.send_signal(signal.SIGUSR1)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                raise RuntimeError("OpenCPN failed to stop within the timeout")
    if process.returncode != 0:
        raise RuntimeError(f"OpenCPN shutdown failed: {process.returncode}")
    cfg = configparser.ConfigParser(strict=False, interpolation=None)
    cfg.read(conf)
    if cfg.get("PlugIns/libgrib_pi.so", "bEnabled") != "0":
        raise RuntimeError("Native GRIB became enabled")
    if cfg.get("Settings", "OpenGL") != "0":
        raise RuntimeError("Software default was overridden")
    for plugin in preview.BUNDLED:
        if cfg.get(f"PlugIns/lib{plugin}_pi.so", "bEnabled") != "1":
            raise RuntimeError(f"Bundled plugin disabled after initialization: {plugin}")
    assert not (Path.home() / ".opencpn").exists(), "Isolated launch touched ordinary profile"
    subprocess.run(["opencpn-chart-aware", "--diagnostics"], check=True)
    print("PASS: clean-profile startup, default plugins, native GRIB disabled, ordinary profile untouched.")


if __name__ == "__main__":
    main()
