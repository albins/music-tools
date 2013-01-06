#!/usr/bin/env python
# -*- mode: Python; encoding: utf-8; indent-tabs-mode: nil; tab-width: 2 -*-
# This is a reference playlist compiler.
from json import load
import codecs

from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from mutagen.oggvorbis import OggVorbis
from os import walk
from os.path  import join as pathjoin

from Levenshtein import ratio
import time
from lxml import etree
from urllib2 import unquote

# This /really/ must be handled better:
MUSIC_DIR = "/var/storage/Musik/"

RB_DB = '/home/albin/.local/share/rhythmbox/rhythmdb.xml'

ACCEPTABLE_TIME_DIFFERENCE = 2

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

def levenshtein_ok(fl, ls):
  fl_artist, fl_title = fl
  ls_artist, ls_title = ls


  title_closeness = ratio(fl_title, ls_title)

  # TODO We should really examine these fields and see which are most unique.
  # We should also examine various threshold values
  if title_closeness > 0.80:
    artist_closeness = ratio(fl_artist, ls_artist)
    if artist_closeness > 0.80:
      print "N: Found match with artist closeness %f, title closeness %f" % (artist_closeness, title_closeness)
      return True
    else:
      return False
  
def match_songs_walk(playlist, music_dir):
  # This is so we can catch any files that aren't found.  This makes an
  # array of the same size as the playlist, containing "None".  This
  # way, we can keep track of our progress.

  # Of course, the order's the same, so found_songs[i] ==
  # playlist['playlist'][i], though of course not literally.
  found_songs = [None]*len(playlist["playlist"])

  # Collect all files here, then do something with them:
  #print "Collecting files"
  music_files = []
  for dirpath, _, files in walk(MUSIC_DIR):
    for f in files:
      music_files.append(pathjoin(dirpath, f))
      #print "Finished collecting files"

  # FIXME This is a good place for some opportunism: if we can somehow sieve out files from their path/file names in music_files, a lot can be gained.

  for fl in music_files:
    if not None in found_songs:
      # We've already found all songs!
          break
    try:
      metadata = read_metadata_from_file(fl)
    except Exception as e:        
      #    print e
      continue
          
    # We've happily found our metadata, let's see if it matches.
    if "levenshtein" in playlist["allow_match"]:
      # Ok, using simple levenshtein matching
      try:
        length = int(metadata.info.length)
        artist = metadata["artist"][0]
        title  = metadata["title"][0]
      except KeyError as e:
        print "W: No metadata field \"%s\" in file %s" % (e[0], fl)
        continue
      
      for i in xrange(len(playlist["playlist"])):
        if found_songs[i] != None:
          # Already found song
          continue
                  
        song = playlist["playlist"][i]
            
        # filter out songs with wrong duration for a first test:
        if abs(length - song["length"]) > ACCEPTABLE_TIME_DIFFERENCE:
          continue
          
        if levenshtein_ok((artist, title), (song['artist'], song['title'])):
          print "File %s matches the song %s by %s" % (fl, song['title'], song['artist'])
          found_songs[i] = fl
          break
  
    else:
        # There was no supported matching method supplied.
        print "E: no supported matching method supplied in file."
        return list()
  
  return found_songs

def match_songs_rb_db(pls, db):
    found_songs = [None]*len(playlist["playlist"])
    
    tree = etree.parse(db)
    root = tree.getroot()

    for element in root:
      if element.get("type") == 'song':
        song = element
      else:
        continue

      # print title, artist, location
      if not None in found_songs:
        # We've already found all songs!
        break
        
      if "levenshtein" in playlist["allow_match"]:
        # do simple levenshtein matching
        # look for "title" and "artist"
        title = None
        artist = None
        location = None

        for attr in song:
          if attr.tag == 'title':
            title = unicode(attr.text)
          elif attr.tag == 'artist':
            artist = unicode(attr.text)
          elif attr.tag == 'location':
            #location=unicode(attr.text)
            location = unicode(unquote(attr.text[7:]), encoding="utf-8")

#        try:
#          metadata = read_metadata_from_file(location)
#        except Exception:
#          continue
        
 #       length = int(metadata.info.length)

        for i in xrange(len(playlist["playlist"])):
          if found_songs[i] != None:
            # Already found song
            continue

          pls_song = playlist["playlist"][i]
            

#          if abs(length - pls_song["length"]) > ACCEPTABLE_TIME_DIFFERENCE:
#            continue
            
          # we'd like to check length of song here, but we can't without parsing it. :(
          # ...and that's hideously slow.
          if levenshtein_ok((artist, title), (pls_song['artist'], pls_song['title'])):
            print "File %s matches the song %s by %s" % (location, pls_song['title'], pls_song['artist'])
            found_songs[i] = location
            break
        
    return found_songs
            
with codecs.open("reference.json", encoding="utf-8") as reffile:
  playlist = load(reffile)

start_time = time.time()
# songs = match_songs_walk(playlist, MUSIC_DIR) # this takes about 57 seconds.

with codecs.open('a.out.m3u', 'wb', encoding='utf-8') as pls:
  songs = match_songs_rb_db(playlist, RB_DB) # this takes about 5 seconds
  for i in xrange(len(songs)):
    if songs[i] == None:
      print "E: couldn't find %d: %s by %s." % ((i+1), playlist["playlist"][i]["title"], playlist["playlist"][i]["artist"])
    else:
      pls.write(u"%s\n" % songs[i])
    
  
print "N: Finished matching in %f seconds" % (time.time() - start_time)

# with codecs.open('a.out.pls', 'wb', encoding='utf-8') as pls:
#   pls.write(u'[playlist]\n')
#   pls.write(u'NumberOfEntries=%d' % len(songs))
#   for i in xrange(len(songs)):
#     pls.write('File%d=%s\n' % ((i + 1), songs[i]))

#with codecs.open('a.out.pls', 'wb', encoding='utf-8') as pls:
