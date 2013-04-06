#!/bin/sh
#
# Run all tests, with timing info.
# This script will take about 4 hours to run.
# Timing notes are on a Dell 3500.
#
echo "H.264 quality tests"
# About half an hour real time, 2 hours CPU time on a Dell T3500
time ./run_h264_tests.sh video
echo "VP8 quality tests"
time ./run_vp8_tests.sh video
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
echo "PSNR bitrate improvement"
./core_data.sh 0
echo "Encode speed improvement"
./core_data.sh encode_speed
