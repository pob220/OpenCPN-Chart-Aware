#!/usr/bin/python3
"""Normalize xGRIB's nested DESTDIR runtime without changing pinned sources.

Its CMake file(INSTALL) applies DESTDIR a second time to an already staged path.
Keep the original staging evidence; copy only the intended helper runtime.
"""
from pathlib import Path
import shutil
import sys

stage = Path(sys.argv[1]).resolve()
relative = Path('usr/lib/opencpn-chart-aware/share/opencpn/plugins/xgrib_pi/runtime')
nested = stage / stage.relative_to('/') / relative
target = stage / relative
if nested.is_dir():
    shutil.copytree(nested, target, dirs_exist_ok=True, symlinks=True)
if not (target / 'lib/libeccodes.so.0').is_file():
    raise RuntimeError('xGRIB staged runtime is missing ecCodes')
print('xGRIB helper runtime staged in its declared installation directory.')
