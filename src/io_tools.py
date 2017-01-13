'''
Provides generic helper methods for io and file/folder handling 
'''
import os


def ensure_path(p):
    '''
    Makes sure all folders in p exist (or are created if not) and are writable.
    p: string containing the path of the folder to be verified.
    '''
    if not os.path.exists(p):
        os.makedirs(p)
    elif not os.access(p, os.W_OK):
        raise IOError('%s not accessible.' % p)