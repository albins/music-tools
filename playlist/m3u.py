# -*- mode: Python; encoding: utf-8; indent-tabs-mode: nil; tab-width: 2 -*-
import codecs

class M3UList(list):    
    def __init__(self, files, name=None, comments=[]):
        super(M3UList, self).__init__(files)
        self.name = name
        self.comments = comments

def parse(fn, name=None):
    "Parse and return a M3UList object given a file name."
    comments = list()
    files = list()
    with codecs.open(fn, encoding="utf-8") as pls:
        for line in pls:
            line = line.strip()
            if not line:
                continue
            elif line[0] == "#":
                # It's a comment!
                comments.append(line[1:].strip())
            else:
                files.append(line)
    return M3UList(files=files, name=name, comments=comments)
    
def write(m3u, fn):
    "Write the m3u object to a file with name fn. Dumps all commments at the beginning."
    if not type(fn) == file:
        plf = codecs.open(fn, 'wb', encoding="utf-8")
    else:
        writer = codecs.getwriter("utf8")
        plf = writer(fn)
    try:
        for comment in m3u.comments:
            plf.write(u"# %s\n" % comment)
        for path in m3u:
            plf.write("%s\n" % path)
    finally:
        plf.close()

        
        
    
