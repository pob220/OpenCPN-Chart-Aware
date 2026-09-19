"""Export the native host import library and its matching zlib dependency."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

from build import ROOT, WORK, INSTALLED
from verify_pe import inspect


def export():
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
                                       text=True).strip()
    destination = ROOT / 'artifacts-windows64-sdk'
    destination.mkdir(exist_ok=True)
    sdk = WORK / 'plugin-sdk'
    files = {
        'lib/opencpn.lib': WORK / 'Release/opencpn.lib',
        'lib/zlib.lib': INSTALLED / 'lib/zlib.lib',
        'bin/z.dll': INSTALLED / 'bin/z.dll',
        'include/zlib.h': INSTALLED / 'include/zlib.h',
        'include/zconf.h': INSTALLED / 'include/zconf.h',
        'licenses/zlib.txt': INSTALLED / 'share/zlib/copyright',
        'licenses/OpenCPN.txt': ROOT / 'COPYING.gplv2',
    }
    for relative, source in files.items():
        if source.suffix == '.lib':
            output = subprocess.check_output(['dumpbin', '/headers', str(source)], text=True)
            machines = re.findall(r'(?im)^\s*([0-9a-f]+) machine\b|Machine\s*:\s*([0-9a-f]+)', output)
            if not machines or any((a or b).lower() != '8664' for a, b in machines):
                raise RuntimeError(f'Import library is not exclusively AMD64: {source}')
        elif source.suffix == '.dll':
            inspect(source)
        target = sdk / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    manifest = {
        'core_repository': 'https://github.com/pob220/OpenCPN-Chart-Aware',
        'core_revision': revision,
        'architecture': 'AMD64', 'wx_version': '3.2.8',
        'target': 'msvc-wx32-x64', 'target_version': '10',
        'files': {name: hashlib.sha256((sdk / name).read_bytes()).hexdigest()
                  for name in files},
    }
    (sdk / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    archive = destination / f'OpenCPN-Windows-x64-plugin-sdk-{revision[:8]}.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as output:
        for path in sorted(sdk.rglob('*')):
            if path.is_file():
                output.write(path, path.relative_to(sdk))
    archive.with_suffix('.zip.sha256').write_text(
        hashlib.sha256(archive.read_bytes()).hexdigest() + '  ' + archive.name + '\n')
    print('Exported native SDK:', archive)


if __name__ == '__main__':
    export()
