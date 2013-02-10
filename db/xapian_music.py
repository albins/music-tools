#!/usr/bin/python
# -*- mode: Python; encoding: utf-8; indent-tabs-mode: nil; tab-width: 2 -*-

import xapian
from db.dirtree import get_songs
import json
import os

# a mapping of query term/aliases → xapian prefixes.
# most of these are also keys to the song[] dict.
# Prefixes from http://xapian.org/docs/omega/termprefixes.html
PREFIXES = {'artist' : 'A',
            'title' : 'S',
            'year' : 'Y',
            'path' : 'U',
            'album' : 'XALBUM',
            'mtime' : 'XMTIME',
            'title' : 'XTITLE',
            'tracknumber' : 'XTRACKNR'}

NUMERIC_PREFIXES = {}

# Use slot #1 for tags
#XAPIAN_TAGS = 1

def index(datapath, dbpath):
    # Create or open the database we're going to be writing to.
    db = xapian.WritableDatabase(dbpath, xapian.DB_CREATE_OR_OPEN)

    # Set up a TermGenerator that we'll use in indexing.
    termgenerator = xapian.TermGenerator()
    termgenerator.set_stemmer(xapian.Stem("en"))

    for song in get_songs(datapath):
        # We make a document and tell the term generator to use this.
        doc = xapian.Document()
        termgenerator.set_document(doc)

        # Index each field with a suitable prefix.
        for term in PREFIXES:
            termgenerator.index_text(unicode(song[term]), 1, PREFIXES[term])

        # Index fields without prefixes for general search.
        for pos, term in enumerate(PREFIXES):
            termgenerator.index_text(unicode(song[term]))
            #if pos < len(term):
            termgenerator.increase_termpos()

        # Store all the fields for display purposes.
        doc.set_data(unicode(json.dumps(song)))

        # use doc.add_term(str.join(K, "my tag"), 0) to add tags the way notmuch does

        # We use the identifier to ensure each object ends up in the
        # database only once no matter how many times we run the
        # indexer.

        # Using relative paths to the data root to get slightly
        # shorter arguments.

        # In the future, we might need to handle this better, see this
        # FAQ: http://trac.xapian.org/wiki/FAQ/UniqueIds
        idterm = "Q" + os.path.relpath(song['path'], datapath)
        doc.add_boolean_term(idterm)
        db.replace_document(idterm, doc)

def search(dbpath, querystring):
    # offset - defines starting point within result set
    # pagesize - defines number of records to retrieve

    # Open the database we're going to search.
    db = xapian.Database(dbpath)

    # Set up a QueryParser with a stemmer and suitable prefixes
    queryparser = xapian.QueryParser()
    queryparser.set_stemmer(xapian.Stem("en"))
    queryparser.set_stemming_strategy(queryparser.STEM_SOME)

    queryparser.add_boolean_prefix("tag", "K")
    
    for term in PREFIXES:
        queryparser.add_prefix(term, PREFIXES[term])


    # And parse the query
    query = queryparser.parse_query(querystring)

    # Use an Enquire object on the database to run the query
    enquire = xapian.Enquire(db)
    enquire.set_query(query)

    # And print out something about each match
    matches = []
    for match in enquire.get_mset(0, db.get_doccount()):
        matches.append({'id': match.docid,
                        'rank' : match.rank + 1,
                        'percent' : match.percent,
                        # FIXME handle the case where there are no tags here
                        #'tags' : json.loads(unicode(match.document.get_value(XAPIAN_TAGS))),
                        'data' : json.loads(unicode(match.document.get_data()))})
                    

    return matches

def add_tag(dbpath, querystring, tag):
    db = xapian.WritableDatabase(dbpath, xapian.DB_CREATE_OR_OPEN)

    queryparser = xapian.QueryParser()
    queryparser.set_stemmer(xapian.Stem("en"))
    queryparser.set_stemming_strategy(queryparser.STEM_SOME)

    for term in PREFIXES:
        queryparser.add_prefix(term, PREFIXES[term])

    query = queryparser.parse_query(querystring)
    enquire = xapian.Enquire(db)
    enquire.set_query(query)

    for m in enquire.get_mset(0, db.get_doccount()):
        doc = m.document
        data = json.loads(doc.get_data())
        new_tags = data['tags']

        new_tags.append(tag)
        doc.add_boolean_term('K' + tag.lower())
        data['tags'] = new_tags
        doc.set_data(unicode(json.dumps(data)))
        assert 'K' + tag.lower() in [t.term for t in doc.termlist()]

        db.replace_document(m.docid, doc)
    

def remove_tag(dbpath, querystring, tags):
    return False

def all_songs(dbpath):
    "Iterator over all songs stored in the database <dbpath>."
    db = xapian.Database(dbpath)

    documents = (db.get_document(post.docid)
                   for post in db.postlist(""))
    
    return ({'id' : doc.get_docid(), 'data' : json.loads(doc.get_data())} 
             for doc in documents) 

