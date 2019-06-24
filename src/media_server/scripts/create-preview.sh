#!/usr/bin/env bash

set -e

# Usage create-vod-hls.sh SOURCE_FILE [OUTPUT_NAME]
[[ ! "${2}" ]] && echo "Usage: create-preview.sh HOST SOURCE_FILE [OUTPUT_NAME]" && exit 1

host="${1}"
source="${2}"
target="${3}"
if [[ ! "${target}" ]]; then
  target="${source##*/}" # leave only last component of path
  target="${target%.*}"  # strip extension
fi
mkdir -p ${target}

if [[ $(head -c 4 "${source}") = "%PDF" ]]; then
    cp ${source} "${target}/preview.pdf"
else
    curl -F "data=@${source}" "${host}/lool/convert-to/pdf" > "${target}/preview.pdf"
fi

convert -density 300 -resize 20% -alpha remove "${target}/preview.pdf[0]" "${target}/preview.jpg"

echo "Done - preview is at ${target}/"
