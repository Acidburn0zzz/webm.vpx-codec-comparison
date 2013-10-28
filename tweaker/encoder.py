"""Encoder and related classes.

This file contains classes that generically define the idea of a codec,
an encoder, an option and so forth.

A codec is a generic mechanism for processing an .yuv file and returning
a score. Given a set of options, a file and a rate, it can produce an encoder.
The codec has a set of options that can have varying values.

An encoder is a codec with a given set of options.

An encoding is an encoder applied to a given filename and target bitrate. 

A variant is an encoder with at least one option changed.
"""

import ast
import glob
import md5
import os
import random
import re
import sys


class Error(Exception):
  pass


class Option(object):
  """This class represents an option given to an encoder.

  Typically the command line representation is "--name=value".
  This class provides functions to modify an option in a command line string.
  """
  def __init__(self, name, values):
    assert(len(values) > 1)
    self.name = name
    self.values = frozenset(values)

  def PickAnother(self, not_this):
    """Find a new value for the option, different from not_this.
    not_this doesn't have to be a member of the values list, but can be.
    """
    rest = list(self.values - set([not_this]))
    return rest[random.randint(0, len(rest) - 1)]

  def OptionString(self, value):
    return '--%s=%s' % (self.name, value)

  def _ChangedOption(self, matchobj):
    return self.OptionString(self.PickAnother(matchobj.group(1)))

  def RandomlyPatchConfig(self, config):
    """ Modify a configuration by changing the value of this parameter."""
    newconfig = re.sub(r'--%s=(\S+)' % self.name,  self._ChangedOption,
                       config)
    assert(config != newconfig)
    return newconfig


class ChoiceOption(Option):
  """This class represents a set of exclusive options (without values).

  One example is the --good, --best option to vpxenc.
  """
  def __init__(self, flags):
     self.values = frozenset(flags)

  def OptionString(self, value):
    return '--%s' % value

  def RandomlyPatchConfig(self, config):
    """ Modify a configuration by replacing the instance of this option."""
    current_flags = set([flag[2:] for flag in config.split()
                         if flag.startswith('--')])
    these_flags = current_flags & self.values
    if len(these_flags) == 0:
      raise Error('No choice option alternative given')
    if len(these_flags) > 1:
      raise Error('Mutually exclusive option alternatives given')
    current_flag = these_flags.pop()
    next_flag = self.PickAnother(current_flag)
    newconfig = re.sub(r'--%s\b' % current_flag,
                       '--%s' % next_flag, config)
    assert(config != newconfig)
    return newconfig


class Videofile(object):
  def __init__(self, filename):
    """ Parse the file name to find width, height and framerate. """
    self.filename = filename
    m = re.search(r'_(\d+)x(\d+)_(\d+)', filename)
    if m:
      self.width = int(m.group(1))
      self.height = int(m.group(2))
      self.framerate = int(m.group(3))
    else:
      m = re.search(r'_(\d+)_(\d+)_(\d+).yuv$', filename)
      if m:
        self.width = int(m.group(1))
        self.height = int(m.group(2))
        self.framerate = int(m.group(3))
      else:
        raise Error("Unable to parse filename " + filename)
    self.basename = os.path.splitext(os.path.basename(filename))[0]


class Codec(object):
  """Abstract class representing a codec.

  Subclasses must define the name, options and start_encoder variables
  """
  def __init__(self, cache=None):
    if cache:
      self.cache = cache
    else:
      self.cache = EncodingDiskCache(self)

  def AllScoredEncodings(self, bitrate, videofile):
    return self.cache.AllScoredEncodings(bitrate, videofile)

  def BestEncoding(self, bitrate, videofile):
    encodings = self.AllScoredEncodings(bitrate, videofile)
    if not encodings.Empty():
      return encodings.BestEncoding()
    else:
      return self.start_encoder.Encoding(bitrate, videofile)

  def Execute(self, parameters, bitrate, videofile, workdir):
    raise Error("The base codec class can't execute anything")

  def RandomlyChangeConfig(self, parameters):
    option_to_change = self.options[random.randint(0, len(self.options)-1)]
    return option_to_change.RandomlyPatchConfig(parameters)

  def ScoreResult(self, bitrate, result):
    raise NotImplementedError

class Encoder(object):
  """This class represents a codec with a specific set of parameters.
  It makes sense to talk about "this encoder produces quality X".
  """
  def __init__(self, codec, parameters=None, filename=None):
    """Parameters:
    codec - a Codec object
    parameters - a string
    filename - a string, passed to the cache for fetching the parameters
    It makes sense to give either the parameters or the filename.
    """
    self.codec = codec
    self.parameters = parameters
    self.stored = False
    if parameters is None:
      if filename is None:
        raise Error("Encoder with neither parameters nor filename")
      else:
        self.parameters = self.codec.cache.ReadEncoderParameters(filename)
        if self.Hashname() != filename:
          raise Error("Filename contains wrong arguments")

  def Encoding(self, bitrate, videofile):
    return Encoding(self, bitrate, videofile)

  def Execute(self, bitrate, videofile, workdir):
    return self.codec.Execute(self.parameters, bitrate, videofile, workdir)

  def Store(self):
    self.codec.cache.StoreEncoder(self)

  def Hashname(self):
    m = md5.new()
    m.update(self.parameters)
    hashname = m.hexdigest()[:12]
    return hashname


class Encoding(object):
  """The encoding represents the result of applying a specific encoder
  to a specific videofile with a specific target bitrate.
  """
  def __init__(self, encoder, bitrate, videofile):
    """Arguments:
    encoder - an Encoder
    bitrate - a number
    videofile - a Videofile
    """
    self.encoder = encoder
    self.bitrate = bitrate
    self.videofile = videofile
    self.result = None

  def SomeUntriedVariants(self):
    """Returns some variant encodings that have not been tried.

    If no such variant can be found, returns an empty EncodingSet.
    """
    result = EncodingSet(())
    variant_encoder = Encoder(
      self.encoder.codec,
      self.encoder.codec.RandomlyChangeConfig(self.encoder.parameters))
    variant_encoding = Encoding(variant_encoder, self.bitrate, self.videofile)
    variant_encoding.Recover()
    if variant_encoding.Score():
      return EncodingSet([])
    else:
      return EncodingSet([variant_encoding])

  def Workdir(self):
    workdir = (self.encoder.codec.name + '/' + self.encoder.Hashname()
               + '/' + str(self.bitrate))
    # TODO(hta): Make this storage subsys dependent.
    if not os.path.isdir(workdir):
      os.makedirs(workdir)
    return workdir

  def Execute(self):
    self.result = self.encoder.Execute(self.bitrate, self.videofile,
                                       self.Workdir())
    return self

  def Score(self):
    return self.encoder.codec.ScoreResult(self.bitrate, self.result)

  def Store(self):
    self.encoder.Store()
    self.encoder.codec.cache.StoreEncoding(self)

  def Recover(self):
    self.encoder.codec.cache.ReadEncodingResult(self)

  @staticmethod
  def FromFile(self, encoder, bitrate, videofile, filename):
    encoding = Encoding(encoder, bitrate, videofile)
    encoding.Recover()
    return encoding


class EncodingSet(object):
  def __init__(self, encodings):
    self.encodings = encodings

  def Empty(self):
    return len(self.encodings) == 0

  def BestEncoding(self):
    if self.encodings:
      return max(self.encodings, key=lambda e: e.Score())
    return None

  def BestGuess(self):
    for encoding in self.encodings:
      if not encoding.Score():
        return encoding


class EncodingDiskCache(object):
  """Encoder and encoding information, saved to disk."""
  def __init__(self, codec):
    self.codec = codec
    if not os.path.isdir(codec.name):
      os.mkdir(codec.name)

  def AllScoredEncodings(self, bitrate, videofile):
    candidates = []
    videofilename = videofile.filename
    basename = os.path.splitext(os.path.basename(videofilename))[0]
    pattern = (self.codec.name + '/*/' + bitrate +
                      '/' + basename + '.result')
    files = glob.glob(pattern)
    for file in files:
      filename = os.path.dirname(file)  # Cut off resultfile
      filename = os.path.dirname(filename)  # Cut off bitrate dir
      filename = os.path.basename(filename)  # Cut off leading codec name
      encoder = Encoder(self.codec, filename=filename)
      candidate = Encoding(encoder, bitrate, videofile)
      candidate.Recover()
      candidates.append(candidate)
    return EncodingSet(candidates)

  def StoreEncoder(self, encoder):
    """Stores an encoder object on disk.

    An encoder object consists of a parameter set.
    Its name is the first 12 bytes of the SHA-1 of its string
    representation."""
    if encoder.stored:
      return
    dirname = self.codec.name + '/' + encoder.Hashname()
    if not os.path.isdir(dirname):
      os.mkdir(dirname)
    with open(dirname + '/parameters', 'w') as parameterfile:
      parameterfile.write(encoder.parameters)
    encoder.stored = True

  def ReadEncoderParameters(self, hashname):
    dirname = self.codec.name + '/' + hashname
    with open(dirname + '/parameters', 'r') as parameterfile:
      return parameterfile.read()

  def StoreEncoding(self, encoding):
    """Stores an encoding object on disk.

    An encoding object consists of its result (if executed).
    The bitrate is encoded as a directory, the videofilename
    is encoded as part of the output filename.
    """
    dirname = '%s/%s/%s' % (self.codec.name, encoding.encoder.Hashname(),
                            str(encoding.bitrate))
    if not os.path.isdir(dirname):
      os.mkdir(dirname)
    if not encoding.result:
      return
    videoname = encoding.videofile.basename
    with open('%s/%s.result' % (dirname, videoname), 'w') as resultfile:
      resultfile.write(str(encoding.result))

  def ReadEncodingResult(self, encoding):
    """Reads an encoding result back from storage, if present.

    Encoder is unchanged if file does not exist."""
    dirname = ('%s/%s/%s' % (self.codec.name, encoding.encoder.Hashname(),
                             str(encoding.bitrate)))
    filename = '%s/%s.result' % (dirname, encoding.videofile.basename)
    if os.path.isfile(filename):
      with open(filename, 'r') as resultfile:
        stringbuffer = resultfile.read()
        encoding.result = ast.literal_eval(stringbuffer)


class EncodingMemoryCache(object):
  """Encoder and encoding information, in-memory only. For testing."""
  def __init__(self, codec):
    self.codec = codec
    self.encoders = {}
    self.encodings = []

  def AllScoredEncodings(self, bitrate, videofile):
    result = []
    for encoding in self.encodings:
      if (bitrate == encoding.bitrate and
          videofile == encoding.videofile and
          encoding.Score()):
        result.append(encoding)
    return EncodingSet(result)

  def StoreEncoder(self, encoder):
    self.encoders[encoder.Hashname()] = encoder

  def ReadEncoderParameters(self, filename):
    if filename in self.encoders:
      return self.encoders[filename].parameters
    return None

  def StoreEncoding(self, encoding):
    self.encodings.append(encoding)

      
