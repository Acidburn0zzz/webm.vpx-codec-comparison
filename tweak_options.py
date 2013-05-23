#!/usr/bin/python
#
# Copyright 2013 Google Inc.
# All Rights Reserved.
#
# Tweak options.
#
# Command line:
#    tweak-options.py [--options] <bitrate> <video>
#
# Algorithm:
# - Find runs with good performance for this bitrate and video
# - Create configs that are like this, but novel.
#
__author__ = "hta@google.com (Harald Alvestrand)"

import glob
import md5
import os
import random
import re
import stat
import sys

from optparse import OptionParser

class Option(object):
  def __init__(self, name, values):
    self.name = name
    self.values = values

  def PickAnother(self, not_this):
    index = random.randint(0, len(self.values)-1)
    if self.values[index] == not_this:
      return self.values[(index + 1) % len(self.values)]
    return self.values[index]

  def OptionString(self, value):
    return '--' + self.name + '=' + value

  def ChangedOption(self, matchval):
    print "ChangedOption called on ", matchval.group(1)
    result = self.OptionString(self.PickAnother(matchval.group(1)))
    print "Returning", result
    return result

  def PatchConfig(self, config):
    """ Modify a configuration by changing the value of this parameter."""
    newconfig = re.sub('--' + self.name + '=' + '(\S+)',  self.ChangedOption,
                       config)
    assert(config != newconfig)
    return newconfig

class ChoiceOption(Option):
  def __init__(self, flags):
     self.values = flags

  def PatchConfig(self, config):
    """ Modify a configuration by replacing the instance of this option."""
    current_flag = ''
    for flag in self.values:
      if config.find(' --' + flag + ' ') >= 0:
        current_flag = flag
        break
    if current_flag == '':
      raise Exception('No choice option alternative given')
    next_flag = self.PickAnother(current_flag)
    print "Changing from", current_flag, "to", next_flag
    newconfig = re.sub('--' + current_flag + ' ',
                       '--' + next_flag + ' ', config)
    assert(config != newconfig)
    return newconfig

options = [
  Option('overshoot-pct', ['0', '15', '30', '45']),
  Option('undershoot-pct', ['0', '25', '50', '75', '100']),
  # CQ mode is not considered for end-usage at the moment.
  Option('end-usage', ['cbr', 'vbr']),
  # End-usage cq doesn't really make sense unless we also set q to something
  # between min and max. This is being checked.
  # Option('end-usage', ['cbr', 'vbr', 'cq']),
  Option('end-usage', ['cbr', 'vbr']),
  Option('cpu-used', ['-16', '0', '16']),
  Option('min-q', ['0', '2', '4', '8', '16', '24']),
  Option('max-q', ['32', '56', '63']),
  Option('buf-sz', ['200', '500', '1000', '2000', '4000', '8000', '16000']),
  Option('buf-initial-sz', ['200', '400', '800', '1000', '2000', '4000', '8000', '16000']),
  Option('max-intra-rate', ['100', '200', '400', '600', '800', '1200']),
  Option('resize-allowed', ['0', '1']),
  Option('lag-in-frames', ['0', '1', '2', '4', '8']),
  ChoiceOption(['good', 'best', 'rt']),
]

class Config(object):

  def __init__(self, dirname, results=''):
    self.dirname = dirname
    self.results = results
    # These 2 values are read when needed.
    self.config = ''
    self.measurer = ''

  def EncoderFileName(self):
    return self.dirname + '/encoder'

  def MeasurerFileName(self):
    return self.dirname + '/measurer'

  def Score(self):
    """Computes the "quality" of the encoding.

    This function should be changed to fit the purpose of the experiment;
    this version works well for finding the best PSNR encoding below
    some bandwidth bound.
    """
    if self.results == '':
      return 0.0
    m = re.match(r'target_rate=(\d+)\nencoded_rate=(\d+)\npsnr=([\d\.]+)',
                 self.results)
    if m:
      target_rate = int(m.group(1))
      encoded_rate = int(m.group(2))
      psnr=float(m.group(3))
      score = psnr
      # Penalize by 0.1 dB per 1 kbits/sec overshoot.
      # TODO(hta): Consider whether this should be adjusted based on old runs.
      if target_rate < encoded_rate:
        score = score - (encoded_rate - target_rate) * 0.1
      return score

  def FetchEncoder(self):
    if self.config == '':
      with open(self.EncoderFileName()) as encoder:
        self.config = encoder.read()

  def Tweak(self):
    """Returns a Config object that's a tweaked version of this object."""
    self.FetchEncoder()
    with open(self.MeasurerFileName()) as measurerfile:
        self.measurer = measurerfile.read()
    newconfig = options[random.randint(0, len(options)-1)].PatchConfig(self.config)
    m = md5.new()
    m.update(newconfig)
    hashname = m.hexdigest()[:12]
    newconf = Config('vp8/' + hashname)
    newconf.config = newconfig
    newconf.measurer = self.measurer
    return newconf

  def Save(self):
    if os.path.isdir(self.dirname):
      print "Config ", self.dirname, " already exists"
      return False
    else:
      print "Emitting new config ", self.dirname
      os.mkdir(self.dirname)
      with open(self.EncoderFileName(), 'w') as encoder:
        encoder.write(self.config)
      os.chmod(self.EncoderFileName(), stat.S_IXUSR | stat.S_IRUSR)
      with open(self.MeasurerFileName(), 'w') as measurerfile:
        measurerfile.write(self.measurer)
      os.chmod(self.MeasurerFileName(), stat.S_IXUSR | stat.S_IRUSR)
      return True

  def Diff(self, otherconfig):
    """ Show config differences. Assumes that words are the same. """
    self.FetchEncoder()
    otherconfig.FetchEncoder()
    words1 = self.config.split()
    words2 = otherconfig.config.split()
    if len(words1) != len(words2):
      return ['Different lengths']
    difflist = []
    for i in xrange(0,len(words1)):
      if words1[i] != words2[i]:
        difflist.append(words1[i] + " -> " + words2[i])
    return difflist

  def AllSingleHopTweaks(self):
    """ Return all configs that differ by a single config change. """
    configs = []
    for option in options:
      for alternative in option.names:
        # do something intelligent
        pass
        
    return configs

def findConfigsWithResult(bitrate, videofilename):
  candidates = []
  basename = os.path.splitext(os.path.basename(videofilename))[0]
  files = glob.glob('vp8/*/' + basename + '.results')
  for file in files:
    with open(file, 'r') as result:
      data = result.read()
      if re.search('target_rate=' + bitrate + '\n', data):
        candidates.append(Config(os.path.dirname(file), data))
  return candidates

def findMatchingConfigs(bitrate):
  candidates = []
  files = glob.glob('vp8/*/' + 'measurer')
  for file in files:
    with open(file, 'r') as result:
      data = result.read()
      if re.search('target_rate=' + bitrate + '\n', data):
        candidates.append(Config(os.path.dirname(file), data))
  return candidates

def rankCandidateConfigs(candidates):
  print "Ranking candidates"
  candidates.sort(key=lambda foo: foo.Score())
  trail = None
  if len(candidates) > 1:
    trail = candidates[-2]
    candidate = candidates[-1]
    print "Changes from", trail.dirname, "to", candidate.dirname
    print '\n'.join(trail.Diff(candidate))
    print candidate.EncoderFileName(), ': ', candidate.Score()

def emitNewConfig(candidates):
  """Tweak the last configuration (highest score) and save it."""
  for i in xrange(10):
    # Since the tweaks are random, and may return a previously tried
    # configuration, try a few times.
    for i in xrange(10):
      if candidates[-1].Tweak().Save():
        return True
    # If there are equivalent candidates, try varying another one.
    if (len(candidates) > 1 and
        candidates[-1].Score() == candidates[-2].Score()):
      candidates.pop()
      print "Skipping to configuration", candidates[-1].dirname
    else:
      return False
  return False

def main():
  parser = OptionParser()
  parser.add_option("--foo", action="store_true", dest="foo")

  (cmdline_options, args) = parser.parse_args()

  print "Finding candidates"
  candidates = findConfigsWithResult(args[0], args[1])
  if len(candidates) == 0:
    print >> sys.stderr, "No candidates found"
    return 1
  rankCandidateConfigs(candidates)
  if emitNewConfig(candidates):
    return 0
  print >> sys.stderr, "Unable to change configuration"
  return 1

if __name__ == '__main__':
  sys.exit(main())
