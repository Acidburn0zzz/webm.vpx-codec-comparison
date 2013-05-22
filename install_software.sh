#!/bin/sh
#
# Install required software to run the tests.
#
set -e

[ -d bin ] || mkdir bin

sudo apt-get install ffmpeg
sudo apt-get install x264
sudo apt-get install python
sudo apt-get install python-numpy
# Reqiurements for compiling libvpx
sudo apt-get install yasm

# Build the vpxenc and vpxdec binaries
if [ ! -d libvpx ]; then
  git clone http://git.chromium.org/webm/libvpx.git
fi
cd libvpx
# Ensure we check out exactly a consistent version.
git checkout master
git checkout c129203f7e5e20f5d67f92c27c65f7d5e362aa7a
./configure
# There's something wrong in the make for libvpx at this version.
# Ignore the result code from make. We'll bail if vpxenc and vpxdec
# were not built.
make || echo "Something went wrong building libvpx, continuing"
cp vpxenc ../bin/
cp vpxdec ../bin/
cd ..

# Build the x264 binary
if [ ! -d x264 ]; then
  git clone git://git.videolan.org/x264.git
fi
cd x264
git checkout 198a7ea
./configure
make x264
cp x264 ../bin/
cd ..

# Build the ffmpeg binary
if [ ! -d ffmpeg ]; then
  git clone git://source.ffmpeg.org/ffmpeg.git ffmpeg
fi
cd ffmpeg
git checkout ae04493
./configure
make ffmpeg
cp ffmpeg ../bin/
cd ..

# Build the psnr binary
gcc -o bin/psnr src/psnr.c -lm


