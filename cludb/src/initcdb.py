import os
from dbshell import Db
import config
import ConfigParser



def checkPath(p):
    if not os.path.exists(p):
        os.makedirs(p)
    elif not os.access(p, os.W_OK):
        raise IOError, '%s not accessible.' % p
        
def initDb(dbDict):
    for dbName, dbProps in dbDict.iteritems():
        checkPath(dbProps['path'])
        dbFileName = '%s.db' % dbName
        dbFile = os.path.join(dbProps['path'],dbFileName)
        if not os.path.exists(dbFile):
            with Db(dbName) as db:
                for specType in dbProps['layout'].iterkeys():
                    db.createTable(specType)
            
    
        
        
def initCludb(mainStorageDir=config.mainStorageDir):
    cfg = ConfigParser.SafeConfigParser()
    "set base path where all cludb files live"
    if mainStorageDir == config.mainStorageDir:
        userCfgFile = os.path.join(config.mainStorageDir, '.cludb')
        if os.path.isfile(userCfgFile):
            cfg.read(userCfgFile)
            config.mainStorageDir = cfg.get('Settings','mainStorageDir')
    else:
        userCfgFile = os.path.join(mainStorageDir, '.cludb')
            
            with open(userCfgFile) as f:
            
    config.mainStorageDir = mainStorageDir
    for p in config.path.itervalues():
        checkPath(p)
        
    initDb(config.db)
                
                