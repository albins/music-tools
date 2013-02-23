# -*- mode: Python; encoding: utf-8; indent-tabs-mode: nil; tab-width: 2 -*-
import sys
import os

# All the module files are in the previous directory, so we need to
# add it to the Python path.
sys.path.append("..")

from db.xapian_music import search
import db.xapian_music

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
  
  # All song objects MUST at least have these keys:
  keys = ["length", "artist", "title", "mtime", "year", "album", "path"]

  for song in dt.get_songs(MUSIC_DIR):
    assert not None in song
    assert song != None
    for key in keys:
      assert key in song
      # These keys must also have real vaules:
      assert song[key] != None
        

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
  from playlist.m3u import parse

  REFERENCE_PLAYLIST = os.path.join(TESTDIR, "reference.json")
  REFERENCE_PLAYLIST_COMPILED_M3U = os.path.join(TESTDIR, "reference.m3u")
  TEST_DB = os.path.join(TESTDIR, "rhythmdb.xml")

  playlist = ts.load(REFERENCE_PLAYLIST)
  songs = rb.get_songs(TEST_DB)

  # This is som preliminary testing that the playlist is actually sane
  # (i.e. contains no missed matches and is the right size.
  matched = match.match_transport(playlist, songs)
  assert len(matched) == len(playlist['playlist'])
  assert not None in matched

  # Here we compare the matched playlist to a hand-compiled m3u list.
  compiled_playlist = parse(REFERENCE_PLAYLIST_COMPILED_M3U)
  for i in xrange(len(matched)):
    assert matched[i] == compiled_playlist[i]

# Helper function for re-indexing for every test, so we don't have to
# worry about breaking the database.
def with_index(f):
  from db.xapian_music import index
  from shutil import rmtree as remove
  
  MUSIC_DIR = os.path.join(TESTDIR, "music_dir") 
  DBPATH = os.path.join(TESTDIR, "music.db")

  index(MUSIC_DIR, DBPATH)
  
  try:
    f(DBPATH)
  finally:
    remove(DBPATH)

def test_index():
  from xapian import Database
  import json
  

  def search_vnv(db):
    vnv_nation_artist  = search(dbpath=db, querystring='artist:"VNV Nation"')
    assert len(vnv_nation_artist) == 2
    vnv_nation_plain = search(dbpath=db, querystring="VNV Nation")
    assert len(vnv_nation_plain) == 2
    assert vnv_nation_plain[0]['data']['artist'] == "VNV Nation" 

  def search_kent(db):
    kent_artist = search(dbpath=db, querystring="artist:Kent")
    assert len(kent_artist) == 1

  def search_false(db):
    false_search = search(dbpath=db, querystring="gurka")
    assert len(false_search) == 0
  
  def search_all(db):
    database = Database(db)
    try:
      # Ok, this is UGLY, and we should implement a proper interface for this.
      documents = [database.get_document(post.docid)
                   for post in database.postlist("")]
      songs = [json.loads(doc.get_data()) for doc in documents]

      print "The following songs were indexed:"
      for song in songs:
        print song['path']
      assert len(songs) == 6
      
    finally:
      database.close()

  with_index(search_vnv)
  with_index(search_kent)
  with_index(search_false)
  with_index(search_all)

def add_ebm(dbpath):
  from db.xapian_music import add_tag
  from db.xapian_music import search

  q = 'artist:"VNV Nation"'
  tag = "ebm"
  add_tag(dbpath, q, tag)
  
  for song in search(dbpath, q):
    assert tag in song['data']['tags']
    assert len(search(dbpath, q)) == len(search(dbpath, "tag:%s" % tag))

def test_add_tags():
  from db.xapian_music import add_tag
  
  with_index(add_ebm)

def test_remove_tags():
  from db.xapian_music import remove_tag
  from db.xapian_music import add_tag
  
  def remove_ebm(dbpath):
    from db.xapian_music import add_tag
    from db.xapian_music import search

    q = 'artist:"VNV Nation"'
    tag = "ebm"
    
    remove_tag(dbpath, q, tag)
    assert not search(dbpath, 'tag:ebm')
    for song in search(dbpath, q):
      assert tag not in song['data']['tags']
    
  def add_and_remove_ebm(db):
    add_ebm(db)
    remove_ebm(db)

  with_index(add_and_remove_ebm)

def test_search_album():

  def search_album(db):
    q = 'album:"Automatic"'
    songs = search(db, q)
    assert len(songs) == 1
    song_data = songs[0]['data']
    assert song_data['title'] == "Streamline"
    assert song_data['path'] == os.path.join(TESTDIR, 
                                             "music_dir/06-streamline.mp3")

  with_index(search_album)

def assert_ascending(values):
  last_value = 0

  for v in values:
    assert v >= last_value
    last_value = v
    print last_value

def test_sort_mtime():

  def sort_mtime(db):
    q = 'artist:VNV Nation'
    songs = search(db, q, order="mtime")
    mtimes = [s['data']['mtime'] for s in songs]
    assert_ascending(mtimes)

  with_index(sort_mtime)

def test_sort_year():
  
  def sort_year(db):
    q = 'artist:VNV Nation'
    songs = search(db, q, order="year")
    years = [s['data']['year'] for s in songs]

    assert_ascending(years)

  with_index(sort_year)

def test_sort_length():
  assert False

def test_sort_tracknumber():
  assert False

def test_sort_lastplayed():
  assert False

def test_search_genre():
  assert False

def test_search_year_interval():

  def search_interval_year(db):
    q_all = 'year..3000'
    q_2010 = 'year..2010'
    q_1999 = 'year..1999'
    q_early_00s = 'year1999..2004'
    songs_all = search(db, q_all)
    songs_2010 = search(db, q_2010)
    songs_1999 = search(db, q_1999)
    songs_early_00s = search(db, q_early_00s)
    assert len(songs_all) == 6
    assert len(songs_2010) == 5
    assert len(songs_1999) == 0
    assert len(songs_early_00s) == 2
    
  with_index(search_interval_year)

def test_search_rating_interval():
  assert False

def test_find_all():
  from db.xapian_music import all_songs
  from db.dirtree import get_files
  
  def test_all_songs(db):
    files = [f for f in get_files(os.path.join(TESTDIR, "music_dir"))]
    song_paths = [song['data']['path'] for song in all_songs(db)]

    # Did we get all songs?
    print song_paths
    assert len(song_paths) == len(files)

    # ...and did we get the RIGHT songs?
    for f in files:
      print f
      assert f in song_paths

  with_index(test_all_songs)
