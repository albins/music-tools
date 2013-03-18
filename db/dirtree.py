# -*- mode: Python; encoding: utf-8; indent-tabs-mode: nil; tab-width: 2 -*-

# FIXME: standardise naming conventions for functions.
import codecs
from mutagen.flac import FLAC
import mutagen
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from mutagen.oggvorbis import OggVorbis
from os import walk
from os.path import join as pathjoin
from os.path import getmtime
import time


class FileFormatError(Exception):
  "Thrown when an unsupported file type was passed."
  pass


class SongData(dict):
    """Basically a dictionary with authorised keys."""
    def __init__(self, *args, **kwargs):
        self.mtime = kwargs['mtime']
        self.genre = kwargs['genre']
        self.lastplayed = kwargs['lastplayed']
        self.rating = kwargs['rating']
        self.length = kwargs['length']
        self.artist = kwargs['artist']
        self.title  = kwargs['title']
        self.year = kwargs['year']
        self.tracknumber = kwargs['tracknumber']
        self.album = kwargs['album']
        self.path = kwargs['path']
        dict.__init__(self, *args, **kwargs)


def read_metadata_from_file(af):
  extension = af.split(".")[-1]
  if extension == "flac":
    return FLAC(af)
  elif extension == "ogg":
    return OggVorbis(af)
  elif extension == "mp3":
    return MP3(af, ID3=EasyID3)
  else:
    raise FileFormatError("File type %s not supported for file: %s." % (extension, af))

def get_files(p):
  for dirpath, _, files in walk(p):
    for f in files:
      # fixme: find out the actual encoding of the file system
      yield unicode(pathjoin(dirpath, f), encoding="utf-8")

def parseFile(filePath):
    "Parse a data file and return something that can be used later on."

    # FIXME: return some kind of pre-defined object. Using a hashmap
    # for this is just silly.
    mtime = time.ctime(getmtime(filePath))
    metadata = read_metadata_from_file(filePath)
    genre = metadata.get("genre", [None])[0]
    lastplayed = None
    rating = metadata.get("rating:banshee", [None])[0]
    length = int(metadata.info.length)
    artist = unicode(metadata["artist"][0])
    title  = unicode(metadata["title"][0])
    year = metadata["date"][0]
    track = metadata.get("tracknumber", [0])[0]
    try:
        tracknumber = int(track)
    except ValueError:
        # Handle those ugly "1/10" track number formats
        tracknumber = int(str(track).split("/")[0])
    album = unicode(metadata["album"][0])

    return SongData(length=length,
                    artist=artist,
                    title=title,
                    mtime=mtime,
                    year=year,
                    album=album,
                    path=filePath,
                    tracknumber=tracknumber,
                    tags=["index"],
                    lastplayed=lastplayed,
                    rating=rating,
                    genre=genre)

def get_songs(tree, prefilter=None, postfilter=None):
    """Generator that returns a dictionary of metadata for a number of songs in that directory tree."""

    for fl in get_files(tree):
      mtime = time.ctime(getmtime(fl))

      if prefilter:
        if not prefilter(fl, mtime):
          continue

      try:
          data = parseFile(fl)
      except FileFormatError as e:
        continue
      except mutagen.flac.FLACNoHeaderError:
        continue

      if postfilter:
        if not postfilter(data):
          continue

      yield data
