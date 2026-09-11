#!/bin/bash
set -euo pipefail
# This script is intentionally for a DISPOSABLE Debian 12/13 container only.
test -f /.dockerenv || { echo 'Run qualification in a disposable Docker container' >&2; exit 1; }
test "$(id -u)" = 0
package=${1:?Usage: qualify.sh EXACT-PACKAGE-PATH}
test -f "$package"
. /etc/os-release
test "$ID" = debian
case "$VERSION_ID" in 12|13) ;; *) echo 'Expected Debian 12 or 13' >&2; exit 1;; esac
apt-get update
apt-get install -y --no-install-recommends "$package" xvfb xauth xdotool binutils
useradd --create-home --uid 1000 previewtest
runuser -u previewtest -- python3 -m unittest discover -s /src/distribution/tests -v
runuser -u previewtest -- dbus-run-session xvfb-run -a python3 /src/distribution/smoke.py
useradd --create-home gltest
runuser -u gltest -- dbus-run-session xvfb-run -a python3 /src/distribution/smoke.py --opengl
useradd --create-home recoverytest
runuser -u recoverytest -- dbus-run-session xvfb-run -a python3 /src/distribution/smoke.py --software-recovery
runuser -u previewtest -- python3 /src/distribution/test-helper.py
python3 /src/distribution/test-replacement.py "$package"
echo "PASS: dependency-only Debian $VERSION_ID runtime installation and GUI smoke"
