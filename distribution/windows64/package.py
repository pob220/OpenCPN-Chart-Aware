"""Create a tester ZIP only after the complete runtime gate succeeds."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

from build import ROOT, STAGE
from build_plugins import DLL_NAMES
from verify_pe import verify

def package():
    result = json.loads((ROOT / 'windows64-runtime-evidence/result.json').read_text(encoding='utf-8'))
    if (set(result['initialized_plugins']) != set(DLL_NAMES.values()) or
            not all(result.get(key) is True for key in (
                'native_chart_safety_connection', 'bundled_tides_loaded',
                'ordinary_profiles_unchanged', 'forbidden_profile_overrides_rejected',
                'packaged_https_verified'))):
        raise RuntimeError('The complete Preview runtime gate has not passed')
    expected = [STAGE / 'opencpn.exe', STAGE / 'plugins/xgrib_pi/bin/environmental-grib.exe']
    expected.extend(STAGE / 'plugins' / name for name in DLL_NAMES.values())
    for path in expected:
        if not path.is_file():
            raise RuntimeError(f'Missing required native component: {path}')
    (STAGE / 'architecture-manifest.json').write_text(json.dumps(verify(STAGE), indent=2) + '\n')
    (STAGE / 'README-Preview.txt').write_text('''OpenCPN Windows x64 Preview

Extract the whole ZIP to a new folder and run opencpn.exe inside it.
This Preview has a separate profile at:
  %LOCALAPPDATA%\\OpenCPN-64bit-Preview\\profile
It does not import your ordinary OpenCPN profile. Add your chart folders in
Options; the chart files can be shared with your existing installation.
Enable the bundled plugins in Options > Plugins. xGRIB and the built-in GRIB
plugin are alternatives, so normally enable xGRIB and leave built-in GRIB off.

Included: xWeatherRouting, xGRIB with native generator, Celestial Navigation,
Polar 1.2.38.0, Climatology with the 2026.2 dataset, and OfflineTides.
Operational shoreline, climatology, eclipse and tide data are bundled.
Chart-aware routing uses the loaded charts and their available charted depths.
OfflineTides does not add tide-adjusted under-keel clearance in this Preview.
The modified licensed o-charts provider/runtime is not included.

All shipped native executables and DLLs are AMD64. Modern 64-bit Windows gives
large-address-aware 64-bit processes up to 128 TB of virtual address space;
available RAM and system commit still limit actual allocations.

Plugin updates must come from a matching x64 Preview bundle. Existing 32-bit
Windows plugin packages cannot load into this core. Legacy CrashRpt is disabled.
CI exercises software rendering, plugin initialization, the chart-safety API
connection and profile isolation. Real charts, graphics drivers and navigation
devices still require tester qualification. Build evidence and exact source
revisions are included; this is a Preview, not a production qualification.

To update, extract a newer complete ZIP into a new folder. It uses the same
Preview profile. To remove the program, delete its extracted folder. Delete
the separate Preview profile only if you also want to remove Preview settings.

Source: https://github.com/pob220/OpenCPN-Chart-Aware/tree/preview/windows-x64
''', encoding='utf-8')
    evidence = STAGE / 'build-evidence'
    evidence.mkdir(exist_ok=True)
    for name in ('result.json', 'helper-capabilities.json', 'loaded-modules.json', 'https.json'):
        shutil.copy2(ROOT / 'windows64-runtime-evidence' / name, evidence)
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    (evidence / 'core-revision.txt').write_text(revision + '\n')
    artifact = ROOT / 'artifacts-windows64'
    artifact.mkdir(exist_ok=True)
    archive = artifact / f'OpenCPN-Windows-x64-Preview-{revision[:8]}.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as output:
        for path in sorted(STAGE.rglob('*')):
            if path.is_file():
                output.write(path, Path('OpenCPN-Windows-x64-Preview') / path.relative_to(STAGE))
    with archive.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    archive.with_suffix('.zip.sha256').write_text(digest + '  ' + archive.name + '\n')
    print('Created', archive, flush=True)

if __name__ == '__main__':
    package()
