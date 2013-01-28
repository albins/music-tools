# -*- mode: Python; encoding: utf-8; indent-tabs-mode: nil; tab-width: 2 -*-
from json import load as load_json
from json import dump as dump_json
from datetime import date
from time import time
import codecs

def load(fn):
    "Load a playlist with the given file name."
    with codecs.open(fn, encoding="utf-8") as reffile:
        return load_json(reffile)

def allowed_match(key, pl):
    """Returns True if the given descriptor key is an accepted
    matching method in the given transport playlist."""
    return key in pl['allow_match']

def updated(playlist):
    "Returns a date object of when the playlist was created."
    return date.fromtimestamp(float(playlist['updated']))

def valid_song(s):
    "Returns true for a valid song dictionary, false otherwise."
    try:
        return len(s['artist']) > 0 \
            and len(s['title']) > 0 \
            and int(s['length']) > 0
    except KeyError:
        return False

def valid_playlist(pl):
    "Returns true for a valid playlist, false otherwise."
    try:
        return len(pl['playlist']) > 0 \
            and len(pl['uri']) > 0 \
            and len(pl['description']) > 0 \
            and len(pl['allow_match']) > 0 \
            and not False in map(valid_song, pl['playlist'])
    except KeyError:
        return False

def make_playlist(playlist, uri, description,
                  creators=[], tags=[], allow_match=["levenshtein"], 
                  repository=None, comment=""):
    "Helper function to make a new playlist."
    return {'description' : description,
            'creators'    : creators,
            'repository'  : repository,
            'uri'         : uri,
            'updated'     : time(),
            'allow_match' : allow_match,
            'comment'     : comment,
            'tags'        : tags,
            'playlist'    : playlist}

def make_song(artist, length, title, album=None):
    "Helper function to make a post for a song."
    if not album == None:
        return {'artist'    : artist,
                'length'    : length,
                'title'     : title,
                'album'     : album}
    else:
        return {'artist'    : artist,
                'length'    : length,
                'title'     : title}

def write(pl, fn):
    "Write a playlist dictionary to file."
    assert valid_playlist(pl)
    if not type(fn) == file:
        plf = codecs.open(fn, 'wb', encoding="utf-8")
    else:
        writer = codecs.getwriter("utf8")
        plf = writer(fn)
    try:
        dump_json(pl, plf)
    finally:
        plf.close()
        
