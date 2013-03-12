timings_vp8=( `./decoder_timing.sh "encoded_clips/vp8/*kbps.webm" 2>&1  | awk '/real/ { a=gensub(/m.*/,"","g",$2) ; b=gensub(/.*m/,"","g",$2); print a*60+b }'` )
timings_264=( `./decoder_timing.sh "encoded_clips/h264/*kbps.mkv" 2>&1  | awk '/real/ { a=gensub(/m.*/,"","g",$2) ; b=gensub(/.*m/,"","g",$2); print a*60+b }'` )
stats_file="vp8vsh264-decodetime.txt"

echo Threads   H264 Time / VP8 Time > $stats_file
for (( i=0;i<${#timings_vp8[@]};i++ ))
do
  time_ratio=`echo ${timings_264[$i]} / ${timings_vp8[$i]} | bc -l`
  echo $((i + 1 ))         $time_ratio  >> $stats_file
done
echo  >> $stats_file
echo  >> $stats_file
echo Every video produced in the quality tests is decoded both for vp8 and h264 using  >> $stats_file
echo ffmpeg. The total time spent decoding all the files is measured for both vp8 and  >> $stats_file
echo h264 and above is the ratio of time spent decoding h264/time spent decoding vp8.  >> $stats_file
echo A number of greater than 1 means that h264 took longer to decode than vp8.  This  >> $stats_file
echo was run once for each thread count 1 to 8. >> $stats_file
