# -*- mode: Python; encoding: utf-8; indent-tabs-mode: nil; tab-width: 2 -*-

import codecs
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from mutagen.oggvorbis import OggVorbis
from os import walk
from os.path  import join as pathjoin
from json import dumps

def read_metadata_from_file(af):
  extension = af.split(".")[-1]
  if extension == "flac":
    return FLAC(af)
  elif extension == "ogg":
    return OggVorbis(af)
  elif extension == "mp3":
    return MP3(af, ID3=EasyID3)
  else:
    raise Exception("File type %s not supported for file: %s." % (extension, af))


def get_songs(tree):
    """Generator that returns a dictionary of metadata for a number of songs in that directory tree."""

    def get_files(p):
        for dirpath, _, files in walk(p):
            for f in files:
                yield pathjoin(dirpath, f)

    for fl in get_files(tree):
        try:
            metadata = read_metadata_from_file(fl)
        except Exception as e:        
            continue
        
        try:
            length = int(metadata.info.length)
            artist = metadata["artist"][0]
            title  = metadata["title"][0]
            mtime = 0
            year = 0
            album = ""
        except KeyError as e:
            print "W: No metadata field \"%s\" in file %s" % (e[0], fl)
            continue

        yield {"length" : length,
               "artist" : artist,
               "title"  : title,
               "mtime"  : mtime,
               "year"   : year,
               "album"  : album,
               "path"   : fl,
               "mdata"  : metadata}

      
