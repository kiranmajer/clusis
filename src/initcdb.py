from dbshell import Db
import config_3f
from load import *
from speclist_3f import *
from git import Repo
import io_tools
#import ConfigParser
#import load
import os
from vcs_shell import Vcs
import sql_tools






 
        
def init_db(cfg):
    for dbName, dbProps in cfg.db.items():
        io_tools.ensure_path(dbProps['path'])
        dbFileName = '{}_v{}.db'.format(dbName, dbProps['version'])
        dbFilePath = os.path.join(dbProps['path'],dbFileName)
        if not os.path.exists(dbFilePath):
            print('Database does not exist, creating it.')
            with Db(dbName, cfg) as db:
                for specType in dbProps['layout'].keys():
                    db.create_table(specType)
            data_storage_path = os.path.join(cfg.path['base'], cfg.path['data'], dbName)
            if os.listdir(os.path.join(cfg.path['base'], cfg.path['data'])):
                repopulate_db(cfg, dbName, dbFileName, data_storage_path)
    
    return dbFilePath

            
def repopulate_db(cfg, db_name, db_filename, data_storage_path):
    '''
    Basically already implemented over add. Integrate scan pickle dir, build spec list, add.
    clear tables?
    check for missing entries? -> consistency check: each table entry has corresponding pickleFile'''
    print('Repopulating database "{}" from: {}'.format(db_filename, data_storage_path))
    mdata_json_list = load.ls(data_storage_path, 'json', recursive=True)
    #print(mdata_json_list)
    specdata_dir_list = [os.path.dirname(jf) for jf in mdata_json_list]
    #print(specdata_dir_list)
    # TODO: this can be a huge list so memory may run out -> split into managable chunks?
    spec_list = [load.spec_from_specdatadir(cfg, dir_path) for dir_path in specdata_dir_list]
    with Db(db_name, cfg)as db:
        db.add(spec_list, update=True)
        
        
        
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
            io_tools.ensure_path(p)
        else:
            p = os.path.join(cfg.path['base'], p)
            io_tools.ensure_path(p)
    
    sql_tools.setup_sqlite3()
    db_filename = os.path.basename(init_db(cfg))
    # if the .git folder does not exist init git repository and make an initial commit
    git_dir_path = os.path.join(cfg.path['base'], '.git')
    if not os.path.exists(git_dir_path):
        # init git repository
        rep = Repo.init(cfg.path['base'])
        del rep
        # create .gitignore with few defaults
        with Vcs(cfg.path['base']) as vcs:
            vcs.update_gitignore(db_filename)
#         with open(git_ignore_path, 'w') as f:
#             f.write('\n'.join([db_filename]))
#         # add .gitignore to index and commit
#         rep.index.add([git_ignore_path])
#         rep.git.commit('-a', '-m Repository initialization: adding ".gitignore".')
#         del rep
    
    return cfg
                
                