import os.path
import numpy as np


class Cfg():
    def __init__(self,user_storage_dir):
        if not os.path.isabs(user_storage_dir):
            raise ValueError('Please enter absolute path.')
        # cfg and base dir absolute
        cfg_dir = os.path.join(os.path.expanduser('~'), '.cludb')
        base_Dir = os.path.join(user_storage_dir, 'cludb3refac')
        # we keep the internal dir structure relative
        data_storage_dir = 'data'
        archive_storage_dir = 'archive'
        
        self.path = {'cfg': cfg_dir,
                     'base': base_Dir,
                     'data': data_storage_dir,
                     'archive': archive_storage_dir
                     }
        
        'TODO: Db should be machine independent in long term.'             
        self.db = {'casi': {'path': self.path['base'],  # path should always be absolute
                            'layout': {'pes': (['sha1', 'TEXT PRIMARY KEY'],
                                               ['clusterBaseUnit', 'TEXT'],
                                               ['clusterBaseUnitNumber', 'INTEGER'],
                                               ['clusterDopant', 'TEXT'],
                                               ['clusterDopantNumber', 'INTEGER'],
                                               ['pickleFile', 'TEXT UNIQUE'],
                                               ['datFile', 'TEXT'],
                                               ['tags', 'LIST'],
                                               ['waveLength', 'REAL'],
                                               ['recTime', 'REAL'],
                                               ['machine', 'TEXT']
                                               ),
                                       'ms': (['sha1', 'TEXT PRIMARY KEY'],
                                              ['clusterBaseUnit', 'TEXT'],
                                              ['clusterBaseUnitNumberStart', 'INTEGER'],
                                              ['clusterBaseUnitNumberEnd', 'INTEGER'],
                                              ['clusterDopant', 'TEXT'],
                                              ['clusterDopantNumber', 'INTEGER'],
                                              ['pickleFile', 'TEXT UNIQUE'],
                                              ['datFile', 'TEXT'],
                                              ['tags', 'LIST'],
                                              ['recTime', 'REAL'],
                                               ['machine', 'TEXT']
                                              ),
                                       'pfs': (['sha1', 'TEXT PRIMARY KEY'],
                                               ['clusterBaseUnit', 'TEXT'],
                                               ['clusterBaseUnitNumber', 'INTEGER'],
                                               ['clusterDopant', 'TEXT'],
                                               ['clusterDopantNumber', 'INTEGER'],
                                               ['pickleFile', 'TEXT UNIQUE'],
                                               ['datFile', 'TEXT'],
                                               ['tags', 'LIST'],
                                               ['waveLength', 'REAL'],
                                               ['recTime', 'REAL'],
                                               ['machine', 'TEXT']
                                               ),
                                       'generic': (['sha1', 'TEXT PRIMARY KEY'],
                                                   ['pickleFile', 'TEXT UNIQUE'],
                                                   ['datFile', 'TEXT'],
                                                   ['tags', 'LIST'],
                                                   ['recTime', 'REAL'],
                                                   ['info', 'TEXT'],
                                                   ['machine', 'TEXT']
                                                   )
                                       }
                            }
                   }
        


        '''
        Mdata reference: 'key': [type|value list, obligatory]
        Only keys listed are allowed in mdata. Should prevent mdata from being tainted with typos.
        '''
        self.wavelengths = [157e-9, 193e-9, 248e-9, 308e-9, 800e-9] # 157.63e-9, 193.35e-9, 248.4e-9
        'When modified -> increase mdata_version!'
        self.mdata_version = 0.1
        self.mdata_ref = {'spec': {'datFile': [str, True],
                                   'info': [str, True],
                                   'machine': [['casi'], True],
                                   'mdataVersion': [[self.mdata_version], True],
                                   'pickleFile': [str, True],
                                   'recTime': [float, True],
                                   'sha1': [str, True],
                                   'specType': [['ms', 'pes', 'pfs', 'generic'], True],
                                   'specTypeClass': [['spec', 'specMs', 'specPe', 'specPePt', 'specPeWater', 'specPf'], True],
                                   'systemTags': [list, True],
                                   'tags': [list, True], # combined tags of systemTags and userTags (for db)
                                   'timePerPoint': [float, True],
                                   'triggerOffset': [float, True],
                                   'userTags': [list, True],
                                   },
                          'specMs': {'cfgFile': [str, False],
                                     'clusterBaseUnit': [str, True],
                                     'clusterBaseUnitMass': [float, True],
                                     'clusterBaseUnitNumberStart': [int, True],
                                     'clusterBaseUnitNumberEnd': [int, True],
                                     'clusterDopant': [str, True],
                                     'clusterDopantMass': [float, True],
                                     'clusterDopantNumber': [int, True],
                                     'delayTimings': [dict, False],
                                     'ionType': [['+','-'], True],
                                     'referenceMass': [float, True],
                                     'referenceTime': [float, True],
                                     'referenceTimeImport': [float, True],
                                     'subtractBgRef': [str, False],
                                     'timeOffset': [float, True],
                                     'timeOffsetImport': [float, True],
                                     'trapTemp': [float, False],
                                     },
                          'specPe': {'cfgFile': [str, False],
                                     'clusterBaseUnit': [str, True],
                                     'clusterBaseUnitNumber': [int, True],
                                     'clusterDopant': [str, True],
                                     'clusterDopantNumber': [int, True],
                                     'delayTimings': [dict, False],
                                     'energyOffset': [float, True],
                                     'energyOffsetImport': [float, True],
                                     'flightLength': [[1.6], True],
                                     'flightLengthScale': [float, True],
                                     'flightLengthScaleImport': [float, True],
                                     'gaugeRef': [str, False],
                                     'ionType': [['+','-'], True],
                                     'subtractBgRef': [str, False],
                                     'timeOffset': [float, True],
                                     'timeOffsetImport': [float, True],
                                     'trapTemp': [float, False],
                                     'waveLength': [self.wavelengths, True],
                                     },
                          'specPePt': {'fitCovar': [np.ndarray, False],
                                       'fitConstrains': [dict, False],
                                       'fitCutoff': [float, False],
                                       'fitInfo': [list, False],
                                       'fitPar': [np.ndarray, False],
                                       'fitPar0': [np.ndarray, False],
                                       'fitPeakPos': [list, False],
                                       'fitXdataKey': [['tof', 'tofGauged', 'ebin', 'ebinGauged'], False],
                                       'fitYdataKey': [['intensity', 'intensitySub', 'jIntensity', 'jIntensitySub'], False]
                                       },
                          'specPeWater': {'fitCovar': [np.ndarray, False],
                                          'fitCutoff': [float, False],
                                          'fitInfo': [list, False],
                                          'fitPar': [np.ndarray, False],
                                          'fitPar0': [np.ndarray, False],
                                          'fitXdataKey': [['tof', 'tofGauged', 'ebin', 'ebinGauged'], False],
                                          'fitYdataKey': [['intensity', 'intensitySub', 'jIntensity', 'jIntensitySub'], False]
                                          },
                          'specPf': {'cfgFile': [str, False],
                                     'clusterBaseUnit': [str, True],
                                     'clusterBaseUnitMass': [float, True],
                                     'clusterBaseUnitNumber': [int, True],
                                     'clusterDopant': [str, True],
                                     'clusterDopantMass': [float, True],
                                     'clusterDopantNumber': [int, True],
                                     'delayTimings': [dict, False],
                                     'ionType': [['+','-'], True],
                                     'subtractBgRef': [str, False],
                                     'timeOffset': [float, True],
                                     'trapTemp': [float, False],
                                     'waveLength': [self.wavelengths, True],
                                     },
                          }

#                    Legacy mdata:
#                    'fitCovarTof': [np.ndarray, ['pes'], False],
#                    
#                    'fitCutoffTof': [float, ['pes'], False],
#                    'fitGauged': [[True,False], ['pes'], False],
#                    'fitGaugedTof': [[True,False], ['pes'], False],
#                    
#                    'fitInfoTof': [list, ['pes'], False],
#                    
#                    'fitPar0Tof': [np.ndarray, ['pes'], False],
#                    'fitParTof': [np.ndarray, ['pes'], False],
#                    
#                    'fitPeakPosTof': [list, ['pes'], False],
#                    'fitSubtractBg': [[True,False], ['pes'], False],
#                    'fitSubtractBgTof': [[True,False], ['pes'], False], 
                    
        
        ''' Values used when importing legacy data'''
        self.defaults = {'casi': {'pes': {'energyOffset': 0,
                                          'energyOffsetImport': 0,
                                          'flightLength': 1.6,
                                          'flightLengthScale': 1.0,
                                          'flightLengthScaleImport': 1.0,
                                          'mdataVersion': self.mdata_version,
                                          'timeOffset': 63e-9,
                                          'timeOffsetImport': 63e-9, # previously used for all pes (better derived by gauging)
                                          'timePerPoint': 2e-9,
                                          'triggerOffset': 0,
                                          },
                                  'ms': {'mdataVersion': self.mdata_version
                                         },
                                  'pfs': {'mdataVersion': self.mdata_version
                                          },
                                  'generic': {'mdataVersion': self.mdata_version
                                              },
                                  }
                         }       
        
        
        self.pt_peakpar = {308e-9: [(2.128, 1.00, 0.01),
                                    (2.224, 0.87, 0.01),
                                    (2.889, 0.08, 0.01),
                                    (2.942, 0.47, 0.01),
                                    (3.384, 0.27, 0.01), 
                                    (3.801, 1.14, 0.001)
                                    ],
                           248e-9: [(2.128, 1.00, 0.01),
                                    (2.224, 0.91, 0.01),
                                    (2.889, 0.06, 0.01),
                                    (2.942, 0.25, 0.01),
                                    (3.384, 0.22, 0.01),
                                    (3.801, 1.05, 0.001),
                                    (4.050, 0.57, 0.001),
                                    (4.430, 0.57, 0.001),
                                    (4.852, 2.20, 0.001)
                                    ]
                           }
        
        
        self.pt_peakpar_alt = {308e-9: [(2.128, 1.00, 0.01),
                                        (2.224, 0.87, 0.01),
                                        (2.889, 0.08, 0.01),
                                        (2.942, 0.47, 0.01),
                                        (3.384, 0.27, 0.01), 
                                        (3.801, 1.14, 0.001),
                                        (3.851, 1.14, 0.001)
                                        ],
                               248e-9: [(2.128, 1.00, 0.01),
                                        (2.224, 0.91, 0.01),
                                        (2.889, 0.06, 0.01),
                                        (2.942, 0.25, 0.01),
                                        (3.384, 0.22, 0.01),
                                        (3.791, 1.05, 0.001),
                                        (3.811, 1.05, 0.001),
                                        (4.040, 0.57, 0.001),
                                        (4.060, 0.57, 0.001),
                                        (4.420, 0.57, 0.001),
                                        (4.440, 0.57, 0.001),
                                        (4.847, 2.20, 0.001),
                                        (4.857, 2.20, 0.001)
                                        ]
                               }
        
        self.pt_level_nist = [2.12800, 2.22420, 2.23010, 2.88926, 2.94227, 3.38232,
                              3.38421, 3.80133, 4.04998, 4.42995, 4.85157, 5.43077,
                              5.86699, 6.17236, 6.30385, 6.35860, 6.50733, 6.62818,
                              6.68834, 6.69616, 6.75783, 6.78865, 6.81076, 6.90588,
                              6.94056, 7.11145, 7.15138, 7.18505, 7.19567, 7.20764,
                              7.31087, 7.41719, 7.48260, 7.57657, 7.63695, 7.63840,
                              7.67385, 7.75668, 7.85240, 7.88327, 7.88507, 7.90845]



