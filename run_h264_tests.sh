#!/bin/bash

# Encode each .yuv file in the specified input directory to H.264 format,
# and compute the PSNR.

# Input Parameters:
#  $1=Input directory

tempyuvfile=$(mktemp ./tempXXXXX.yuv)

if [ ! -d "$1" ]; then
  echo "No such directory: $1"
  exit 1
fi

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

  # Reset previous run data
  rm -f ./stats/h264/${clip_stem}.txt

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
    echo "Encoding for $rate"
    # Encode into ./<clip_name>_<width>_<height>_<frame_rate>_<rate>kbps.yuv
    ./bin/x264 \
      --vbv-bufsize ${rate} \
      --bitrate ${rate} --fps ${frame_rate} \
      --threads 1 \
      --profile baseline --no-scenecut --keyint infinite --preset veryslow \
      --input-res ${width}x${height} \
      --tune psnr \
      -o ./encoded_clips/h264/${clip_stem}_${rate}kbps.mkv ${filename} \
      2> ./logs/h264/${clip_stem}_${rate}kbps.txt

    # Decode the clip to a temporary file in order to compute PSNR and extract
    # bitrate.
    rm -f $tempyuvfile
    encoded_rate=( `bin/ffmpeg -i ./encoded_clips/h264/${clip_stem}_${rate}kbps.mkv \
      $tempyuvfile 2>&1 | awk '/bitrate:/ { print $6 }'` )
    if expr $encoded_rate + 0 > /dev/null; then
      # Compute the global PSNR.
      psnr=$(./bin/psnr ${filename} $tempyuvfile ${width} ${height} 9999)

      if [ $rate -ne $encoded_rate ]; then
        # Rename the file to reflect the encoded datarate.
        mv ./encoded_clips/h264/${clip_stem}_${rate}kbps.mkv \
          ./encoded_clips/h264/${clip_stem}_${encoded_rate}kbps.mkv
      fi
      echo "${encoded_rate} ${psnr}" >> ./stats/h264/${clip_stem}.txt
    else
      echo "Non-numeric bitrate $encoded_rate"
      exit 1
    fi

    rm -f $tempyuvfile
  done
done

