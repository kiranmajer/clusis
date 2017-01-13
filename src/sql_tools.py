'''
Provides generic helper methods for sql related stuff.
'''
import sqlite3


# Adapters to handle python type <=> sql type conversion
def list_adapter(l):
    list_to_text = '<||>'.join(l)
    list_to_text = '|>' + list_to_text + '<|'
    return list_to_text

def list_converter(s):
    '''Not sure why we get byte out while put str in.'''
    text_to_list = s.decode('utf-8')
    text_to_list = text_to_list.lstrip('|>').rstrip('<|').split('<||>')
    return text_to_list

# setup adapters
def setup_sqlite3():
    sqlite3.register_adapter(list, list_adapter)
    sqlite3.register_converter('LIST', list_converter)