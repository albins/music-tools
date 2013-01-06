#!/usr/bin/python
# -*- mode: Python; encoding: utf-8; indent-tabs-mode: nil; tab-width: 2 -*-

import xapian
from db.dirtree import get_songs

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
        # Prefixes from http://xapian.org/docs/omega/termprefixes.html
        termgenerator.index_text(song['title'], 1, 'S')
        termgenerator.index_text(song['artist'], 1, 'A')
#        termgenerator.index_text(description, 1, 'XD')

        # Index fields without prefixes for general search.
        termgenerator.index_text(song['title'])
        termgenerator.increase_termpos()
        termgenerator.index_text(song['artist'])

        # Store all the fields for display purposes.
        doc.set_data(unicode(song['mdata']))

        # use doc.add_term(str.join(K, "my tag"), 0) to add tags the way notmuch does

        # We use the identifier to ensure each object ends up in the
        # database only once no matter how many times we run the
        # indexer.
        idterm = u"Q" + song['path']
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
    queryparser.add_prefix("title", "S")
    queryparser.add_prefix("artist", "A")

    # And parse the query
    query = queryparser.parse_query(querystring)

    # Use an Enquire object on the database to run the query
    enquire = xapian.Enquire(db)
    enquire.set_query(query)

    # And print out something about each match
    matches = []
    for match in enquire.get_mset(0, 100):
        matches.append(match.docid)

    return matches
