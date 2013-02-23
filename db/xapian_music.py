#!/usr/bin/python
# -*- mode: Python; encoding: utf-8; indent-tabs-mode: nil; tab-width: 2 -*-

import xapian
from db.dirtree import get_songs
import json
import os
import time

# a mapping of query term/aliases → xapian prefixes.
# most of these are also keys to the song[] dict.
# Prefixes from http://xapian.org/docs/omega/termprefixes.html
PREFIXES = {'artist' : 'A',
            'title' : 'S',
            'path' : 'U',
            'album' : 'XALBUM',
            'title' : 'XTITLE'}

# These numeric prefixes will also be used as data slots.
NUMERIC_PREFIXES = {'year' : 'Y',
                    'mtime' : 'XMTIME',
                    'tracknumber' : 'XTRACKNR',
                    'rating' : 'XRATING'}

def index(datapath, dbpath):
    # Create or open the database we're going to be writing to.
    db = xapian.WritableDatabase(dbpath, xapian.DB_CREATE_OR_OPEN)

    # Set up a TermGenerator that we'll use in indexing.
    termgenerator = xapian.TermGenerator()
    termgenerator.set_stemmer(xapian.Stem("en"))

    def make_value(s, term):
        "Parse various string values and return suitable numeric representations."
        if term == 'year':
            # This is in a date string format due to serialization.
            return xapian.sortable_serialise(int(s))
        if term == 'mtime':
            return xapian.sortable_serialise(time.mktime(time.strptime(s)))
        if term == 'rating':
            return xapian.sortable_serialise(max([float(n) for n in s]))
        else:
            return xapian.sortable_serialise(int(s))

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

        for data_slot, term in enumerate(NUMERIC_PREFIXES):
            if song[term]:
                doc.add_value(data_slot, make_value(song[term], term))
                

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

def parse_query(q):
    "Parse the query <q> and return a query ready for use with enquire.set_query()."
    
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

def query(dbpath, querystring):
    "Query the database at path <dbpath> with the string <querystring>. Return iterator over maches. This is mostly for internal use, as it returns xapian match objects."

    # Open the database we're going to search.
    db = xapian.Database(dbpath)

    query = parse_query(querystring)

    # Use an Enquire object on the database to run the query
    enquire = xapian.Enquire(db)
    enquire.set_query(query)

    for match in enquire.get_mset(0, db.get_doccount()):
        yield match

def search(dbpath, querystring):
    "Search the database at dbpath with querystring. Return list of matches."

    return [({'id': match.docid,
                'rank' : match.rank + 1,
                'percent' : match.percent,
                'data' : json.loads(unicode(match.document.get_data()))})
            for match in query(dbpath, querystring)]

def add_tag(dbpath, querystring, tag):
    "Add the tag <tag> to all songs matching <querystring>."
    db = xapian.WritableDatabase(dbpath, xapian.DB_CREATE_OR_OPEN)
    
    for m in query(dbpath, querystring):
        doc = m.document
        data = json.loads(doc.get_data())
        new_tags = data['tags']

        new_tags.append(tag)
        doc.add_boolean_term('K' + tag.lower())
        data['tags'] = new_tags
        doc.set_data(unicode(json.dumps(data)))
        # This is to make sure the term was actually added BEFORE
        # modifying the database.
        assert 'K' + tag.lower() in [t.term for t in doc.termlist()]

        db.replace_document(m.docid, doc)
    
def remove_tag(dbpath, querystring, tag):
    db = xapian.WritableDatabase(dbpath, xapian.DB_CREATE_OR_OPEN)

    for m in query(dbpath, querystring):
        doc = m.document
        data = json.loads(doc.get_data())
        new_tags = [tag for tag in data['tags'] if tag != tag]

        doc.remove_term('K' + tag.lower())
        data['tags'] = new_tags
        doc.set_data(unicode(json.dumps(data)))
        assert 'K' + tag.lower() not in [t.term for t in doc.termlist()]

        db.replace_document(m.docid, doc)

def all_songs(dbpath):
    "Iterator over all songs stored in the database <dbpath>."
    db = xapian.Database(dbpath)

    documents = (db.get_document(post.docid)
                   for post in db.postlist(""))
    
    return ({'id' : doc.get_docid(), 'data' : json.loads(doc.get_data())} 
             for doc in documents) 

