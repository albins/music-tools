#!/usr/bin/env python
# -*- mode: Python; encoding: utf-8; indent-tabs-mode: nil; tab-width: 2 -*-
# This is a reference playlist decompiler.
import os
import sys
from playlist import transport as ts
from playlist import m3u
from db import dirtree as dt

def main(args):
    if len(args) != 2:
        sys.stderr.write("Usage: pldc <playlist file>.\n")
        sys.exit()
    
    playlist = m3u.parse(args[1])
    
    def mangle_song(s):
        ("Read the metadata from the song in path s, "
         "and mangle it to a valid line for the songs "
         "part of a transport playlist.")

        md = dt.read_metadata_from_file(s)
        return ts.make_song(artist=md['artist'][0],
                            length=md.info.length,
                            title=md['title'][0],
                            album=md.get("album", None)[0])
        

    songs = map(mangle_song, playlist)

    # fixme: these and other options should be provided at command line:
    transport = ts.make_playlist(songs, 
                                 "http://test.example.com/pls",
                                 "description")
    ts.write(transport, sys.stdout)
    
    

if __name__ == "__main__":
    main(sys.argv)
