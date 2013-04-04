#!/bin/sh
# Fetch and decompress the videos for the comparision test.
#
set -e

files='
desktop_640_360_30.yuv
gipsrecmotion_1280_720_50.yuv
gipsrecstat_1280_720_50.yuv
kirland_640_480_30.yuv
macmarcomoving_640_480_30.yuv
macmarcostationary_640_480_30.yuv
niklas_1280_720_30.yuv
niklas_640_480_30.yuv
tacomanarrows_640_480_30.yuv
tacomasmallcameramovement_640_480_30.yuv
thaloundeskmtg_640_480_30.yuv
'

if which wget; then
  # Do nothing
  true
else
  echo "No wget, exiting"
  exit 1
fi

if [ ! -d video ]; then
  mkdir video
fi

cd video

for file in $files; do
  if [ ! -f $file ]; then
    # Remove earlier partial downloads.
    [ -f $file.xz ] && rm $file.xz
    wget http://downloads.webmproject.org/ietf_tests/$file.xz
    xz -d $file.xz
  else
    echo "Already have $file"
  fi
done


