#!/usr/bin/python
#
# Copyright 2013 Google Inc.
# All Rights Reserved.
#
# Tweak options.
#
# Command line:
#    tweak-options.sh <bitrate> <video>
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

options = [
  Option('overshoot-pct', ['0', '15', '30', '45']),
  Option('undershoot-pct', ['0', '25', '50', '75', '100']),
  # CQ mode is not considered for end-usage at the moment.
  Option('end-usage', ['cbr', 'vbr']),
  Option('cpu-used', ['-16', '0', '16']),
  Option('min-q', ['0', '2', '4', '8', '16', '24']),
  Option('max-q', ['32', '56', '63']),
  Option('buf-sz', ['200', '500', '1000', '2000', '4000']),
  Option('buf-initial-sz', ['200', '400', '800', '1000', '2000', '4000']),
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
    else:
      print "Emitting new config ", self.dirname
      os.mkdir(self.dirname)
      with open(self.EncoderFileName(), 'w') as encoder:
        encoder.write(self.config)
      os.chmod(self.EncoderFileName(), stat.S_IXUSR | stat.S_IRUSR)
      with open(self.MeasurerFileName(), 'w') as measurerfile:
        measurerfile.write(self.measurer)
      os.chmod(self.MeasurerFileName(), stat.S_IXUSR | stat.S_IRUSR)
  def Diff(self, otherconfig):
    """ Show config differences. Assumes that words are the same. """
    print "Changes from", self.dirname, "to", otherconfig.dirname
    self.FetchEncoder()
    otherconfig.FetchEncoder()
    words1 = self.config.split()
    words2 = otherconfig.config.split()
    if len(words1) != len(words2):
      print "Lengths differ"
      return
    for i in xrange(0,len(words1)):
      if words1[i] != words2[i]:
        print words1[i], " -> ", words2[i]

def findCandidateConfigs(bitrate, videofilename):
  print "Finding candidates"
  candidates = []
  basename = os.path.splitext(os.path.basename(videofilename))[0]
  files = glob.glob('vp8/*/' + basename + '.results')
  for file in files:
    with open(file, 'r') as result:
      data = result.read()
      if re.search('target_rate=' + bitrate + '\n', data):
        candidates.append(Config(os.path.dirname(file), data))
  return candidates

def rankCandidateConfigs():
  print "Ranking candidates"
  candidates.sort(key=lambda foo: foo.Score())
  trail = None
  for candidate in candidates:
    if trail:
      trail.Diff(candidate)
    trail = candidate
    print candidate.EncoderFileName(), ': ', candidate.Score()

def emitNewConfig(candidates):
  """Tweak the last configuration (highest score) and save it."""
  candidates[-1].Tweak().Save()

# Main
candidates = findCandidateConfigs(sys.argv[1], sys.argv[2])
rankCandidateConfigs()
emitNewConfig(candidates)
