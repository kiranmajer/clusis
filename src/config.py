import os.path
import numpy as np
from abc import ABCMeta, abstractmethod
# import correct spectrumClass


class Cfg(metaclass=ABCMeta):
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
        self.metadata = {
                 'tags': [],
                 'systemTags': [],
                 'userTags': [],
                 'evalTags': [],
                 'machine': self.get_machine(),
                 'delayState': {},
                 'info': ''
                }
        self.initDb()
        
        
        
        
    @abstractmethod
    def initDb(self):
        pass
    
    @abstractmethod
    def get_typeclass_map(self):
        pass
    
    @abstractmethod
    def get_metadata(self):
        pass
    
    @abstractmethod
    def get_machine(self):
        pass
    
    @abstractmethod
    def get_spectrum(self):
        pass
    
    @abstractmethod
    def get_speclist(self):
        pass