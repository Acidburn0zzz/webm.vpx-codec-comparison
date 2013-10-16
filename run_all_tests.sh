#!/bin/sh
#
# Run all tests, with timing info.
#
# Argument: "speed" or "quality", and codec name for running only
# one set of codecs.
#
# This script will take about 4 hours to run with no arguments.
# Timing notes are on a Dell 3500.
#
COMMAND=$1
CODEC=$2

if [ "$COMMAND" == "" -o "$COMMAND" == "quality" ]; then
  if [ "$CODEC" == "" -o "$CODEC" == "h264" ]; then
    echo "H.264 quality tests"
    # About half an hour real time, 2 hours CPU time on a Dell T3500
    time ./run_h264_tests.sh video
  fi
  if [ "$CODEC" == "" -o "$CODEC" == "vp8" ]; then
    echo "VP8 quality tests"
    time ./run_vp8_tests.sh video
  fi
  echo "Drawing graphs"
  # 2 seconds
  ./draw_graphs.sh
  echo "PSNR bitrate improvement"
  ./core_data.sh 0
fi

if [ "$COMMAND" == "" -o "$COMMAND" == "speed" ]; then
  # About 2 hours
  echo "H.264 speed tests"
  # About 45 minutes
  time ./run_h264_speed_tests.sh video
  echo "VP8 speed tests"
  # About half an hour
  time ./run_vp8_speed_tests.sh video
  echo "Drawing graphs"
  # 2 seconds
  ./draw_graphs.sh
  echo "Encode speed improvement"
  ./core_data.sh encode_speed
fi

