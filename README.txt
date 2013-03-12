Comparing VP8 & H.264 Constrained Baseline Profile

8th March, 2013

Objective:

To compare the typical performance of VP8 and H.264 in a real-time scenario.

Methodology:

We gathered a small set of test clips containing content that is
representative of that found in a typical video-conferencing application
scenario. We encoded each of these clips into both the VP8 and H.264
(Constrained Baseline Profile) formats over a range of data rates, using
the following versions of the vpxenc and x264 encoding applications,
respectively:

vp8:  Git Commit-Id: c129203f7e5e20f5d67f92c27c65f7d5e362aa7a
x264: Version: 0.128.2216 198a7ea

Directory Structure:

The script files can be downloaded using the following link:
http://downloads.webmproject.org/ietf_tests/vp8_to_h264.tar.xz
and reflated with the command:
tar -x --xz -f vp8_vs_h264.tar.xz

Once unpacked the files are arranged in the following directory structure:
./                           // Script files.
./bin                        // Executables.
./src                        // Source code for the PSNR application.

The test video files can be individually downloaded using the following links:
http://downloads.webmproject.org/ietf_tests/desktop_640_360_30.yuv.xz
http://downloads.webmproject.org/ietf_tests/gipsrecmotion_1280_720_50.yuv.xz
http://downloads.webmproject.org/ietf_tests/gipsrecstat_1280_720_50.yuv.xz
http://downloads.webmproject.org/ietf_tests/kirland_640_480_30.yuv.xz
http://downloads.webmproject.org/ietf_tests/macmarcomoving_640_480_30.yuv.xz
http://downloads.webmproject.org/ietf_tests/macmarcostationary_640_480_30.yuv.xz
http://downloads.webmproject.org/ietf_tests/niklas_1280_720_30.yuv.xz
http://downloads.webmproject.org/ietf_tests/niklas_640_480_30.yuv.xz
http://downloads.webmproject.org/ietf_tests/tacomanarrows_640_480_30.yuv.xz
http://downloads.webmproject.org/ietf_tests/tacomasmallcameramovement_640_480_30.yuv.xz
http://downloads.webmproject.org/ietf_tests/thaloundeskmtg_640_480_30.yuv.xz

Each must be reflated using the command:
xz -d <filename>.xz
(The .xz file will be removed automatically)

The YUV format video files, once extracted, should be placed in the
./video directory (which must first be created).

The following directories are created during the execution of the scripts:
./logs                       // Output logs for:
    ./logs/vp8               //    -VP8 runs,
    ./logs/h264              //    -H264 runs.
./encoded_clips              // Encoded output files for:
    ./encoded_clips/vp8      //     -VP8 runs,
    ./encoded_clips/h264     //     -H264 runs.
./stats                      // Data-rate, PSNR, decode and encode time values for:
    ./stats/vp8              //     -VP8 runs,
    ./stats/h264             //     -H264 runs.

Requirements:

These scripts assume that the following software is installed on the host
machine:

* ffmpeg (http://ffmpeg.org/).
* x264 (http://www.videolan.org/developers/x264.html).
* python (required to run draw_graphs.sh).
* vpxenc & vpxdec (built from source found at http://www.webmproject.org/).

The VP8 encoder (vpxenc) and decoder (vpxdec) must be built and copied to
the ./bin directory. The VP8 configuration command line should be:

./configure

In addition, the psnr utility needs to be built from ./src/psnr.c (requires
the math library "-lm") and copied into the ./bin directory.

gcc -o bin/psnr src/psnr.c -lm

Running the Quality Tests:

To run the VP8 tests:
$ sh  run_vp8_tests.sh  video
For each test video, an output log is produced in the logs/vp8 directory
and the compressed clip is stored in encoded_clips/vp8. A file containing
the summarised (data-rate, psnr) values at each data-rate for each video
is stored in stats/vp8.

To run the H264 tests:
$ sh  run_h264_tests.sh  video
For each test video, an output log is produced in the logs/h264 directory
and the compressed clip is stored in encoded_clips/h264. A file containing
the summarised (data-rate, psnr) values at each data-rate for each video
is stored in stats/h264.

Running the Encode Speed Tests

To run the VP8 tests:
$ sh run_vp8_speed_tests.sh video
For each test video, an output log is produced in the logs/vp8 directory
and the compressed clip is stored in encoded_clips/vp8. A file containing
the summarised (time to encode , psnr) values at each data-rate for each
video is stored in stats/vp8.

To run the H264 tests:
$ sh run_h264_speed_tests.sh video
For each test video, an output log is produced in the logs/vp8 directory
and the compressed clip is stored in encoded_clips/h264. A file containing
the summarised (time to encode, psnr) values at each data-rate for each
video is stored in stats/h264.

To produce the rate distortion curves as an HTML file:
(Assumes that the other scripts have already been run)
$ sh draw_graphs.sh

This script employs a modified version of the “WebM Contributors Guide” to
create 2 files “vp8_vs_h264_quality.html” that presents the resulting RD-curves
in graphical form and "vp8_vs_h264_speed.html" that graphs time to encode versus
quality. Once loaded into a browser the user can examine the curves for each test
video and also see the difference between VP8 & H.264 expressed as a percentage.
For vp8_vs_h264_quality.html the figure represents the increased (+ve) or
decreased (-ve) number of bits required by H.264 Constrained Baseline Profile to
achieve the same quality as VP8, expressed as the percentage of the size of the
VP8 compressed file. Thus, +10% would mean that H.264 requires, on average, 10%
more bits than VP8 to achieve the same quality (measured in terms of
overall/global PSNR). For vp8_vs_h264_speed.html the figure represents the
amount of time needed for vp8 to match x264 quality.

Note: Source file psnr.c is provided in the bin directory for reference (this
is exactly the same PSNR algorithm implemented in VP8).

Running the Decode Speed Tests

./time_decodes.sh

This calculates the aggregate time to decode all of the files that have been
encoded in encoded_clips/vp8 and the aggregate time to decode all of the files
that have been encoded in encoded_clips/h264. The decodes are run with a thread
count set from 1 to 8 and the results are stored in the file
vp8vsh264-decodetime.txt.

