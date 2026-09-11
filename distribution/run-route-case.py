#!/usr/bin/env python3
"""Run one controlled route using the installed preview and a private profile."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument('directory', type=Path)
parser.add_argument('--climatology', action='store_true')
parser.add_argument('--pacific', action='store_true')
parser.add_argument('--currents', action='store_true')
parser.add_argument('--dateline', action='store_true')
parser.add_argument('--wide-course', action='store_true')
parser.add_argument('--timeout', type=int, default=120)
parser.add_argument('--plugin', type=Path, help='Explicit candidate library, copied only into this fresh test profile')
args = parser.parse_args()
root = args.directory.resolve()
root.mkdir(parents=True, exist_ok=True)
prefix = Path('/usr/lib/opencpn-chart-aware')
spec = importlib.util.spec_from_file_location('preview', prefix / 'share/opencpn-chart-aware/preview.py')
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)
profile = preview.initialize(root / 'state')
if args.plugin:
    shutil.copy2(args.plugin.resolve(), profile / 'plugins/lib/opencpn/libweather_routing_pi.so')
config = profile / 'opencpn.conf'
config.write_text(preview.config_updates(config.read_text(), {
    ('Plugins/WeatherRouting', 'ConfigVersion'): '117',
    ('PlugIns/WeatherRouting', 'ConfigVersion'): '117',
}))
scenario = {
    'schemaVersion': 1, 'name': 'Short synthetic-grid installed preview control',
    'start': {'name': 'Start', 'lat': 53.05, 'lon': -6.27},
    'end': {'name': 'Finish', 'lat': 53.05, 'lon': -6.15},
    'startTime': '2026-07-12T01:00:00Z',
    'departureOptimization': {'enabled': False},
    'environment': {'useGrib': not args.climatology, 'useCurrents': args.currents,
                    'allowClimatologyFallback': args.climatology},
    'route': {'boatFile': str(prefix / 'share/opencpn/plugins/weather_routing_pi/data/boats/Boat.xml'),
              'timeStepSeconds': 300, 'headingFromDegrees': 40,
              'headingToDegrees': 160, 'headingStepDegrees': 5,
              'maxTrueWindKnots': 100, 'maxApparentWindKnots': 100},
    'safety': {'mode': 'none', 'enforce': False, 'landMarginNm': 0,
               'minimumDepthM': 0, 'persistentCertifiedCacheEnabled': False},
}
scenario_path = root / 'scenario.json'
if args.wide_course:
    scenario['route'].update(maxDivertedCourseDegrees=180, maxCourseAngleDegrees=180)
if args.climatology:
    # Climatology is an ocean dataset; the tiny synthetic fixture overlaps land.
    scenario['name'] = 'Short open-water Climatology control'
    scenario['start'].update(lat=53.5, lon=-5.2)
    scenario['end'].update(lat=53.5, lon=-5.0)
    if args.pacific:
        scenario['name'] = 'Short South Pacific Climatology control'
        scenario['start'].update(lat=-20.0, lon=-175.0)
        scenario['end'].update(lat=-20.0, lon=-174.8)
if args.dateline:
    scenario['name'] = 'Short Climatology control across the date line'
    scenario['start'].update(lat=-20.0, lon=179.9)
    scenario['end'].update(lat=-20.0, lon=-179.9)
scenario_path.write_text(json.dumps(scenario, indent=2) + '\n')
env = os.environ.copy()
env.update(OPENCPN_CHART_AWARE_PROFILE=str(profile), OPENCPN_CHART_AWARE_PREFIX=str(prefix),
           OPENCPN_PLUGIN_DIRS=f'{profile}/plugins/lib/opencpn:{prefix}/lib/opencpn',
           XDG_DATA_DIRS=f'{profile}/plugins/share:{prefix}/share:/usr/local/share:/usr/share',
           PATH=f'{profile}/plugins/bin:{prefix}/bin:' + env.get('PATH','/usr/bin:/bin'),
           WR_HEADLESS_SCENARIO=str(scenario_path), WR_HEADLESS_OUTPUT=str(root / 'result.json'),
           WR_HEADLESS_TIMEOUT_MS=str(args.timeout * 1000))
if not args.climatology:
    shutil.copy2(prefix / 'share/opencpn-chart-aware/qualification-fixtures/wind-known.grb2', root / 'wind.grb2')
    env['WR_HEADLESS_GRIB_FILE'] = str(root / 'wind.grb2')
with (root / 'process.log').open('w') as output:
    process = subprocess.Popen([str(prefix / 'bin/opencpn'), '--configdir=' + str(profile), '--no_opengl'],
                               env=env, stdout=output, stderr=subprocess.STDOUT)
    deadline = time.monotonic() + args.timeout + 45
    while process.poll() is None and time.monotonic() < deadline:
        # Only this newly created profile is eligible for importing examples.
        imports = subprocess.run(['xdotool','search','--name','^New or updated data available$'],
                                 capture_output=True, text=True)
        for window in imports.stdout.split():
            subprocess.run(['xdotool','key','--window',window,'Return'], check=False)
        windows = subprocess.run(['xdotool','search','--name','OpenCPN.*(Warning|Disclaimer)|Welcome to OpenCPN'],
                                 capture_output=True, text=True)
        for window in windows.stdout.split():
            geometry = subprocess.run(['xdotool','getwindowgeometry','--shell',window],capture_output=True,text=True)
            if geometry.returncode:
                continue
            dimensions = dict(line.split('=',1) for line in geometry.stdout.splitlines())
            subprocess.run(['xdotool','mousemove','--window',window,str(int(dimensions['WIDTH'])-50),
                            str(int(dimensions['HEIGHT'])-25),'click','1'], check=False)
        time.sleep(0.5)
    if process.poll() is None:
        process.send_signal(signal.SIGUSR1)
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
result_file = root / 'result.json'
result = json.loads(result_file.read_text()) if result_file.exists() else {'status': 'missing-result'}
print(json.dumps({'exit_code': process.returncode, 'result': result}, indent=2))
passed = process.returncode == 0 and result.get('status') == 'complete'
if passed:
    candidates = result.get('candidates', [])
    passed = len(candidates) == 1 and candidates[0].get('state') == 'complete'
    route = candidates[0].get('route', []) if candidates else []
    passed = passed and len(route) >= 2
    if passed:
        for point, expected in ((route[0], scenario['start']), (route[-1], scenario['end'])):
            lon_error = (point['longitudeDegrees'] - expected['lon'] + 180) % 360 - 180
            passed = passed and abs(point['latitudeDegrees'] - expected['lat']) < 1e-6 and abs(lon_error) < 1e-6
raise SystemExit(0 if passed else 1)
