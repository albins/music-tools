# -*- mode: Python; encoding: utf-8; indent-tabs-mode: nil; tab-width: 2 -*-
from playlist import transport as ts
from Levenshtein import ratio

def levenshtein_ok(fl_title, fl_artist, ls_artist, ls_title):

    title_closeness = ratio(fl_title, ls_title)

    # TODO We should really examine these fields and see which are most unique.
    # We should also examine various threshold values
    if title_closeness > 0.80:
        artist_closeness = ratio(fl_artist, ls_artist)
        if artist_closeness > 0.80:
            return True
        else:
            return False


def match_transport(pl, songs):
    """Return a playlist with matches (search paths) for transport
    playlist pl in the song collection songs."""

    found_songs = [None]*len(pl["playlist"])

    if not ts.valid_playlist(pl):
        raise Exception("Invalid playlist format!")
        return []

    if not ts.allowed_match("levenshtein", pl):
        raise Exception("Playlist requires unsupported match method!")
        return []

    for song in songs:
        title, artist, location = song

        if not None in found_songs:
            # We've already found all songs!
            break
        
        
        for i in xrange(len(pl["playlist"])):
            if found_songs[i] != None:
                # Already found song
                continue
            
            pls_song = pl["playlist"][i]
            if levenshtein_ok(fl_title=title, fl_artist=artist,
                              ls_artist=pls_song["artist"],
                              ls_title=pls_song["title"]):
                found_songs[i] = location
                break

    return found_songs
            
            
            
        
