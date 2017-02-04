import json

import os
import errno

import re
import json

WORD_REGEX = re.compile(r'[\w]+')
def fsSafeString( text ):
    return "_".join(WORD_REGEX.findall(text))

def ensureDir(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

class FileDict(dict):
    def __init__(self, filename):
        self.filename = filename
        self.reload()

    def reload(self):
        try:
            with open(self.filename, 'r') as f:
                d = json.load(f)
                dict.__init__(self, d)
        except:
            pass
        return

    def __setitem__(self, i, y):
        r = dict.__setitem__(self, i, y)
        with open(self.filename, 'w') as f:
            json.dump(self, f, sort_keys=True, indent=2)
        return r

    def __getitem__(self, i):
        return dict.__getitem__(self, i)

class DirDict(FileDict):
    def __init__(self, dirname, keyHasher=fsSafeString, valueDumper=lambda x:x, valueLoader=lambda x:x):
        ensureDir(dirname)
        self.dirname = dirname
        self.keyHasher = keyHasher
        self.valueDumper = valueDumper
        self.valueLoader = valueLoader
        FileDict.__init__(self, os.path.join(self.dirname, '.keys2file') )
        self.reload()

    def filePath(self, filename):
        return os.path.join(self.dirname, filename)

    def __setitem__(self, key, content):
        filename = self.keyHasher(key)
        FileDict.__setitem__( self, key, filename )
        with open( self.filePath( filename ), 'w' ) as f:
            for l in self.valueDumper(content):
                f.write(l)
            f.flush()

    def __getitem__(self, key):
        filename = FileDict.__getitem__(self, key)
        with open( self.filePath( filename ), 'r' ) as f:
            r = "".join(f.readlines())
        return self.valueLoader(r)

