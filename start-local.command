#!/bin/zsh
# Double-clickable launcher for the PhysEarth-Agent Studio.
#
# A thin wrapper on purpose: `scripts/studio.sh` is the tracked implementation — interpreter
# discovery, a free-port check, and the `PYTHONPATH=src` that the package move requires — and
# duplicating that logic here is how the two drift. This file exists only because macOS needs the
# `.command` extension to run something from Finder.
#
# The previous version of this file called `python app.py` directly and would have died with
# `ModuleNotFoundError: No module named 'physearth'`, because the package lives under `src/`.

cd "$(dirname "$0")" || exit 1

./scripts/studio.sh --open

echo
echo "The Studio has stopped. Press any key to close this window."
read -r -k 1 -s
