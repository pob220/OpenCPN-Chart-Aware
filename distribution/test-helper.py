#!/usr/bin/python3
"""Exercise installed xGRIB runtime without compiler-image libraries/network."""
import json
from pathlib import Path
import subprocess
import tempfile

prefix = Path('/usr/lib/opencpn-chart-aware')
helper = prefix / 'share/opencpn/plugins/xgrib_pi/bin/environmental-grib'
fixtures = prefix / 'share/opencpn-chart-aware/qualification-fixtures'


def output(*args):
    return json.loads(subprocess.check_output([str(helper), *map(str, args)], text=True))


capabilities = output('capabilities')
assert capabilities['schemaVersion'] == 1
assert capabilities['operations'] == ['generateEnvironment']
with tempfile.TemporaryDirectory(prefix='chart-aware-helper-') as directory:
    root = Path(directory)
    result = output('merge-environment-gribs', '--weather', fixtures / 'wind-known.grb2',
                    '--current', fixtures / 'current-differing.grb',
                    '--output', root / 'combined.grb2', '--overwrite')
    assert result['success'] and not result['errors']
    assert result['output_message_count'] == 10
    inspection = result['output_inspection']
    assert inspection['short_name_counts']['10u'] == 2
    assert inspection['short_name_counts']['10v'] == 2
    assert inspection['current_component_counts'] == {'u_49': 3, 'v_50': 3, 'u_grib2': 0, 'v_grib2': 0}
    assert inspection['valid_times'] == ['20260712T0000', '20260712T0300', '20260712T0600']
print('PASS: installed xGRIB helper merges weather/current GRIB fixtures on dependency-only Debian.')
