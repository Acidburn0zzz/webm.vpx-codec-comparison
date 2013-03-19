#!/bin/bash

# Encode each .yuv file in the specified input directory to H.264 format,
# and compute the PSNR.

# Input Parameters:
#  $1=Input directory

if [ ! -d encoded_clips ]; then
  mkdir encoded_clips
  mkdir encoded_clips/h264
  mkdir encoded_clips/vp8
fi

if [ ! -d logs ]; then
  mkdir logs
  mkdir logs/h264
  mkdir logs/vp8
fi

if [ ! -d stats ]; then
  mkdir stats
  mkdir stats/h264
  mkdir stats/vp8
fi

for filename in $1/*.yuv
do
  echo "Processing ${filename}"

  # filename format: <path>/<clip_name>_<width>_<height>_<frame_rate>.yuv
  pathless=$(basename ${filename})
  clip_stem=${pathless%.*}
  part=($(echo $clip_stem | tr "_" "\n"))
  width=${part[1]}
  height=${part[2]}
  frame_rate=${part[3]}

  # Data-rate range depends on input format
  if [ ${width} -gt 640 ]; then
    rate_start=800
    rate_end=1500
    rate_step=100
  else
    rate_start=100
    rate_end=800
    rate_step=100
  fi

  for (( rate=rate_start; rate<=rate_end; rate+=rate_step ))
  do
    # Encode into ./<clip_name>_<width>_<height>_<frame_rate>_<rate>kbps.yuv
    x264 --nal-hrd cbr --vbv-maxrate ${rate} --vbv-bufsize ${rate} \
      --vbv-init 0.8 --bitrate ${rate} --fps ${frame_rate} \
      --profile baseline --no-scenecut --keyint infinite --preset veryslow \
      --input-res ${width}x${height} \
      --tune psnr \
      -o ./encoded_clips/h264/${clip_stem}_${rate}kbps.mkv ${filename} \
      2> ./logs/h264/${clip_stem}_${rate}kbps.txt

    # Decode the clip to a temporary file in order to compute PSNR and extract
    # bitrate.
    encoded_rate=( `ffmpeg -i ./encoded_clips/h264/${clip_stem}_${rate}kbps.mkv \
      temp.yuv 2>&1 | awk '/bitrate/ { print $6 }'` )

    # Compute the global PSNR.
    psnr=$(./bin/psnr ${filename} temp.yuv ${width} ${height} 9999)

    # Rename the file to reflect the encoded datarate.
    mv ./encoded_clips/h264/${clip_stem}_${rate}kbps.mkv \
      ./encoded_clips/h264/${clip_stem}_${encoded_rate}kbps.mkv

    echo "${encoded_rate} ${psnr}" >> ./stats/h264/${clip_stem}.txt

    rm -f temp.yuv
  done
done

