"""Stage and verify the operational datasets for the complete Preview bundle."""
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

from build import ROOT, CACHE, STAGE, INSTALLED, download
from fetch_plugins import INPUTS

ECLIPSE_URL = ('https://github.com/pob220/celestial_navigation_pi/releases/download/'
               'eclipse-data-2026.1/')
ECLIPSE = {
    'de440s.bsp': ('c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2', 32726016),
    'moon_pa_de440_200625.bpc': ('60cd55aa401ea2ea97360636f567554bfe4e37bb829f901b4460a455dfaf783f', 12863488),
    'lola64-pa.bin': ('f59edf8437442b05525345b3c29b65f0f31af8fc96420abf2dd18af3480f7ff4', 530841624),
    'ECLIPSE_DATA_README.md': ('a948ad393c5891362e57992d0b149c3a84172c5995aaac76a841ed0a3d8a4911', 1937),
}

def verify(path, expected, size=None):
    with path.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != expected or (size is not None and path.stat().st_size != size):
        raise RuntimeError(f'Dataset verification failed: {path}; '
                           f'expected {expected} / {size} bytes, '
                           f'got {actual} / {path.stat().st_size} bytes')
    return {'file': path.relative_to(STAGE).as_posix(), 'sha256': actual,
            'bytes': path.stat().st_size}

def stage_data():
    from build_plugins import DLL_NAMES
    for path in [STAGE / 'opencpn.exe', *(STAGE / 'plugins' / name for name in DLL_NAMES.values())]:
        if not path.is_file():
            raise RuntimeError(f'Cannot exercise an incomplete native runtime: {path}')
    records = []
    pins = json.loads((ROOT / 'distribution/windows64/components-candidate.json').read_text(encoding='utf-8'))
    climate = STAGE / 'plugins/climatology_pi/data'
    manifest = json.loads((climate / 'dataset-manifest.json').read_text(encoding='utf-8'))
    if manifest['dataset_version'] != pins['plugins']['climatology']['dataset']:
        raise RuntimeError('The Climatology dataset is not the pinned 2026.2 build')
    for item in manifest['outputs']:
        records.append(verify(climate / item['file'], item['sha256'], item['bytes']))

    shoreline = STAGE / 'plugins/xweather_routing_pi/data/shoreline'
    manifest = json.loads((shoreline / 'manifest.json').read_text(encoding='utf-8'))
    full = next(item for item in manifest['datasets'] if item['quality'] == 'f')
    records.append(verify(shoreline / full['file'], full['archive_sha256'], full['archive_bytes']))

    tides = pins['plugins']['offlinetides']
    archive = CACHE / 'offlinetides-global-data-1.0.0-alpha1.tar.gz'
    download(tides['data_url'], archive, tides['data_sha256'])
    tides_data = STAGE / 'plugins/offlinetides_pi/data'
    tides_data.mkdir(parents=True, exist_ok=True)
    # Copy only the release's named operational payload and documentation.
    prefix = 'offlinetides-global-data-1.0.0-alpha1/'
    with tarfile.open(archive) as package:
        for name in ('offlinetides-global-v1.0.0-alpha1.xtdt', 'README.txt',
                     'SHA256SUMS', 'manifest.json'):
            member = package.getmember(prefix + name)
            if not member.isfile():
                raise RuntimeError(f'Unexpected dataset archive member: {name}')
            with package.extractfile(member) as stream, (tides_data / name).open('wb') as out:
                shutil.copyfileobj(stream, out)
    records.append(verify(tides_data / 'offlinetides-global-v1.0.0-alpha1.xtdt',
        '418f76d25c69122167876a56ea167b355134b97fbf711044f6002ea8ab17fd3f', 25802358))

    eclipse = STAGE / 'plugins/celestial_navigation_pi/data/eclipse'
    eclipse.mkdir(parents=True, exist_ok=True)
    for name, (sha, size) in ECLIPSE.items():
        cached = CACHE / 'eclipse-data-2026.1' / name
        download(ECLIPSE_URL + name, cached, sha)
        shutil.copy2(cached, eclipse / name)
        records.append(verify(eclipse / name, sha, size))

    licenses = STAGE / 'licenses'
    licenses.mkdir(exist_ok=True)
    for path in ROOT.glob('COPYING.*'):
        shutil.copy2(path, licenses)
    shutil.copy2(ROOT / 'data/copyright', licenses / 'OpenCPN-copyright.txt')
    download('https://raw.githubusercontent.com/wxWidgets/wxWidgets/v3.2.8/docs/licence.txt',
             licenses / 'wxWidgets-licence.txt',
             'e8453be21aea2b7cc9a39d5b0475190bbfa0a60605b4178377590b94d9c43eae')
    for source in INPUTS.iterdir():
        for path in source.rglob('*'):
            if path.is_file() and path.name.lower().split('.')[0] in (
                    'license', 'licence', 'copying', 'copyright', 'notice'):
                target = licenses / 'plugins' / source.name / path.relative_to(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
    for path in (INSTALLED / 'share').glob('*/copyright'):
        target = licenses / 'dependencies' / (path.parent.name + '.txt')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    # CMake DIRECTORY installs should not carry source-control metadata.
    for path in STAGE.rglob('.git'):
        if path.is_file():
            path.unlink()
        else:
            raise RuntimeError(f'Unexpected source-control directory in stage: {path}')
    (STAGE / 'dataset-manifest.json').write_text(json.dumps(records, indent=2) + '\n')
    print(f'Verified {len(records)} operational dataset files', flush=True)

if __name__ == '__main__':
    stage_data()
