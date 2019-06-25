#!/usr/bin/env bash

set -e

# Usage create-tn.sh SOURCE_FILE [DESTINATION]
[[ ! "${1}" ]] && echo "Usage: create-tn.sh SOURCE_FILE [DESTINATION]" && exit 1

source="${1}"
target="${2}"
if [[ ! "${target}" ]]; then
  target="${source##*/}" # leave only last component of path
  target="${target%.*}"  # strip extension
fi
mkdir -p ${target}

convert "${source}" -auto-orient -background white -alpha remove -alpha off -thumbnail 400x300^ -gravity center -extent 400x300 "${target}/tn.jpg"

echo "Done - thumbnail is at ${target}/"
