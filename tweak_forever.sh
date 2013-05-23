#!/bin/bash
#
# Tweak a config forever, trying to get it to improve.
#
set -e

RATE=${1-1600}
#FILE=mpeg_video/PeopleOnStreet_2560x1600_30_crop.yuv
FILE=mpeg_video/Traffic_2560x1600_30_crop.yuv

while true; do
  for config in $(./select_tests.py $RATE $FILE | head -5); do
    echo "./run_one_test $config $FILE"
    ./run_one_test $config $FILE >> /tmp/encodelogfile 2>&1
  done
  ./tweak_options.py $RATE $FILE
done
