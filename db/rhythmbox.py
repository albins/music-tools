# -*- mode: Python; encoding: utf-8; indent-tabs-mode: nil; tab-width: 2 -*-

from lxml import etree
from urllib2 import unquote

def get_songs(rb):
    "Get all songs in a rhythmbox XML tree."
    tree = etree.parse(rb)
    root = tree.getroot()

    tags = (element for element in root if element.get('type') == 'song')

    for song in tags:
        title = None
        artist = None
        location = None

        for field in song:
            if field.tag == 'title':
                title = unicode(field.text)
            elif field.tag == 'artist':
                artist = unicode(field.text)
            elif field.tag == 'location':
                location = unicode(unquote(field.text[7:]), encoding="utf-8")
        
        song_data = (title, artist, location)

        if not None in song_data:
            yield song_data
        
    
