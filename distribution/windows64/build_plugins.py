"""Build the pinned Preview plugins with the native core's MSVC import library."""
import hashlib
import difflib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

from build import ROOT, WORK, STAGE, INSTALLED, CACHE, download, run, cmake_sdk_args, runtime_environment
from fetch_plugins import INPUTS

BUILD = ROOT / 'plugin-build-windows64'
GENERATOR_STAGE = BUILD / 'generator-stage'
DLL_NAMES = {
    'weather_routing': 'xweather_routing_pi.dll',
    'xgrib': 'xgrib_pi.dll',
    'climatology': 'climatology_pi.dll',
    'polar': 'polar_pi.dll',
    'celestial': 'celestial_navigation_pi.dll',
    'offlinetides': 'offlinetides_pi.dll',
}

def native_source_fixes(name, source):
    if name == 'climatology':
        replacements = [
            ('opencpn-libs/wxJSON/include/wx/json_defs.h',
             '#if !defined(snprintf) && defined(_MSC_VER)',
             '#if !defined(snprintf) && defined(_MSC_VER) && _MSC_VER < 1900'),
            ('include/defs.h', '# if !defined(snprintf)',
             '# if !defined(snprintf) && _MSC_VER < 1900'),
            ('opencpn-libs/zlib/CMakeLists.txt', 'if (WIN32)',
             'if (WIN32 AND CMAKE_SIZEOF_VOID_P EQUAL 4)'),
        ]
    elif name == 'celestial':
        replacements = [
            ('test/lunar_ui_smoke_tests.cpp', '#include <wx/filename.h>',
             '#include <wx/filename.h>\n#include <wx/fileconf.h>'),
            ('src/Sight.h',
             '#define isnan _isnan\n#define isinf(x) (!_finite(x) && !_isnan(x))\n\n'
             '#define trunc(d) (((d) > 0) ? floor(d) : ceil(d))',
             'using std::isnan;\nusing std::isinf;\nusing std::trunc;'),
            ('test/CMakeLists.txt', 'add_executable(celestial_tests ${SRC})',
             'add_executable(celestial_tests ${SRC} "' +
             (ROOT / 'distribution/windows64/celestial-test-main.cpp').as_posix() + '")\n'
             '# This executable supplies the host API through mocks.\n'
             'target_compile_options(celestial_tests PRIVATE /UMAKING_PLUGIN)\n'
             'target_compile_definitions(celestial_tests PRIVATE DECL_EXP=)\n'
             'target_include_directories(celestial_tests PRIVATE\n'
             '    $<TARGET_PROPERTY:ocpn::api,INTERFACE_INCLUDE_DIRECTORIES>)'),
            ('test/CMakeLists.txt', '        ocpn::api\n', ''),
            ('test/CMakeLists.txt', '        GTest::Main\n', ''),
            ('src/plugin_dc/dc_utils/CMakeLists.txt',
             'add_library(_DC_UTILS STATIC ${SRC})',
             'add_library(_DC_UTILS STATIC ${SRC})\n'
             '# Static drawing utilities do not export the host API classes.\n'
             'target_compile_definitions(_DC_UTILS PRIVATE DECL_EXP=)'),
        ]
    elif name == 'weather_routing':
        zlib_dll = INSTALLED / 'bin/z.dll'
        if not zlib_dll.is_file():
            raise RuntimeError('The native SDK zlib runtime is missing')
        replacements = [
            ('opencpn-libs/zlib/CMakeLists.txt', 'if (WIN32)',
             'if (WIN32 AND CMAKE_SIZEOF_VOID_P EQUAL 4)'),
            ('test/CMakeLists.txt',
             '${WEATHER_ROUTING_SOURCE_DIR}/opencpn-libs/zlib/win/zlib1.dll',
             zlib_dll.as_posix()),
            ('test/CMakeLists.txt',
             '# zlib1.lib is an import library. Keep its matching x86 DLL beside the\n'
             '       # x86 test executable so GoogleTest discovery cannot select an',
             '# Keep the native SDK zlib DLL beside the test executable\n'
             '       # so GoogleTest discovery cannot select an'),
        ]
        for filename in ('StabilityCorridor_tests.cpp', 'RoutingScenarioJson_tests.cpp'):
            replacements.append(('test/' + filename, '#include <wx/wx.h>',
                                 '#include <wx/wx.h>\n#include <wx/filename.h>'))
        for filename, paths in {
            'StabilityCorridor_tests.cpp': ['weather-routing-stability-test.geojson'],
            'RoutingScenarioJson_tests.cpp': [
                'weather-routing-climatology-on.json',
                'weather-routing-climatology-absent.json',
                'weather-routing-utc-scenario.json',
                'weather-routing-stability-result.json'],
        }.items():
            for path in paths:
                replacements.append(('test/' + filename, '"/tmp/' + path + '"',
                                     'wxFileName::CreateTempFileName("' + path + '-")'))
    else:
        return
    originals = {}
    for relative, needle, replacement in replacements:
        path = source / relative
        before = path.read_text(encoding='utf-8')
        originals.setdefault(relative, before)
        if before.count(needle) != 1:
            raise RuntimeError(f'The native compatibility patch no longer matches {name}/{relative}')
        path.write_text(before.replace(needle, replacement), encoding='utf-8')
    diffs = []
    for relative, before in originals.items():
        after = (source / relative).read_text(encoding='utf-8')
        diffs.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                        fromfile='a/' + relative, tofile='b/' + relative))
    (BUILD / f'{name}-native-fixes.patch').write_text(''.join(diffs), encoding='utf-8')

def bundled_data_defaults(name, source):
    """Use shipped read-only data when the user has not selected private data."""
    if name == 'offlinetides':
        path = source / 'src/xtidal_pi.cpp'
        before = path.read_text(encoding='utf-8')
        needle = '  config->Read("package_path", &package_path_);'
        replacement = needle + '''
  if (package_path_.empty()) {
    const wxString data = GetPluginDataDir("offlinetides_pi");
    const wxString bundled = data + "/data/offlinetides-global-v1.0.0-alpha1.xtdt";
    if (!data.empty() && wxFileExists(bundled)) package_path_ = bundled;
  }'''
        if before.count(needle) != 1:
            raise RuntimeError('OfflineTides settings implementation changed')
        after = before.replace(needle, replacement).replace(
            '#include <wx/fileconf.h>', '#include <wx/fileconf.h>\n#include <wx/filefn.h>')
    elif name == 'celestial':
        path = source / 'src/EclipseDialog.cpp'
        before = path.read_text(encoding='utf-8')
        after = before
        for filename in ('de440s.bsp', 'moon_pa_de440_200625.bpc', 'lola64-pa.bin'):
            needle = f'  return DataDirectory() + "{filename}";'
            replacement = f'''  const wxString private_file = DataDirectory() + "{filename}";
  if (wxFileExists(private_file)) return private_file;
  const wxString data = GetPluginDataDir("celestial_navigation_pi");
  const wxString bundled = data + "/data/eclipse/{filename}";
  return !data.empty() && wxFileExists(bundled) ? bundled : private_file;'''
            if after.count(needle) != 1:
                raise RuntimeError('Celestial eclipse data lookup changed')
            after = after.replace(needle, replacement)
    else:
        return
    changes = [(path, before, after)]
    if name == 'celestial':
        path = source / 'src/Sight.cpp'
        before = path.read_text(encoding='utf-8')
        needle = '''      const wxString path = celestial_navigation_pi::StandardPath() +
                            _T("eclipse") + wxFileName::GetPathSeparator() +
                            _T("de440s.bsp");'''
        replacement = '''      wxString path = celestial_navigation_pi::StandardPath() +
                      _T("eclipse") + wxFileName::GetPathSeparator() +
                      _T("de440s.bsp");
      if (!wxFileName::FileExists(path)) {
        const wxString data = GetPluginDataDir("celestial_navigation_pi");
        const wxString bundled = data + "/data/eclipse/de440s.bsp";
        if (!data.empty() && wxFileName::FileExists(bundled)) path = bundled;
      }'''
        if before.count(needle) != 1:
            raise RuntimeError('Celestial lunar kernel lookup changed')
        changes.append((path, before, before.replace(needle, replacement)))
    diffs = []
    for path, before, after in changes:
        path.write_text(after, encoding='utf-8')
        relative = path.relative_to(source).as_posix()
        diffs.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                        fromfile='a/' + relative, tofile='b/' + relative))
    (BUILD / f'{name}-data-defaults.patch').write_text(''.join(diffs), encoding='utf-8')

def overlay_sources(name):
    # Work on disposable copies; never alter the pinned input repositories.
    source = BUILD / 'sources' / name
    spec = json.loads((ROOT / 'distribution/windows64/components-candidate.json').read_text(encoding='utf-8'))['plugins'][name]
    if not (source / '.git').exists():
        # Preserve plugin Git provenance instead of accidentally discovering the
        # enclosing OpenCPN repository when CMake generates version metadata.
        run('git', 'clone', '--shared', '--no-checkout', INPUTS / name, source)
        run('git', 'checkout', '--detach', spec['revision'], cwd=source)
        run('git', 'remote', 'set-url', 'origin', spec['repository'], cwd=source)
    actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
    if actual != spec['revision']:
        raise RuntimeError(f'Remove the stale disposable build source before rebuilding: {source}')
    shutil.copytree(INPUTS / name, source, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('.git', '__pycache__'))
    import_lib = WORK / 'Release/opencpn.lib'
    if not import_lib.is_file():
        raise RuntimeError(f'The new x64 core import library is missing: {import_lib}')
    changes = []
    version = re.search(r'set\(OCPN_API_VERSION_MINOR\s+"(\d+)"\)',
                        (source / 'CMakeLists.txt').read_text(encoding='utf-8')).group(1)
    api_files = list(source.glob(f'**/api-{version}/CMakeLists.txt'))
    if not api_files:
        raise RuntimeError(f'No plugin API build definition found: {name}')
    for path in api_files:
        before_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        before = path.read_text(encoding='utf-8')
        old = '${CMAKE_CURRENT_SOURCE_DIR}/msvc-wx32/opencpn.lib'
        if old not in before:
            raise RuntimeError(f'Unexpected API import library definition: {path}')
        after = before.replace(old, import_lib.as_posix())
        path.write_text(after, encoding='utf-8')
        changes.append({'file': str(path.relative_to(source)),
                        'before_sha256': before_hash,
                        'after_sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    path = source / 'cmake/PluginInstall.cmake'
    before = path.read_text(encoding='utf-8')
    after = before.replace('  set(CMAKE_INSTALL_PREFIX ${CMAKE_INSTALL_PREFIX}/../OpenCPN)\n', '')
    if before != after:
        path.write_text(after, encoding='utf-8')
        changes.append({'file': 'cmake/PluginInstall.cmake',
                        'change': 'Honor the isolated staging prefix'})
    (BUILD / f'{name}-overlays.json').write_text(json.dumps(changes, indent=2) + '\n')
    native_source_fixes(name, source)
    bundled_data_defaults(name, source)
    return source

def build_generator():
    source = INPUTS / 'xgrib/generator'
    work = BUILD / 'generator'
    run('cmake', '-S', source, '-B', work, *cmake_sdk_args(),
        '-DCMAKE_INSTALL_PREFIX=' + str(GENERATOR_STAGE), '-DBUILD_TESTING=ON')
    run('cmake', '--build', work, '--config', 'Release', '--parallel', '4')
    run('ctest', '--test-dir', work, '-C', 'Release', '--output-on-failure',
        '--no-tests=error', '--timeout', '180')
    run('cmake', '--install', work, '--config', 'Release')
    for dll in (INSTALLED / 'bin').glob('*.dll'):
        shutil.copy2(dll, GENERATOR_STAGE / 'bin')
    for directory in ('eccodes/definitions', 'eccodes/samples', 'proj'):
        shutil.copytree(INSTALLED / 'share' / directory,
                        GENERATOR_STAGE / 'runtime/share' / directory, dirs_exist_ok=True)
    run(sys.executable, ROOT / 'distribution/windows64/verify_pe.py', GENERATOR_STAGE)

def build_plugin(name):
    source = overlay_sources(name)
    work = BUILD / name
    tests = name not in ('polar', 'offlinetides')
    args = ['-DCMAKE_INSTALL_PREFIX=' + str(STAGE),
            '-DCMAKE_BUILD_TYPE=Release', '-DBUILD_TESTING=' + ('ON' if tests else 'OFF'),
            '-DOCPN_BUILD_TEST=' + ('ON' if tests else 'OFF'),
            '-DWXWIDGETS_FORCE_VERSION=3.2', '-DUSE_GL=ON']
    if name == 'xgrib':
        args += ['-DXGRIB_EXTERNAL_GENERATOR_DIR=' + str(GENERATOR_STAGE),
                 '-DXGRIB_USE_BUNDLED_JASPER=ON', '-DBUNDLE_GENERATOR_RUNTIME=ON']
    if name == 'offlinetides':
        args += ['-DXTIDAL_STANDALONE_API=ON', '-DXTIDAL_BUILD_AUTHORING_TOOLS=OFF']
    if name == 'celestial':
        from stage_data import ECLIPSE, ECLIPSE_URL
        # The native test suite verifies and uses the real pinned DE440 kernel.
        kernel = CACHE / 'eclipse-data-2026.1/de440s.bsp'
        download(ECLIPSE_URL + 'de440s.bsp', kernel, ECLIPSE['de440s.bsp'][0])
        target = source / 'eclipse/data/de440s.bsp'
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(kernel, target)
        # Reuse the native static GoogleTest built for the core, with its
        # matching headers, instead of adding a second SDK test library.
        gtest = WORK / 'lib/Release/gtest.lib'
        gtest_main = WORK / 'lib/Release/gtest_main.lib'
        gtest_include = WORK / '_deps/googletest-src/googletest/include'
        if not all(path.exists() for path in (gtest, gtest_main, gtest_include)):
            raise RuntimeError('The native core GoogleTest build is missing')
        args += ['-DGTEST_LIBRARY=' + str(gtest),
                 '-DGTEST_MAIN_LIBRARY=' + str(gtest_main),
                 '-DGTEST_INCLUDE_DIR=' + str(gtest_include)]
    run('cmake', '-S', source, '-B', work, *cmake_sdk_args(), *args)
    run('cmake', '--build', work, '--config', 'Release', '--parallel', '4')
    # Stage successful builds so later diagnostics can exercise the complete
    # runtime even if a unit test fails. CI still requires every stage to pass
    # before creating a tester ZIP.
    run('cmake', '--install', work, '--config', 'Release', '--prefix', STAGE)
    expected = STAGE / 'plugins' / DLL_NAMES[name]
    if not expected.is_file():
        raise RuntimeError(f'Plugin was not installed: {expected}')
    if tests:
        # Retain the actual imported DLL names before trying to execute tests.
        for executable in work.rglob('Release/*tests.exe'):
            imports = subprocess.check_output(['dumpbin', '/dependents', str(executable)],
                                              text=True)
            print(str(executable) + '\n' + imports, flush=True)
            if name == 'celestial' and re.search(r'^\s+opencpn\.exe\s*$', imports,
                                                re.MULTILINE | re.IGNORECASE):
                raise RuntimeError('Celestial tests still import the host executable instead of their mocks')
        run('ctest', '--test-dir', work, '-C', 'Release', '--output-on-failure',
            '--no-tests=error', '--timeout', '180')

def main():
    runtime_environment()
    BUILD.mkdir(exist_ok=True)
    failures = []
    try:
        build_generator()
    except (subprocess.CalledProcessError, RuntimeError, OSError) as error:
        failures.append('xGRIB generator')
        print(f'BUILD FAILED: xGRIB generator: {error}', flush=True)
    for name in DLL_NAMES:
        if name == 'xgrib' and 'xGRIB generator' in failures:
            failures.append(name)
            print('BUILD SKIPPED: xgrib requires its generator', flush=True)
            continue
        try:
            build_plugin(name)
        except (subprocess.CalledProcessError, RuntimeError, OSError) as error:
            failures.append(name)
            print(f'BUILD FAILED: {name}: {error}', flush=True)
    if failures:
        raise SystemExit('Native plugin qualification failed: ' + ', '.join(failures))
    # Retain source, dependency and overlay provenance alongside the binaries.
    evidence = STAGE / 'build-evidence'
    evidence.mkdir(exist_ok=True)
    for path in (ROOT / 'distribution/windows64').glob('*.json'):
        shutil.copy2(path, evidence)
    for path in BUILD.glob('*-overlays.json'):
        shutil.copy2(path, evidence)
    for path in BUILD.glob('*-data-defaults.patch'):
        shutil.copy2(path, evidence)
    for path in BUILD.glob('*-native-fixes.patch'):
        shutil.copy2(path, evidence)
    shutil.copy2(ROOT / 'distribution/windows64/celestial-test-main.cpp', evidence)
    run(sys.executable, ROOT / 'distribution/windows64/verify_pe.py', STAGE)

if __name__ == '__main__':
    if sys.platform != 'win32':
        raise SystemExit('Plugin builds require the native Windows x64 SDK')
    main()
