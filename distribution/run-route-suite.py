#!/usr/bin/env python3
"""Sequential isolated routing controls; retain every profile and result."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
parser = argparse.ArgumentParser()
parser.add_argument('directory', type=Path)
parser.add_argument('--plugin', type=Path)
args = parser.parse_args()
root = args.directory.resolve()
root.mkdir(parents=True, exist_ok=True)
harness = Path(__file__).with_name('run-route-case.py')
cases = {'wind': [], 'pacific-climatology': ['--climatology', '--pacific'],
         'pacific-climatology-currents': ['--climatology', '--pacific', '--currents'],
         'dateline-climatology': ['--climatology', '--dateline']}
summary = {}
for name, options in cases.items():
    command = ['dbus-run-session', 'xvfb-run', '-a', sys.executable, str(harness), str(root / name), *options]
    if args.plugin:
        command.extend(['--plugin', str(args.plugin.resolve())])
    with (root / (name + '.log')).open('w') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=210)
    summary[name] = result.returncode
    (root / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(name, result.returncode, flush=True)
raise SystemExit(int(any(summary.values())))
