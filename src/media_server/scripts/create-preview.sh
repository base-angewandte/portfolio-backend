#!/usr/bin/env bash

set -e

# Usage create-preview.sh SOURCE_FILE [DESTINATION]
[[ ! ${2} ]] && echo "Usage: create-preview.sh HOST SOURCE_FILE [DESTINATION]" && exit 1

host="${1}"
source="${2}"
target="${3}"
if [[ ! ${target} ]]; then
	target="${source##*/}" # leave only last component of path
	target="${target%.*}"  # strip extension
fi
mkdir -p "${target}"

if [[ $(head -c 4 "${source}") == "%PDF" ]]; then
	cp "${source}" "${target}/preview.pdf"
else
	filename="${source##*/}"
	extension="${filename##*.}"
	tmpfile="${target}/preview_tmp.${extension}"
	cp "${source}" "${tmpfile}"
	curl -F "data=@${tmpfile}" "${host}/lool/convert-to/pdf" >"${target}/preview.pdf"
	rm "${tmpfile}"
fi

convert -density 270 -resize 20% -alpha remove "${target}/preview.pdf[0]" "${target}/preview.jpg"

echo "Done - preview is at ${target}/"
