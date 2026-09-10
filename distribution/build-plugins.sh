#!/bin/bash
set -euo pipefail
work=${1:?Usage: build-plugins.sh WORK-DIRECTORY}
prefix=/usr/lib/opencpn-chart-aware
jobs=${BUILD_JOBS:-4}
mkdir -p "$work/logs" "$work/plugin-stage"

for name in ${PLUGIN_COMPONENTS:-weather_routing xgrib climatology}; do
  source_dir="$work/inputs/$name"
  build_dir="$work/plugin-build/$name"
  options=()
  case "$name" in
    weather_routing) options=(-DWEATHER_ROUTING_STANDALONE_API=ON -DOCPN_BUILD_TEST=ON);;
    xgrib) options=(-DBUNDLE_GENERATOR_RUNTIME=ON -DXGRIB_USE_BUNDLED_JASPER=ON);;
    climatology) options=(-DBUILD_TESTING=ON);;
  esac
  cmake -S "$source_dir" -B "$build_dir" -G Ninja \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$prefix" \
    "${options[@]}" 2>&1 | tee "$work/logs/$name-configure.log"
  cmake --build "$build_dir" --parallel "$jobs" \
    2>&1 | tee "$work/logs/$name-build.log"
  ctest --test-dir "$build_dir" --output-on-failure \
    --output-junit "$work/logs/$name-tests.xml" \
    2>&1 | tee "$work/logs/$name-tests.log"
  if [[ "$name" == weather_routing ]]; then
    # Avoid installing test-only libraries with the end-user plugin.
    cmake -S "$source_dir" -B "$build_dir" -DOCPN_BUILD_TEST=OFF
  fi
  DESTDIR="$work/plugin-stage" cmake --install "$build_dir" \
    > "$work/logs/$name-install.log" 2>&1
  echo "Installed $name; details in $work/logs/$name-install.log"
  if [[ "$name" == xgrib ]]; then
    bash "$source_dir/scripts/run-functional-merge-test.sh" "$build_dir" "$work/logs/xgrib-functional"
    bash "$source_dir/scripts/test-packaged-helper.sh" "$work/plugin-stage$prefix"
  fi
done

source_dir="$work/inputs/ocharts"
build_dir="$work/plugin-build/ocharts"
cmake -S "$source_dir" -B "$build_dir" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$work/ocharts-build-install" -DBUILD_TYPE=tarball \
  2>&1 | tee "$work/logs/ocharts-configure.log"
cmake --build "$build_dir" --target o-charts_pi --parallel "$jobs" \
  2>&1 | tee "$work/logs/ocharts-build.log"
python3 /src/distribution/vendor-payloads.py "$work"
