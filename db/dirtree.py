# -*- mode: Python; encoding: utf-8; indent-tabs-mode: nil; tab-width: 2 -*-

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

def get_songs(tree, prefilter=None, postfilter=None):
    """Generator that returns a dictionary of metadata for a number of songs in that directory tree."""

    for fl in get_files(tree):
      mtime = time.ctime(getmtime(fl))

      if prefilter:
        if not prefilter(fl, mtime):
          continue

      try:
        metadata = read_metadata_from_file(fl)
      except FileFormatError as e:        
        continue
      except mutagen.flac.FLACNoHeaderError:
        continue
        
      try:
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
      except KeyError as e:
        #print "W: No metadata field \"%s\" in file %s" % (e[0], fl)
        continue
        
      if postfilter:
        if not postfilter(fl, mtime, length, artist, title, year, album, tracknumber):
          continue

      yield {"length" : length,
             "artist" : artist,
             "title"  : title,
             "mtime"  : mtime,
             "year"   : year,
             "album"  : album,
             "path"   : fl,
             "tracknumber" : tracknumber,
             "tags"   : ["index"],
             "lastplayed" : lastplayed,
             "rating" : rating,
             "genre" : genre
             
             # investigate which other metadata posts we should include.
             #"mdata"  : metadata
      }

      
