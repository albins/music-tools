# -*- mode: Python; encoding: utf-8; indent-tabs-mode: nil; tab-width: 2 -*-
import sys
import os

# All the module files are in the previous directory, so we need to
# add it to the Python path.
sys.path.append("..")

TESTDIR = os.path.dirname(__file__)

def test_m3u_object():
  from playlist import m3u
  playlist_name = "Test1"
  files = ["file1", "file2", "file3"]
  try:
    pls = m3u.M3UList(files, name=playlist_name)

    for i in xrange(len(files)):
      assert files[i] == pls[i]

    assert playlist_name == pls.name
  finally:
    pass

def test_m3u_parse():
  from playlist.m3u import parse, M3UList
  TEST_PLAYLIST = os.path.join(TESTDIR, "test.m3u")
  try:
    playlist = parse(TEST_PLAYLIST)
    assert type(playlist) == M3UList
    assert playlist.comments[0] == "This is a comment"
    assert playlist[0] == "/music/opeth/white cluster.mp3"
    assert playlist[3] == "/video/mononoke.avi"
    assert len(playlist) == 4
  finally:
    pass

def test_m3u_write():
  from playlist.m3u import write, M3UList, parse
  from os import remove

  TEMP_FILE = os.path.join(TESTDIR, "m3u_write_test.m3u")

  playlist = M3UList(["/music/file_1.mp3", "/music/file_2.mp3"], comments=["This is a comment", "This is another comment"])
  
  try:
    write(playlist, TEMP_FILE)
    new_playlist = parse(TEMP_FILE)
    assert playlist == new_playlist
    assert len(playlist.comments) == len(new_playlist.comments)
    assert playlist.comments[0] == new_playlist.comments[0]
    
    for comment in playlist.comments:
      assert comment in new_playlist.comments

  finally:
    remove(TEMP_FILE)
  
def test_rhythmbox_db_get_songs():
  from db import rhythmbox as rb
  TEST_DB = os.path.join(TESTDIR, "rhythmdb.xml")

  songs = rb.get_songs(TEST_DB)

  for song in songs:
    assert len(song) == 3
    assert not None in song
    assert song != None
    
def test_dirtree_db_get_songs():
  from db import dirtree as dt
  MUSIC_DIR = os.path.join(TESTDIR, "music_dir/")

  for song in dt.get_songs(MUSIC_DIR):
    assert len(song) == 4
    assert not None in song
    assert song != None

def test_parse_reference_playlist():
  from playlist import transport as ts
  from datetime import date
  REFERENCE_PLAYLIST = os.path.join(TESTDIR, "reference.json")

  playlist = ts.load(REFERENCE_PLAYLIST)
  assert ts.allowed_match("levenshtein", playlist)
  assert playlist['tags'][0] == "ebm"
  assert type(ts.updated(playlist)) == date
  assert ts.valid_playlist(playlist)

def test_playlist_creators():
  from playlist import transport as ts

  REFERENCE_PLAYLIST = os.path.join(TESTDIR, "reference.json")
  
  valid_song = ts.make_song("Test artist", 200, "Test song")
  invalid_song = {"fisk" : "sylt"}
  invalid_song2 = {"artist" : "Test_artist"}

  assert ts.valid_song(valid_song)
  assert not ts.valid_song(invalid_song)
  assert not ts.valid_song(invalid_song2)

  valid_playlist = ts.make_playlist([valid_song], 
                                 "http://test.com/test.json",
                                 "Test playlist",
                                 ["Albin Stjerna"])

  invalid_playlist = ts.make_playlist([invalid_song, invalid_song2], 
                                 "http://test.com/test.json",
                                 "Test playlist",
                                 ["Albin Stjerna"])

  assert ts.valid_playlist(valid_playlist)
  assert not ts.valid_playlist(invalid_playlist)

def test_transport_write():
  from playlist import transport as ts
  from os import remove
  
  TEMP_FILE = os.path.join(TESTDIR, "transport_write_test.json")
  REFERENCE_PLAYLIST = os.path.join(TESTDIR, "reference.json")

  playlist = ts.load(REFERENCE_PLAYLIST)
  try:
    ts.write(playlist, TEMP_FILE)
    new_playlist = ts.load(TEMP_FILE)
    assert ts.valid_playlist(new_playlist)
    assert playlist == new_playlist
  finally:
    remove(TEMP_FILE)

def test_match():
  from playlist import match
  from playlist import transport as ts
  from db import rhythmbox as rb

  REFERENCE_PLAYLIST = os.path.join(TESTDIR, "reference.json")
  TEST_DB = os.path.join(TESTDIR, "rhythmdb.xml")

  playlist = ts.load(REFERENCE_PLAYLIST)
  songs = rb.get_songs(TEST_DB)

  matched = match.match_transport(playlist, songs)
  assert len(matched) == len(playlist['playlist'])
  assert not None in matched

def test_index():
    from search import index
    from search import search
    from shutil import rmtree as remove

    MUSIC_DIR = os.path.join(TESTDIR, "music_dir") 
    DBPATH = os.path.join(TESTDIR, "music.db")

    try:
        index(datapath = MUSIC_DIR, dbpath = DBPATH)

        vnv_nation_artist  = search(dbpath=DBPATH, querystring="artist:\"VNV Nation\"")
        assert len(vnv_nation_artist) == 2
        vnv_nation_plain = search(dbpath=DBPATH, querystring="VNV Nation")
        assert len(vnv_nation_plain) == 2

        false_search = search(dbpath=DBPATH, querystring="gurka")
        assert len(false_search) == 0
    finally:
        pass
#        remove(DBPATH)  
