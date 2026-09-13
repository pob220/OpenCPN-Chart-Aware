"""Fetch pinned plugin sources into the isolated Preview build tree."""
import concurrent.futures
import json
from pathlib import Path
import subprocess
from build import ROOT, run

INPUTS = ROOT / 'inputs-windows64'

def fetch(item):
    name, spec = item
    dest = INPUTS / name
    if not dest.exists():
        run('git', 'clone', '--no-checkout', '--filter=blob:none', spec['repository'], dest)
    # Refuse to reset user edits. Build overlays are applied only after fetching.
    dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=dest, text=True)
    unmaterialized = all(p.name == '.git' for p in dest.iterdir())
    if dirty.strip() and not unmaterialized:
        raise RuntimeError(f'Plugin checkout has edits: {dest}')
    run('git', 'fetch', 'origin', spec['revision'], cwd=dest)
    run('git', 'checkout', '--detach', spec['revision'], cwd=dest)
    run('git', 'submodule', 'update', '--init', '--recursive', '--jobs', '4', cwd=dest)
    actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=dest, text=True).strip()
    if actual != spec['revision']:
        raise RuntimeError(f'Wrong revision for {name}: {actual}')
    if name == 'xgrib':
        actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=dest / 'generator', text=True).strip()
        if actual != spec['generator_revision']:
            raise RuntimeError(f'Wrong xGRIB generator revision: {actual}')
    return name

if __name__ == '__main__':
    INPUTS.mkdir(exist_ok=True)
    pins = json.loads((ROOT / 'distribution/windows64/components-candidate.json').read_text())
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for name in pool.map(fetch, pins['plugins'].items()):
            print('Pinned source ready:', name, flush=True)
