#!/usr/bin/env bash
# Put the working copy on the Home Assistant host and restart core.
#
# Faster than publishing: no tag, no HACS download, and no version number
# spent on an experiment. Releases still go through HACS; this is the loop
# between them.
set -euo pipefail

HOST="${1:-192.168.0.76}"
TARGET="/config/custom_components/room_thermostat"

rsync -a --delete --exclude '__pycache__' \
  custom_components/room_thermostat/ "root@${HOST}:${TARGET}/"

VERSION="$(python3 -c 'import json;print(json.load(open("custom_components/room_thermostat/manifest.json"))["version"])')"
echo "deployed ${VERSION} to ${HOST}"
ssh "root@${HOST}" 'ha core restart'
