#!/bin/bash
#
# Tweak a config forever, trying to get it to improve.
#
set -e

RATE=400
FILE=mpeg_video/Johnny_1280x720_60.yuv

while true; do
  ./tweak_options.py $RATE $FILE
  ./run_tests $FILE >> /tmp/encodelogfile 2>&1
done
