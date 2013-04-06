#!/bin/sh
# Extremely hacky way to extract a number from the stats
# without changing scripts.
# "Metric" is the string 0 for quality, encode_speed for encoding speed.
METRIC=${1-0}

cat > tmp_core_data.template <<EOF
//%%filestable_avg%%//
EOF

cat > tmp_core_data.py <<EOF
filestable_avg=[{}, {}]
EOF

./visual_metrics.py tmp_core_data.template "*$METRIC.txt" \
   stats/h264 stats/vp8 >> tmp_core_data.py
cat >> tmp_core_data.py <<EOF
print filestable_avg[1]['rows'][-1]['c'][1]['v']
EOF

python tmp_core_data.py

