#!/usr/bin/env bash

set -e

# Usage create-mp3.sh SOURCE_FILE [DESTINATION]
[[ ! ${1} ]] && echo "Usage: create-mp3.sh SOURCE_FILE [DESTINATION]" && exit 1

source="${1}"
target="${2}"
if [[ ! ${target} ]]; then
	target="${source##*/}" # leave only last component of path
	target="${target%.*}"  # strip extension
fi
mkdir -p "${target}"

ffmpeg -i "${source}" -codec:a libmp3lame -qscale:a 5 "${target}/listen.mp3"

echo "Done - encoded MP3 is at ${target}/"
