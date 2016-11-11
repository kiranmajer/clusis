import os.path
import numpy as np
from config import *
from spec_3f import *
from speclist_3f import *
from rawData_3f import *
from parsing_files import *


'''
#########################################
##
## Config class for data aquired in
## third floor
##
######################################### 
'''
class Cfg3f(Cfg):
    def __init__(self,user_storage_dir, base_dir_name):
        self.database_name = '3f'
        self.typeclass_map = {'spec': Spec,
                         'specM': SpecM,
                         'specTof': SpecTof}
        
        self.typeclass_of_lists_map = {'generic': SpecList,
                         'ms': SpecMList,
                         'tof': SpecTofList}
        
        self.channel_map={'ch1': 'rawVoltageSpec', 'ch2': 'rawVoltageRamp'}
        self.rawdatatype="RawData_3f"
        super().__init__(user_storage_dir, base_dir_name) # calls initDb
        
        '''
            change here if u use somthing else than silver
        '''
        self.metadata['clusterBaseUnit'] = 'Ag'
   


    def list_tables(self):
        
        with Db(self.database_name, self) as db:
            tablenames = db.list_tables()
            for row in tablenames:
                print(row['name'])
    def get_machine(self):
        return "Mobile Clustersource"
    
    def get_metadata(self):
        return self.metadata
        
    def get_typeclass_map(self):
        return self.typeclass_map 
    
    
    def get_raw_data(self,datFile,spectype,commonMdata={}):
        return RawDataMobileSource(datFile, self, parse_picoscope, spectype=spectype, commonMdata=commonMdata)
    
    
    def get_speclist(self, spectype='ms'):
        s=False
        if not spectype in self.typeclass_of_lists_map.keys():
            print("No such Spectrumtpe: "+ spectype)
            print("Available SpecTypes are:")
            self.list_tables()
            return
        if spectype == 'ms':
            print('Assuming Type: Massspectrum')
            s= self.typeclass_of_lists_map[spectype](self)
        if spectype == 'tof':
            print('Assuming Type: Time-Of-Flight')
            s= self.typeclass_of_lists_map[spectype](self)
        if spectype == 'generic':
            print('Assuming Type: Generic')
            s= self.typeclass_of_lists_map[spectype](self)
        
        
        return s
    
    
    
    
    def init_flighttimes(self):
        spectra = self.get_speclist(spectype='ms')
        for spec in spectra:
            self.init_flighttime(spec)
        
    def init_flighttime(self,massSpec):
        tofs = get_speclist(spectype='tof')
        
    
    
    
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
                                             ['flighttime', 'REAL'],
                                             ),
                                     'ms': (['sha1', 'TEXT PRIMARY KEY'],
                                            ['clusterBaseUnit', 'TEXT'],
                                            ['pickleFile', 'TEXT UNIQUE'],
                                            ['datFile', 'TEXT'],
                                            ['tags', 'LIST'],
                                            ['recTime', 'REAL'],
                                            ['flighttime', 'REAL'],
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
         
