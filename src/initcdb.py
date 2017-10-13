import os
import sqlite3
from dbshell import Db
import config
#import ConfigParser



def ensure_path(p):
    if not os.path.exists(p):
        os.makedirs(p)
    elif not os.access(p, os.W_OK):
        raise IOError('%s not accessible.' % p)
        

def list_adapter(l):
    list_to_text = '<||>'.join(l)
    list_to_text = '|>' + list_to_text + '<|'
    return list_to_text

def list_converter(s):
    '''Not sure why we get byte out while put str in.'''
    text_to_list = s.decode('utf-8')
    text_to_list = text_to_list.lstrip('|>').rstrip('<|').split('<||>')
    return text_to_list

def setup_sqlite3():
    sqlite3.register_adapter(list, list_adapter)
    sqlite3.register_converter('LIST', list_converter)
 
        
def init_db(cfg):
    for dbName, dbProps in cfg.db.items():
        ensure_path(dbProps['path'])
        dbFileName = '%s.db' % dbName
        dbFile = os.path.join(dbProps['path'],dbFileName)
        if not os.path.exists(dbFile):
            with Db(dbName, cfg) as db:
                for specType in dbProps['layout'].keys():
                    db.create_table(specType)
            
    
        
        
def init_cludb(user_storage_dir, base_dir_name):
    'TODO: provide global cfg object.'
    cfg = config.Cfg(user_storage_dir, base_dir_name)
    for p in cfg.path.values():
        if os.path.isabs(p):
            ensure_path(p)
        else:
            p = os.path.join(cfg.path['base'], p)
            ensure_path(p)
    
    setup_sqlite3()
    init_db(cfg)
    
    return cfg
                
                