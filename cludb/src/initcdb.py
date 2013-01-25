import os
import sqlite3
from dbshell import Db
import config
#import ConfigParser



def checkPath(p):
    if not os.path.exists(p):
        os.makedirs(p)
    elif not os.access(p, os.W_OK):
        raise IOError('%s not accessible.' % p)
        

def listAdapter(l):
    return '<|>'.join(l)

def listConverter(s):
    '''Not sure why we get byte out while put str in.'''
    s = s.decode('utf-8')
    return s.split('<|>')

def prepSql():
    sqlite3.register_adapter(list, listAdapter)
    sqlite3.register_converter('LIST', listConverter)
 
        
def initDb(cfg):
    for dbName, dbProps in cfg.db.items():
        checkPath(dbProps['path'])
        dbFileName = '%s.db' % dbName
        dbFile = os.path.join(dbProps['path'],dbFileName)
        if not os.path.exists(dbFile):
            with Db(dbName, cfg) as db:
                for specType in dbProps['layout'].keys():
                    db.createTable(specType)
            
    
        
        
def initCludb(userStorageDir):
    'TODO: provide global cfg object.'
    cfg = config.Cfg(userStorageDir)
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
            checkPath(p)
        else:
            p = os.path.join(cfg.path['base'], p)
            checkPath(p)
    
    prepSql()
    initDb(cfg)
    
    return cfg
                
                