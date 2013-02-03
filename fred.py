#!/usr/bin/python
# -*- mode: Python; encoding: utf-8; indent-tabs-mode: nil; tab-width: 2 -*-

# Fred: a xapian-backed music search utility.
import sys
import os
import time
from db import xapian_music as db

CURRENT_DIR = os.path.dirname(__file__)
DBPATH = os.path.join(CURRENT_DIR, "music.db")
#MUSIC_DIR = os.path.join(CURRENT_DIR, "test/music_dir")
MUSIC_DIR = "/var/storage/Musik/"

def main(args):
    start_time = time.time()
    
    db.index(datapath = MUSIC_DIR, dbpath = DBPATH)
    
    #db.tag(dbpath=DBPATH, querystring=" ".join(args[1:]), tags=["inbox", "fisk"])
    
    matches = db.search(dbpath=DBPATH, querystring=" ".join(args[1:]))
    for match in matches:
        print u"{tracknumber} {artist} – »{title}« from {album} {year} ({length} s). Last modified {mtime}. Tagged {tags}.".format(**match['data'])
    print "N: Found %i tracks in  in %f ms.\n" % (len(matches), (time.time() - start_time)*1000)
    

if __name__ == "__main__":
    main(sys.argv)
