#!/usr/bin/python
# -*- mode: Python; encoding: utf-8; indent-tabs-mode: nil; tab-width: 2 -*-

import xapian
from db.dirtree import get_songs
import db.dirtree as dt
import json
import os
import time
#import hashlib
import logging

# a mapping of query term/aliases → xapian prefixes.
# most of these are also keys to the song[] dict.
# Prefixes from http://xapian.org/docs/omega/termprefixes.html
PREFIXES = {'artist' : 'A',
            'title' : 'S',
            'path' : 'U',
            'genre' : 'XGENRE',
            'album' : 'XALBUM'}

# These numeric prefixes will also be used as data slots.
NUMERIC_PREFIXES = ['year', 'mtime', 'lastplayed',
                    'tracknumber', 'rating', 'length']


class SongMatch(dict):
    def __init__(self, **kwargs):
        self.data = dt.SongData(**kwargs['data'])
        self.id = kwargs['id']
        self.rank = kwargs['rank']
        self.percent = kwargs['percent']

        setDict = {'data' : self.data, 'id' : self.id,
                   'rank' : self.rank, 'percent' : self.percent}
        dict.__init__(self, **setDict)


def addSong(db, songData):
    """Add a song with songData to the xapian WritableDatabase
    db. Performs no double-checking to see if file already exists, and
    will overwrite data mercilessly."""
    doc = xapian.Document()

    # Set up a TermGenerator that we'll use in indexing.
    termGenerator = xapian.TermGenerator()
    termGenerator.set_stemmer(xapian.Stem("en"))
    termGenerator.set_document(doc)

    # Index each field with a suitable prefix.
    for term in PREFIXES:
        termGenerator.index_text(unicode(songData[term]),
                                 1, PREFIXES[term])

    # Index fields without prefixes for general search.
    for term in PREFIXES:
        termGenerator.index_text(unicode(songData[term]))
        termGenerator.increase_termpos()

    for data_slot, term in enumerate(NUMERIC_PREFIXES):
        if songData[term]:
            doc.add_value(data_slot, make_value(songData[term], term))


    # Store all the fields for display purposes.
    doc.set_data(unicode(json.dumps(songData)))

    # We use the identifier to ensure each object ends up in the
    # database only once no matter how many times we run the
    # indexer.

    idterm = "P" + songData.path
    # previous solution:
    # hashlib.sha256(songData.path).hexdigest()
    doc.add_boolean_term(idterm)
    db.replace_document(idterm, doc)

def mergeSongs(songA, songB):
    """Will merge the two song data sets. Data fields existing in any
    of the songs will be kept in the final product. Left fields will
    be preferred if duplicates exist."""
    mergedSong = dict()
    for key in songA:
        if songA[key]:
            # this would seem silly, but handles empty strings etc.
            if songB[key]:
                logging.warning("Throwing away %s value %s in merge"
                       % (key, songB[key]))
            mergedSong[key] = songA[key]
        elif songB[key]:
            # This catches the case where there was an empty string
            # at the key, but where songB has something.
            mergedSong[key] = songB[key]

    for key in songB:
        if key not in mergedSong or not mergedSong[key]:
            mergedSong[key] = songB[key]

    return dt.SongData(**mergedSong)

def pathInDB(db, path):
    """Returns True if a song with path exists in the xapian database
    db, False otherwise."""
    enquire = xapian.Enquire(db)
    enquire.set_query(parse_query("path:" + path))
    enquire.set_docid_order(enquire.DONT_CARE)
    return bool(enquire.get_mset(0, db.get_doccount()))

def make_value(s, term):
    """Parse various string values and return suitable numeric
    representations."""
    if term == 'year':
        # This is in a date string format due to serialization.
        return xapian.sortable_serialise(int(s))
    if term == 'mtime':
        return xapian.sortable_serialise(time.mktime(time.strptime(s)))
    if term == 'rating':
        return xapian.sortable_serialise(float(s))
    else:
        return xapian.sortable_serialise(int(s))

def index(datapath, dbpath):
    """Create or update the index stored in database <dbpath>, using
    the music file/directory structure in <datapath>."""
    # Create or open the database we're going to be writing to.
    db = xapian.WritableDatabase(dbpath, xapian.DB_CREATE_OR_OPEN)

    # Make sure all songs in the directory are in the database.
    for filePath in dt.get_files(datapath):
        if not pathInDB(db, filePath):
            addSong(db, dt.parseFile(filePath))
        else:
            mtimeFile = os.path.getmtime(filePath)
            dbEntry = search(dbpath, "path:" + filePath)[0]
            mtimeDB = time.mktime(time.strptime(dbEntry['data']['mtime']))
            if mtimeFile > mtimeDB:
                logging.warning("File %s has changed." % filePath)
                addSong(db, mergeSongs(dbEntry['data'], dt.parseFile(filePath)))
            else:
                logging.info("File %s hasn't changed." % filePath)

    # Now, make sure no songs have disappeared.
    songFiles = dt.get_files(datapath)
    for song in all_songs(dbpath):
        songPath = song['data']['path']
        if not songPath in songFiles:
            logging.warning("Song file %s has disappeared!" % songPath)
            # do some voodoo to delete the entry here.

def parse_query(q):
    """Parse the query <q> and return a query ready for use with
    enquire.set_query()."""

    # Set up a QueryParser with a stemmer and suitable prefixes
    queryparser = xapian.QueryParser()
    queryparser.set_stemmer(xapian.Stem("en"))
    queryparser.set_stemming_strategy(queryparser.STEM_SOME)

    queryparser.add_boolean_prefix("tag", "K")

    for term in PREFIXES:
        queryparser.add_prefix(term, PREFIXES[term])

    for data_slot, term in enumerate(NUMERIC_PREFIXES):
        queryparser.add_valuerangeprocessor(
            xapian.NumberValueRangeProcessor(data_slot, term, True)
        )

    # And parse the query
    return queryparser.parse_query(q)

def query(dbpath, querystring, order=None):
    """Query the database at path <dbpath> with the string
    <querystring>. Return iterator over maches. This is mostly for
    internal use, as it returns xapian match objects. Optionally takes
    the argument order with valid values None or any numeric term."""

    # Open the database we're going to search.
    db = xapian.Database(dbpath)

    # Use an Enquire object on the database to run the query
    enquire = xapian.Enquire(db)
    enquire.set_query(parse_query(querystring))

    # Don't care about document ID order, just optimize.
    enquire.set_docid_order(enquire.DONT_CARE)

    if order in NUMERIC_PREFIXES:
        slot_id = NUMERIC_PREFIXES.index(order)
        enquire.set_sort_by_value_then_relevance(slot_id, False)

    for match in enquire.get_mset(0, db.get_doccount()):
        yield match

def search(dbpath, querystring, order=None):
    """Search the database at dbpath with querystring. Return list of
    SongMatch object."""

    return [SongMatch(id=match.docid, rank=(match.rank + 1),
                      percent=match.percent,
                      data=(json.loads(unicode(match.document.get_data()))))
            for match in query(dbpath, querystring, order)]

def parseTags(tagString):
    """Parse the tags in tagString, returning a tuple of tags to add
    and to remove."""

    remove = []
    add = []
    for tag in tagString.split():
        if tag[:1] == "-":
            remove.append(tag[1:])
        else:
            add.append(tag)
    return add, remove

def tag(dbPath, queryString, tagString):
    "Add and remove tags (in one transaction) to the db att dbPath."

    addTags, removeTags = parseTags(tagString)
    # This is a list of touples with document ID and Document objects
    # to modify.
    docsModify = []

    try:
        db = xapian.WritableDatabase(dbPath, xapian.DB_CREATE_OR_OPEN)
        # We open the database this early because it will lock the
        # database for writing, making sure our fetched documents
        # doesn't change during the processing, making us overwrite
        # changes at the last step.

        # It is the responsibility of the client/higher level
        # interface to handle queuing of database writes.
        for match in query(dbPath, queryString):
            doc = match.document
            data = json.loads(doc.get_data())
            # Remove the tags to remove:
            newTags = filter(lambda t: not t in removeTags, data['tags'])
            #...and add the tags to add:
            newTags = newTags + addTags
            data['tags'] = newTags
        
            for tag in removeTags:
                doc.remove_term('K' + tag.lower())
            for tag in addTags:
                doc.add_boolean_term('K' + tag.lower())

            doc.set_data(unicode(json.dumps(data)))
            docsModify.append((match.docid, doc))

        # This is done finally to avoid half-completed
        # transactions. Either all documents matching the search
        # should be given all the specified tags, or none.
        for docId, doc in docsModify:
            db.replace_document(docId, doc)
    finally:
        db.close()

def add_tag(dbpath, querystring, addTag):
    "Add the tag <tag> to all songs matching <querystring>."
    tag(dbpath, querystring, unicode(addTag))

def remove_tag(dbpath, querystring, removeTag):
    """Remove the tag <tag> (if existing) from all entries in the
    database at dbpath matching querystring."""
    tag(dbpath, querystring, unicode("-" + removeTag))

def all_songs(dbpath):
    "Iterator over all songs stored in the database <dbpath>."
    db = xapian.Database(dbpath)

    documents = (db.get_document(post.docid)
                   for post in db.postlist(""))

    return ({'id' : doc.get_docid(), 'data' : json.loads(doc.get_data())}
             for doc in documents)
