#!/bin/bash
set -euo pipefail
source_dir=$(cd "$(dirname "$0")/.." && pwd)
work=${1:?Usage: build-core.sh WORK-DIRECTORY}
mkdir -p "$work/core" "$work/stage" "$work/logs"
git -C "$source_dir" rev-parse HEAD > "$work/logs/core-source-commit.txt"
cmake -S "$source_dir" -B "$work/core" -G Ninja \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DCMAKE_INSTALL_PREFIX=/usr/lib/opencpn-chart-aware \
  -DOCPN_CI_BUILD=ON -DOCPN_DISTRO_BUILD=ON \
  -DOCPN_USE_BUNDLED_LIBS=OFF -DOCPN_BUILD_TEST=ON \
  2>&1 | tee "$work/logs/core-configure.log"
cmake --build "$work/core" --parallel "${BUILD_JOBS:-4}" \
  2>&1 | tee "$work/logs/core-build.log"
dbus-run-session "$work/core/test/tests" \
  --gtest_filter='ChartSafetyDepth.*:ChartSafetyService.*' \
  --gtest_output="xml:$work/logs/core-chart-tests.xml" \
  2>&1 | tee "$work/logs/core-chart-tests.log"
DESTDIR="$work/stage" cmake --install "$work/core" \
  2>&1 | tee "$work/logs/core-install.log"
