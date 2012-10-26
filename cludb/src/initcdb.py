'''
Initializes paths and db folders.
'''
import os
from dbshell import Db
import config



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
            
    
        
        
        
for p in config.path.itervalues():
    checkPath(p)
    
initDb(config.db)
                
                