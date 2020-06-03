#!/usr/bin/env bash

# origin: https://gist.github.com/mrbar42/ae111731906f958b396f30906004b3fa
# modified by Philipp Mayer

set -e

# Usage create-vod-hls.sh SOURCE_FILE [OUTPUT_NAME]
[[ ! "${1}" ]] && echo "Usage: create-vod-hls.sh SOURCE_FILE [OUTPUT_NAME]" && exit 1

# comment/add lines here to control which renditions would be created
renditions=(
# resolution  bitrate  audio-rate
#  "426x240    400k    64k"
  "640x360    800k     96k"
  "842x480    1400k    128k"
  "1280x720   2800k    128k"
  "1920x1080  5000k    192k"
)

cover_filter="scale=-1:300,crop=400:300"
cover_filter_portrait="scale=400:-1,crop=400:300"

segment_target_duration=4       # try to create a new segment every X seconds
max_bitrate_ratio=1.07          # maximum accepted bitrate fluctuations
rate_monitor_buffer_ratio=1.5   # maximum buffer size between bitrate conformance checks

#########################################################################

source="${1}"
target="${2}"
if [[ ! "${target}" ]]; then
  target="${source##*/}" # leave only last component of path
  target="${target%.*}"  # strip extension
fi
mkdir -p ${target}

width_prefix='streams_stream_0_width='
height_prefix='streams_stream_0_height='
declare -a dimensions
while read -r line
do
    dimensions+=( "${line}" )
done < <( ffprobe -v error -of flat=s=_ -select_streams v:0 -show_entries stream=width,height "${source}" )
source_width_with_prefix=${dimensions[0]}
source_height_with_prefix=${dimensions[1]}
source_width=${source_width_with_prefix#${width_prefix}}
source_height=${source_height_with_prefix#${height_prefix}}

rotation=$(ffprobe -loglevel error -select_streams v:0 -show_entries stream_tags=rotate -of default=nw=1:nk=1 -i "${source}")

if [[ $rotation -eq 90 ]] || [[ $rotation -eq 270 ]] || [[ $source_width -le $source_height ]]; then
  # portrait (or square) video
  cover_filter=${cover_filter_portrait}
fi

duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${source}")
# round to second
duration=$(printf "%.0f" ${duration})

cover_time=$(($duration/20))
cover_gif_len=$(($duration < 10 ? $duration : 10))

ffmpeg -ss ${cover_time} -i ${source} -hide_banner -y -vframes 1 -filter "${cover_filter}" "${target}/cover.jpg"
ffmpeg -ss 0 -t ${cover_gif_len} -i ${source} -hide_banner -y -filter_complex "[0:v] fps=4,${cover_filter},split [a][b];[a] palettegen [p];[b][p] paletteuse" "${target}/cover.gif"

key_frames_interval="$(echo `ffprobe ${source} 2>&1 | grep -oE '[[:digit:]]+(.[[:digit:]]+)? fps' | grep -oE '[[:digit:]]+(.[[:digit:]]+)?'`*2 | bc || echo '')"
key_frames_interval=${key_frames_interval:-50}
key_frames_interval=$(echo `printf "%.1f\n" $(bc -l <<<"$key_frames_interval/10")`*10 | bc) # round
key_frames_interval=${key_frames_interval%.*} # truncate to integer

# static parameters that are similar for all renditions
static_params="-c:a aac -ar 48000 -c:v h264 -profile:v main -crf 20 -sc_threshold 0"
static_params+=" -g ${key_frames_interval} -keyint_min ${key_frames_interval} -hls_time ${segment_target_duration}"
static_params+=" -hls_playlist_type vod"

# misc params
misc_params="-hide_banner -y"

master_playlist="#EXTM3U
#EXT-X-VERSION:3
"
cmd=""
for rendition in "${renditions[@]}"; do
  # drop extraneous spaces
  rendition="${rendition/[[:space:]]+/ }"

  # rendition fields
  resolution="$(echo ${rendition} | cut -d ' ' -f 1)"
  bitrate="$(echo ${rendition} | cut -d ' ' -f 2)"
  audiorate="$(echo ${rendition} | cut -d ' ' -f 3)"

  # calculated fields
  if [[ $rotation -eq 90 ]] || [[ $rotation -eq 270 ]]; then
    # portrait video
    height="$(echo ${resolution} | grep -oE '^[[:digit:]]+')"
    width="$(echo ${resolution} | grep -oE '[[:digit:]]+$')"
    compare_width=${source_height}
    compare_height=${source_width}
  else
    width="$(echo ${resolution} | grep -oE '^[[:digit:]]+')"
    height="$(echo ${resolution} | grep -oE '[[:digit:]]+$')"
    compare_width=${source_width}
    compare_height=${source_height}
  fi
  maxrate="$(echo "`echo ${bitrate} | grep -oE '[[:digit:]]+'`*${max_bitrate_ratio}" | bc)"
  bufsize="$(echo "`echo ${bitrate} | grep -oE '[[:digit:]]+'`*${rate_monitor_buffer_ratio}" | bc)"
  bandwidth="$(echo ${bitrate} | grep -oE '[[:digit:]]+')000"
  name="${height}p"

  # do not upscale, but ensure there is at least one version
  if { [[ "${height}" -le "${compare_height}" ]] && [[ "${width}" -le "${compare_width}" ]]; } || [[ "$cmd" -eq "" ]] ; then
    cmd+=" ${static_params} -vf scale=w=${width}:h=${height}:force_original_aspect_ratio=decrease,crop=floor(iw/2)*2:floor(ih/2)*2"
    cmd+=" -b:v ${bitrate} -maxrate ${maxrate%.*}k -bufsize ${bufsize%.*}k -b:a ${audiorate}"
    cmd+=" -hls_segment_filename ${target}/${name}_%03d.ts ${target}/${name}.m3u8"

    # add rendition entry in the master playlist
    master_playlist+="#EXT-X-STREAM-INF:BANDWIDTH=${bandwidth},RESOLUTION=${resolution}\n${name}.m3u8\n"
  fi

done

# start conversion
echo -e "Executing command:\nffmpeg ${misc_params} -i ${source} ${cmd}"
ffmpeg ${misc_params} -i ${source} ${cmd}

# create master playlist file
echo -e "${master_playlist}" > ${target}/playlist.m3u8

echo "Done - encoded HLS is at ${target}/"
