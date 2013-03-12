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
  if [ ${width} -gt 640 ]; then
    rate=1000
  else
    rate=600
  fi
  for mode in -16 -15 -14 -13 -12 -11 -10 -9 -8 -7 -6 -5 -4 -3 -2 -1
  do

    # Encode into ./encoded_clips/vp8/${clip_stem}_${mode}.webm
    static_thresh=1
    if (( ${mode} < -10 )); then
      let static_thresh=1000
    fi
    encode_time=` { time \
      ./bin/vpxenc --lag-in-frames=0 --target-bitrate=${rate} --kf-min-dist=3000 \
      --kf-max-dist=3000 -t 1 --cpu-used=${mode} --fps=${frame_rate}/1 \
      --static-thresh=${static_thresh} \
      --token-parts=1 --drop-frame=0 --end-usage=cbr --min-q=2 --max-q=56 \
      --undershoot-pct=100 --overshoot-pct=15 --buf-sz=1000 -q \
      --buf-initial-sz=5000 --buf-optimal-sz=600 --max-intra-rate=1200 \
      --resize-allowed=0 --drop-frame=0 --passes=1 --rt --noise-sensitivity=0 \
      -w ${width} -h ${height} ${filename} --codec=vp8 \
      -o ./encoded_clips/vp8/${clip_stem}_${mode}.webm \
      &>./logs/vp8/${clip_stem}_${mode}.txt;} 2>&1 | \
      awk '/real/ { minutes = gensub(/m.*/, "", "g", $2); \
                    seconds = gensub(/.*m/, "", "g", $2); \
                    print minutes*60+seconds }'`

    # Decode the clip to a temporary file in order to compute PSNR and extract
    # bitrate.
    encoded_rate=( `ffmpeg -i ./encoded_clips/vp8/${clip_stem}_${mode}.webm \
      temp.yuv 2>&1 | awk '/bitrate/ { print $6 }'` )

    # Compute the global PSNR.
    psnr=$(./bin/psnr ${filename} temp.yuv ${width} ${height} 9999)

    # Rename the file to reflect the encoded datarate.
    mv ./encoded_clips/vp8/${clip_stem}_${mode}.webm \
      ./encoded_clips/vp8/${clip_stem}_${mode}_${encoded_rate}.webm

    echo "${encode_time} ${psnr} ${encoded_rate}" >> \
      ./stats/vp8/${clip_stem}_encode_speed.txt

    rm -f temp.yuv
  done
done

