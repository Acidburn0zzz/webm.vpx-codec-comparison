#!/usr/bin/python
#
# Copyright 2013 Google Inc.
# All Rights Reserved.
#
# Select tests for a given bitrate.
# Arguments: bitrate, video file
#
import tweak_options
import sys
import os

from optparse import OptionParser

def main():
  parser = OptionParser()
  parser.add_option("--foo", action="store_true", dest="foo")

  (cmdline_options, args) = parser.parse_args()

  candidates = tweak_options.findMatchingConfigs(args[0])
  if len(candidates) == 0:
    print >> sys.stderr, "No candidates found\n"
    return 1
  
  # Only show dirs without this result if videoname is present.
  if len(args) > 1:
    video_basename = os.path.splitext(os.path.basename(args[1]))[0]
    for candidate in candidates:
      if not os.path.isfile(candidate.dirname + '/'
                            + video_basename + '.results'):
        print candidate.dirname
  else:
    for candidate in candidates:
      print candidate.dirname
  return 0

if __name__ == '__main__':
  sys.exit(main())
