import os.path
import numpy as np


class Cfg():
    def __init__(self,user_storage_dir, base_dir_name):
        if not os.path.isabs(user_storage_dir):
            raise ValueError('Please enter absolute path.')
        # cfg and base dir absolute
        cfg_dir = os.path.join(os.path.expanduser('~'), '.clusis_3f')
        base_Dir = os.path.join(user_storage_dir, base_dir_name)
        # we keep the internal dir structure relative
        data_storage_dir = 'data'
        archive_storage_dir = 'archive'
        
        self.path = {'cfg': cfg_dir,
                     'base': base_Dir,
                     'data': data_storage_dir,
                     'archive': archive_storage_dir
                     }
        
        'TODO: Db should be machine independent in long term.'             
        self.db = {'3f': {'path': self.path['base'],  # path should always be absolute
                          'layout': {'tof': (['sha1', 'TEXT PRIMARY KEY'],
                                             ['clusterBaseUnit', 'TEXT'],
                                             ['pickleFile', 'TEXT UNIQUE'],
                                             ['dataFile', 'TEXT'],
                                             ['deflectorVoltage', 'REAL'],
                                             ['tags', 'LIST'],
                                             ['recTime', 'REAL'],
                                             ),
                                     'ms': (['sha1', 'TEXT PRIMARY KEY'],
                                            ['clusterBaseUnit', 'TEXT'],
                                            ['pickleFile', 'TEXT UNIQUE'],
                                            ['dataFile', 'TEXT'],
                                            ['tags', 'LIST'],
                                            ['recTime', 'REAL'],
                                            ),
                                     'generic': (['sha1', 'TEXT PRIMARY KEY'],
                                                 ['pickleFile', 'TEXT UNIQUE'],
                                                 ['dataFile', 'TEXT'],
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
                                   'specTypeClass': [['spec', 'specMs', 'specTof'], True],
                                   'sweeps': [int, False],
                                   'systemTags': [list, True],
                                   'tags': [list, True], # combined tags of *Tags (for db)
                                   'timePerPoint': [float, True],
                                   'triggerOffset': [float, True],
                                   'triggerFrequency': [float, False],
                                   'userTags': [list, True],
                                   },
                          'specMs': {'clusterBaseUnit': [str, True],
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
                                        },
                                'ms': {'mdataVersion': self.mdata_version
                                       },
                                'generic': {'mdataVersion': self.mdata_version
                                            },
                                }
                         }       
        
#        
# 
#     def convert_mdata_v0p1_to_v0p2(self, mdata):
#         start_version = 0.1
#         target_version = 0.2
#         if mdata['mdataVersion'] == start_version: 
#             print('Converting mdata from version {} to {} ...'.format(start_version, target_version))
#             if mdata['specType'] in ['generic']:
#                 mdata['mdataVersion'] = target_version
#             else:
#                 mdata['delayState'] = mdata.pop('delayTimings')
#                 mdata['mdataVersion'] = target_version
#         else:
#             raise ValueError('mdata has wrong version: {}, expected {}.'.format(mdata['mdataVersion'],
#                                                                                 start_version))
#         
#         return mdata 
#     
#     def convert_mdata_v0p2_to_v0p3(self, mdata):
#         start_version = 0.2
#         target_version = 0.3
#         if mdata['mdataVersion'] == start_version:
#             print('Converting mdata from version {} to {} ...'.format(start_version, target_version))
#             if mdata['specTypeClass'] in ['specPeWater'] and 'fitPar' in mdata.keys():
#                 print('Converting fit data in new dictionary ...')
#                 mdata['fitData'] = {'default_fit': {'covar': mdata.pop('fitCovar'),
#                                                     'cutoff': mdata.pop('fitCutoff'),
#                                                     'info': mdata.pop('fitInfo'),
#                                                     'par': mdata.pop('fitPar'),
#                                                     'par0': mdata.pop('fitPar0'),
#                                                     'xdataKey': mdata.pop('fitXdataKey'),
#                                                     'ydataKey': mdata.pop('fitYdataKey'),
#                                                     }
#                                     }
#                 mdata['evalTags'] = ['default_fit']
#                 mdata['tags'].append('default_fit')
#                 mdata['mdataVersion'] = target_version
#             else:
#                 mdata['evalTags'] = []
#                 mdata['mdataVersion'] = target_version
#         else:
#             raise ValueError('mdata has wrong version: {}, expected {}.'.format(mdata['mdataVersion'],
#                                                                                 start_version))
#         
#         return mdata
#         
