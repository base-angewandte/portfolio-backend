#!/usr/bin/env bash

set -e

# Usage create-tn.sh SOURCE_FILE [DESTINATION]
[[ ! ${1} ]] && echo "Usage: create-tn.sh SOURCE_FILE [DESTINATION]" && exit 1

resolutions=(
	640
	768
	1024
	1366
	1600
	1920
)

source="${1}"
target="${2}"
if [[ ! ${target} ]]; then
	target="${source##*/}" # leave only last component of path
	target="${target%.*}"  # strip extension
fi
mkdir -p "${target}"

source="${source}[0]"

convert "${source}" -auto-orient -background white -alpha remove -alpha off -thumbnail 400x300^ -gravity center -extent 400x300 "${target}/tn.jpg"

width=$(identify -format "%[fx:w]" "${source}")

if [ "$(identify -format '%[opaque]' "${source}")" = "true" ]; then
	filetype="jpg"
else
	filetype="png"
fi

previewtxt="${target}/preview.txt"

: >"${previewtxt}" # make sure the file is empty

for resolution in "${resolutions[@]}"; do
	if [[ width -lt resolution ]]; then
		outfile="preview-${width}.${filetype}"
		convert "${source}" -auto-orient -adaptive-resize "${resolution}>" "${target}/$outfile"
		echo "${width},${outfile}" >>"${previewtxt}"
		break
	else
		outfile="preview-${resolution}.${filetype}"
		convert "${source}" -auto-orient -adaptive-resize "${resolution}" "${target}/$outfile"
		echo "${resolution},${outfile}" >>"${previewtxt}"
	fi
done

echo "Done - thumbnail is at ${target}/"
