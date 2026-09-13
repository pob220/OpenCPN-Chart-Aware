"""Reproducible native MSVC x64 Preview build. Run on a Windows builder."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'build-windows64'
CACHE = ROOT / 'cache-windows64'
VCPKG = CACHE / 'vcpkg'
TRIPLET = 'x64-windows-release'
WX = CACHE / 'wxWidgets-3.2.8'
WX_LIB = WX / 'lib/vc14x_x64_dll'
STAGE = ROOT / 'stage-windows64'

def run(*args, cwd=ROOT):
    print('+', ' '.join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), cwd=cwd, check=True)

def download(url, path, sha256):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        urllib.request.urlretrieve(url, path)
    if hashlib.sha256(path.read_bytes()).hexdigest() != sha256:
        raise RuntimeError(f'Checksum mismatch: {path}')

def dependencies():
    CACHE.mkdir(exist_ok=True)
    if not (VCPKG / '.git').exists():
        run('git', 'clone', 'https://github.com/microsoft/vcpkg.git', VCPKG)
    pin = json.loads((ROOT / 'distribution/windows64/dependencies.json').read_text())
    run('git', 'checkout', '--detach', pin['vcpkg_revision'], cwd=VCPKG)
    run('cmd', '/c', VCPKG / 'bootstrap-vcpkg.bat', '-disableMetrics')
    run(VCPKG / 'vcpkg.exe', 'install', '--triplet', TRIPLET,
        '--overlay-triplets=' + str(ROOT / 'distribution/windows64/triplets'),
        *pin['ports'])
    WX.mkdir(exist_ok=True)
    for name, sha in pin['wx_archives'].items():
        path = CACHE / name
        download('https://github.com/wxWidgets/wxWidgets/releases/download/v3.2.8/' + name, path, sha)
        run('7z', 'x', '-y', '-o' + str(WX), path)

def build_core():
    installed = VCPKG / 'installed' / TRIPLET
    os.environ['PATH'] = str(WX_LIB) + os.pathsep + str(installed / 'bin') + os.pathsep + os.environ['PATH']
    run('cmake', '-S', ROOT, '-B', WORK, '-G', 'Visual Studio 17 2022', '-A', 'x64',
        '-DCMAKE_TOOLCHAIN_FILE=' + str(VCPKG / 'scripts/buildsystems/vcpkg.cmake'),
        '-DVCPKG_TARGET_TRIPLET=' + TRIPLET,
        '-DVCPKG_OVERLAY_TRIPLETS=' + str(ROOT / 'distribution/windows64/triplets'),
        '-DOCPN_WINDOWS64_PREVIEW=ON', '-DOCPN_TARGET_TUPLE=msvc-wx32-x64;10;x86_64',
        '-DwxWidgets_ROOT_DIR=' + str(WX), '-DwxWidgets_LIB_DIR=' + str(WX_LIB),
        '-DwxWidgets_CONFIGURATION=mswu', '-DOCPN_USE_CRASHREPORT=OFF',
        '-DOCPN_CI_BUILD=ON', '-DOCPN_BUILD_TEST=ON', '-DOCPN_BUNDLE_WXDLLS=ON',
        '-DOCPN_BUNDLE_VCDLLS=OFF', '-DBUNDLE_LIBARCHIVEDLLS=OFF',
        '-DOCPN_BUNDLE_DOCS=OFF', '-DOCPN_BUNDLE_GSHHS=OFF',
        '-DCMAKE_INSTALL_PREFIX=' + str(STAGE), '-DOCPN_VERBOSE=OFF')
    run('cmake', '--build', WORK, '--config', 'Release', '--parallel', '4')
    run('ctest', '--test-dir', WORK, '-C', 'Release', '--output-on-failure', '--timeout', '120')
    run('cmake', '--install', WORK, '--config', 'Release')
    for dll in (installed / 'bin').glob('*.dll'):
        shutil.copy2(dll, STAGE)
    run(sys.executable, ROOT / 'distribution/windows64/verify_pe.py', STAGE)

if __name__ == '__main__':
    if sys.platform != 'win32':
        raise SystemExit('This build requires a native Windows x64 MSVC environment')
    mode = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if mode in ('dependencies', 'all'):
        dependencies()
    if mode in ('core', 'all'):
        build_core()
