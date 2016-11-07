import os.path
import numpy as np
from config import *
from spec_3f import *
from speclist_3f import *
from rawData_3f import *

class Cfg3f(Cfg):
    def __init__(self,user_storage_dir, base_dir_name):
        self.database_name = '3f'
        self.typeclass_map = {'spec': Spec,
                         'specM': SpecM,
                         'specTof': SpecTof}
        
        self.channel_map={'ch1': 'rawVoltageSpec', 'ch2': 'rawVoltageRamp'}
        super().__init__(user_storage_dir, base_dir_name) # calls initDb
        
    
    def get_typeclass_map(self):
        return self.typeclass_map 
    
    def get_raw_data(self,datFile,spectype,commonMdata={}):
        return RawData_3f(datFile, self, spectype, commonMdata=commonMdata)
    
    
    def get_speclist(self, spectype='ms'):
        s=False
        if spectype == 'ms':
            print('Assuming Type: Massspectrum')
            s= SpecMList(self)
            
        return s
    
    def get_spectrum(self,mi):
        # init spec obj
        mdata = mi.mdata.data()         
        #~~~~~~~
        ydata = {self.channel_map['ch1']: mi.data_ch1}
        ydata[self.channel_map['ch2']] = mi.data_ch2
        xdata = {'idx': np.arange(0,len(ydata['rawVoltageSpec']))} # intensity for [i,i+1] will be displayed at i+0.5
        spec = self.typeclass_map[mdata['specTypeClass']](mdata, xdata, ydata, self)
        #~~~~~~~
        return spec
    
    def initDb(self):
        'TODO: Db should be machine independent in long term.'             
        self.db = {self.database_name: {'path': self.path['base'],  # path should always be absolute
                          'layout': {'tof': (['sha1', 'TEXT PRIMARY KEY'],
                                             ['clusterBaseUnit', 'TEXT'],
                                             ['pickleFile', 'TEXT UNIQUE'],
                                             ['datFile', 'TEXT'],
                                             ['deflectorVoltage', 'REAL'],
                                             ['tags', 'LIST'],
                                             ['recTime', 'REAL'],
                                             ),
                                     'ms': (['sha1', 'TEXT PRIMARY KEY'],
                                            ['clusterBaseUnit', 'TEXT'],
                                            ['pickleFile', 'TEXT UNIQUE'],
                                            ['datFile', 'TEXT'],
                                            ['tags', 'LIST'],
                                            ['recTime', 'REAL'],
                                            ),
                                     'generic': (['sha1', 'TEXT PRIMARY KEY'],
                                                 ['pickleFile', 'TEXT UNIQUE'],
                                                 ['datFile', 'TEXT'],
                                                 ['tags', 'LIST'],
                                                 ['recTime', 'REAL'],
                                                 ['info', 'TEXT'],
                                                 )
                                     }
                          }
                   }
        


        '''
        Mdata reference: 'key': [type|value list, obligatory]
        Only keys listed are allowed in mdata. Should prevent mdata from being tainted with typos.
        '''
#         self.wavelengths = [157.63e-9, 193.35e-9, 248.4e-9, 308e-9, 590e-9, 800e-9] # 157.63e-9, 193.35e-9, 248.4e-9
        'When modified -> increase mdata_version!'
        self.mdata_version = 0.1
        self.mdata_ref = {'spec': {'datFile': [str, True],
                                   'evalTags': [list, True],
                                   'info': [str, True],
                                   'machine': [['3f'], True],
                                   'mdataVersion': [float, True],
                                   'pickleFile': [str, True],
                                   'recTime': [float, True],
                                   'sha1': [str, True],
                                   'specType': [['ms', 'tof', 'generic'], True],
                                   'specTypeClass': [['spec', 'specM', 'specTof'], True],
                                   'sweeps': [int, False],
                                   'systemTags': [list, True],
                                   'tags': [list, True], # combined tags of *Tags (for db)
                                   'timePerPoint': [float, True],
                                   'timeOffset': [float, True],
                                   'triggerOffset': [float, True],
                                   'triggerFrequency': [float, False],
                                   'userTags': [list, True],
                                   },
                          'specM': {'clusterBaseUnit': [str, True],
                                    'clusterBaseUnitMass': [float, True],
                                    'ionType': [['+','-'], True],
                                    'refTofSpec':[str, False],
                                    },
                          'specTof': {'cfgFile': [str, False],
                                      'clusterBaseUnit': [str, True],
                                      'clusterBaseUnitMass': [float, True],
                                      'deflectorVoltage': [float, True],
                                      'flightLength': [float, True],
                                      'ionType': [['+','-'], True],
                                      },
                          }


        self.mdata_systemtags = ['trash', 'background', 'fitted', 'gauged', 'subtracted', 'up/down']
                    
        
        ''' Values used when importing legacy data'''
        self.defaults = {'3f': {'tof': {'flightLength': 0.19,
                                        'mdataVersion': self.mdata_version,
                                        'timeOffset': 0,
                                        },
                                'ms': {'mdataVersion': self.mdata_version,
                                       'timeOffset': 0,
                                       },
                                'generic': {'mdataVersion': self.mdata_version,
                                            'timeOffset': 0,
                                            },
                                }
                         }       
         
