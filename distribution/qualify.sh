#!/bin/bash
set -euo pipefail
# This script is intentionally for a DISPOSABLE Debian 13 container only.
test -f /.dockerenv || { echo 'Run qualification in a disposable Docker container' >&2; exit 1; }
test "$(id -u)" = 0
package=${1:?Usage: qualify.sh EXACT-PACKAGE-PATH}
test -f "$package"
. /etc/os-release
test "$ID" = debian && test "$VERSION_ID" = 13
apt-get update
apt-get install -y --no-install-recommends "$package" xvfb xauth xdotool binutils
useradd --create-home --uid 1000 previewtest
runuser -u previewtest -- python3 -m unittest discover -s /src/distribution/tests -v
runuser -u previewtest -- dbus-run-session xvfb-run -a python3 /src/distribution/smoke.py
helper=/usr/lib/opencpn-chart-aware/share/opencpn/plugins/xgrib_pi/bin/environmental-grib
runuser -u previewtest -- "$helper" --help
echo 'PASS: dependency-only Debian 13 runtime installation and GUI smoke'
