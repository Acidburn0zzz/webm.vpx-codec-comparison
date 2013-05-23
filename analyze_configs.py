#!/usr/bin/python
#
# Copyright 2013 Google Inc.
# All Rights Reserved.
#
# Analyze configs for a given test suite, and show what matters.
#7
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

  candidates = tweak_options.findConfigsWithResult(args[0], args[1])
  if len(candidates) == 0:
    print >> sys.stderr, "No candidates found\n"
    return 1

  candidates.sort(key=lambda foo: foo.Score())

  best_candidate = candidates[-1]
  best_candidate.FetchEncoder()
  print len(candidates), "configurations tried"
  print 'Best score: ', best_candidate.Score(), "for", best_candidate.dirname
  print "-----------------"
  print best_candidate.config
  print "-----------------"
  print best_candidate.results
  print "-----------------"
  # Show single-parameter changes and their effects.
  multiparams = 0
  print len(candidates), " candidates"
  for candidate in candidates[::-1]:
    delta = best_candidate.Score() - candidate.Score()
    diff = best_candidate.Diff(candidate)
    if len(diff) > 1:
      multiparams += 1
    elif len(diff) == 0:
      # It's the optimal config. Ignore.
      pass
    elif delta == 0.0:
      print "No effect: ", diff
    else:
      print "Effect", delta, ":", diff
  print multiparams, "multi-parameter changes not listed"

if __name__ == '__main__':
  sys.exit(main())
