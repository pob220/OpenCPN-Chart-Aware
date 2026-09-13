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
INSTALLED = VCPKG / 'installed' / TRIPLET

def cmake_sdk_args():
    return ['-G', 'Visual Studio 17 2022', '-A', 'x64',
            '-DCMAKE_TOOLCHAIN_FILE=' + str(VCPKG / 'scripts/buildsystems/vcpkg.cmake'),
            '-DVCPKG_TARGET_TRIPLET=' + TRIPLET,
            '-DVCPKG_OVERLAY_TRIPLETS=' + str(ROOT / 'distribution/windows64/triplets'),
            '-DwxWidgets_ROOT_DIR=' + str(WX), '-DwxWidgets_LIB_DIR=' + str(WX_LIB),
            '-DwxWidgets_CONFIGURATION=mswu',
            '-DCMAKE_PROJECT_INCLUDE=' + str(ROOT / 'distribution/windows64/native-options.cmake')]

def runtime_environment():
    os.environ['PATH'] = str(WX_LIB) + os.pathsep + str(INSTALLED / 'bin') + os.pathsep + os.environ['PATH']
    os.environ['ECCODES_DEFINITION_PATH'] = str(INSTALLED / 'share/eccodes/definitions')
    os.environ['ECCODES_SAMPLES_PATH'] = str(INSTALLED / 'share/eccodes/samples')
    os.environ['PROJ_DATA'] = str(INSTALLED / 'share/proj')

def run(*args, cwd=ROOT):
    print('+', ' '.join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), cwd=cwd, check=True)

def download(url, path, sha256):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        partial = path.with_suffix(path.suffix + '.part')
        urllib.request.urlretrieve(url, partial)
        with partial.open('rb') as stream:
            actual = hashlib.file_digest(stream, 'sha256').hexdigest()
        if actual != sha256:
            raise RuntimeError(f'Checksum mismatch: {partial}')
        partial.replace(path)
    with path.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != sha256:
        raise RuntimeError(f'Checksum mismatch: {path}')

def dependencies():
    CACHE.mkdir(exist_ok=True)
    if not (VCPKG / '.git').exists():
        run('git', 'clone', 'https://github.com/microsoft/vcpkg.git', VCPKG)
    pin = json.loads((ROOT / 'distribution/windows64/dependencies.json').read_text(encoding='utf-8'))
    run('git', 'checkout', '--detach', pin['vcpkg_revision'], cwd=VCPKG)
    run('cmd', '/c', VCPKG / 'bootstrap-vcpkg.bat', '-disableMetrics')
    # Migrate the earlier multi-TLS SDK cache once. Classic vcpkg otherwise
    # retains the previously requested OpenSSL feature when installing curl.
    schannel_marker = CACHE / 'curl-schannel-default-v1'
    if not schannel_marker.exists() and (INSTALLED / 'lib/libcurl.lib').exists():
        run(VCPKG / 'vcpkg.exe', 'remove', 'curl:' + TRIPLET, '--recurse')
    run(VCPKG / 'vcpkg.exe', 'install', '--triplet', TRIPLET,
        '--overlay-triplets=' + str(ROOT / 'distribution/windows64/triplets'),
        '--overlay-ports=' + str(ROOT / 'distribution/windows64/ports'),
        *pin['ports'])
    run(sys.executable, ROOT / 'distribution/windows64/verify_https.py', INSTALLED / 'bin')
    schannel_marker.write_text('Verified Schannel with Windows certificate validation.\n')
    WX.mkdir(exist_ok=True)
    for name, sha in pin['wx_archives'].items():
        path = CACHE / name
        download('https://github.com/wxWidgets/wxWidgets/releases/download/v3.2.8/' + name, path, sha)
        run('7z', 'x', '-y', '-o' + str(WX), path)

def build_core(phase='all'):
    runtime_environment()
    if phase in ('all', 'build'):
        run('cmake', '-S', ROOT, '-B', WORK, *cmake_sdk_args(),
            '-DOCPN_WINDOWS64_PREVIEW=ON', '-DOCPN_TARGET_TUPLE=msvc-wx32-x64;10;x86_64',
            '-DOCPN_USE_CRASHREPORT=OFF',
            '-DOCPN_CI_BUILD=ON', '-DOCPN_BUILD_TEST=ON', '-DOCPN_BUNDLE_WXDLLS=ON',
            '-DOCPN_BUNDLE_VCDLLS=OFF', '-DBUNDLE_LIBARCHIVEDLLS=OFF',
            '-DOCPN_BUNDLE_DOCS=OFF', '-DOCPN_BUNDLE_GSHHS=ON',
            '-DCMAKE_INSTALL_PREFIX=' + str(STAGE), '-DOCPN_VERBOSE=OFF')
        run('cmake', '--build', WORK, '--config', 'Release', '--parallel', '4')
    if phase in ('all', 'test'):
        # Upstream enables CTest in test/, not in the top-level project.
        run('ctest', '--test-dir', WORK / 'test', '-C', 'Release',
            '--output-on-failure', '--no-tests=error', '--timeout', '120')
    if phase in ('all', 'stage'):
        run('cmake', '--install', WORK, '--config', 'Release')
        for dll in (INSTALLED / 'bin').glob('*.dll'):
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
    elif mode in ('core-build', 'core-test', 'core-stage'):
        build_core(mode.removeprefix('core-'))
