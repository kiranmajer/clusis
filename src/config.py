import os.path
import numpy as np

# import correct spectrumClass


class Cfg():
    def __init__(self,user_storage_dir, base_dir_name):
        if not os.path.isabs(user_storage_dir):
            raise ValueError('Please enter absolute path.')
        # cfg and base dir absolute
        cfg_dir = os.path.join(os.path.expanduser('~'), '.cludb')
        base_Dir = os.path.join(user_storage_dir, base_dir_name)
        # we keep the internal dir structure relative
        data_storage_dir = 'data'
        archive_storage_dir = 'archive'
        
        self.path = {'cfg': cfg_dir,
                     'base': base_Dir,
                     'data': data_storage_dir,
                     'archive': archive_storage_dir
                     }
        
        self.initDb()
        
    def initDb(self):
        print("You MUST overwrite initDb()!!")
        'TODO: Db should be machine independent in long term.'             
        self.db = {self.database_name: {'path': self.path['base'],  # path should always be absolute
                            }
                   }
        


        
        ''' Values used when importing legacy data'''
        self.defaults = {self.database_name : {
                                  }
                         }       
    def get_typeclass_map():
        print("You must overwrite get_typeclass_map()!!")
        
