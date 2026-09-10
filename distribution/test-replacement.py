#!/usr/bin/python3
"""Destructive APT lifecycle test: DISPOSABLE Debian container only."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def run(args, **kwargs):
    return subprocess.run(args, check=True, text=True, **kwargs)


def main(package):
    if os.geteuid() != 0 or not Path('/.dockerenv').exists():
        raise RuntimeError('Only run in a disposable root Docker container')
    run(['apt-get', 'install', '-y', '--no-install-recommends', 'opencpn'])
    run(['useradd', '--create-home', 'replacementtest'])
    home = Path('/home/replacementtest')
    original = home / '.opencpn'
    original.mkdir()
    original_text = '[Settings]\nOpenGL=0\n[ChartDirectories]\nChartDir1=/example/charts\n'
    (original / 'opencpn.conf').write_text(original_text)
    (original / 'navobj.xml').write_text('<gpx version="1.1"/>')
    run(['chown', '-R', 'replacementtest:replacementtest', str(original)])
    as_user = ['runuser', '-u', 'replacementtest', '--']
    run(as_user + ['opencpn-chart-aware', '--import-profile', str(original)])
    state = home / '.local/share/opencpn-chart-aware'
    profile = state / 'profile'
    config_before = (profile / 'opencpn.conf').read_bytes()
    # This temporary sudo rule exists only inside the disposable test container.
    rule = Path('/etc/sudoers.d/chart-aware-test')
    rule.write_text('replacementtest ALL=(root) NOPASSWD: /usr/bin/apt\n')
    rule.chmod(0o440)
    run(as_user + ['opencpn-chart-aware-replace'], input='REPLACE\ny\n')
    recovery = next(state.glob('package-recovery-*'))
    manifest = json.loads((recovery / 'recovery.json').read_text())
    for name, expected in manifest['sha256'].items():
        with (recovery / name).open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == expected
    assert 'opencpn-chart-aware' in Path('/usr/bin/opencpn').read_text()
    assert (original / 'opencpn.conf').read_text() == original_text
    assert (profile / 'opencpn.conf').read_bytes() == config_before
    run(['apt-get', 'remove', '-y', 'opencpn-chart-aware-replacement'])
    run(['apt-get', 'install', '-y', *map(str, recovery.glob('*.deb'))])
    for name, version in manifest['packages'].items():
        actual = subprocess.check_output(['dpkg-query', '-W', '-f=${Version}', name], text=True)
        assert actual == version, (name, actual, version)
    # Reinstallation/upgrade must not replace user configuration.
    run(['apt-get', 'install', '--reinstall', '-y', str(package)])
    assert (original / 'opencpn.conf').read_text() == original_text
    assert (profile / 'opencpn.conf').read_bytes() == config_before
    print('PASS: APT coexistence, profile import, explicit replacement, verified recovery and reinstall preserve both profiles.')


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
