import os
import sqlite3
from dbshell import Db
import config_3f
from load import *
from speclist_3f import *
from git import Repo
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
    
    return dbFile 
            
    
        
        
def init_cludb(user_storage_dir, base_dir_name):
    'TODO: provide global cfg object.'
    cfg = config_3f.Cfg(user_storage_dir, base_dir_name)
#    cfg = ConfigParser.SafeConfigParser()
#    "set base path where all cludb files live"
#    if mainStorageDir == config.mainStorageDir:
#        userCfgFile = os.path.join(config.mainStorageDir, '.cludb')
#        if os.path.isfile(userCfgFile):
#            cfg.read(userCfgFile)
#            config.mainStorageDir = cfg.get('Settings','mainStorageDir')
#    else:
#        userCfgFile = os.path.join(mainStorageDir, '.cludb')
#            
#            with open(userCfgFile) as f:
#            
#    config.mainStorageDir = mainStorageDir
    for p in cfg.path.values():
        if os.path.isabs(p):
            ensure_path(p)
        else:
            p = os.path.join(cfg.path['base'], p)
            ensure_path(p)
    
    setup_sqlite3()
    db_filename = os.path.basename(init_db(cfg))
    # if .gitignore does not exist init git and make an initial commit
    git_ignore_path = os.path.join(cfg.path['base'], '.gitignore')
    if not os.path.exists(git_ignore_path):
        # init git repository
        rep = Repo.init(cfg.path['base'])
        # create .gitignore with few defaults if it does not exist already
        with open(git_ignore_path, 'w') as f:
            f.write('\n'.join([db_filename]))
        # add .gitignore to index and commit
        rep.index.add([git_ignore_path])
        rep.git.commit('-a', '-m Repository initialization: adding ".gitignore".')
        del rep
    
    return cfg
                
                