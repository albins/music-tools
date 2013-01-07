#!/usr/bin/env python
# -*- mode: Python; encoding: utf-8; indent-tabs-mode: nil; tab-width: 2 -*-
# This is a reference playlist compiler.
import time
import os
import sys
from playlist import transport as ts
from playlist import m3u
from playlist.match import match_transport
from db import rhythmbox as rb
from db import dirtree

# This /really/ must be handled better:
MUSIC_DIR = "/var/storage/Musik/"
RB_DB = '/home/albin/.local/share/rhythmbox/rhythmdb.xml'
CURRENT_DIR = os.path.dirname(__file__)

if len(sys.argv) > 1 and not len(sys.argv) > 2:
  playlist = ts.load(sys.argv[1])
else:
  sys.stderr.write("Usage: plc <playlist file> <optional output file>. If no output file is given, print to stdout.\n")
  sys.exit()

start_time = time.time()

songs = match_transport(playlist, rb.get_songs(RB_DB))

for i in xrange(len(songs)):
  if songs[i] == None:
    sys.stderr.write("E: couldn't find %d: %s by %s.\n" % ((i+1), playlist["playlist"][i]["title"], playlist["playlist"][i]["artist"]))

m3u_list = m3u.M3UList(songs, name=playlist['description'], comments=[playlist['comment']])

target = sys.stdout

if len(sys.argv) > 2:
  target = sys.argv[2]

m3u.write(m3u_list, target)

sys.stderr.write("N: Finished matching in %f seconds.\n" % (time.time() - start_time))


