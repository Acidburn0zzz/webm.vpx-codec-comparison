# time directory
for threads in 1 2 3 4 5 6 7 8
do
  time for i in $1; do ffmpeg -threads $threads -y -i $i -c:v rawvideo -f null - 2> /dev/null ;done
done
