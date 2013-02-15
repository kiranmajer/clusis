import os.path
import numpy as np


class Cfg():
    def __init__(self,userStorageDir):
        if not os.path.isabs(userStorageDir):
            raise ValueError('Please enter absolute path.')
        # cfg and base dir absolute
        cfgDir = os.path.join(os.path.expanduser('~'), '.cludb')
        baseDir = os.path.join(userStorageDir, 'cludb3')
        # we keep the internal dir structure relative
        dataStorageDir = 'data'
        archiveStorageDir = 'archive'
        
        self.path = {'cfg': cfgDir,
                     'base': baseDir,
                     'data': dataStorageDir,
                     'archive': archiveStorageDir
                     }
                     
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
                                               ['recTime', 'REAL']
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
                                              ['recTime', 'REAL']
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
                                               ['recTime', 'REAL']
                                               ),
                                       'generic': (['sha1', 'TEXT PRIMARY KEY'],
                                                   ['pickleFile', 'TEXT UNIQUE'],
                                                   ['datFile', 'TEXT'],
                                                   ['tags', 'LIST'],
                                                   ['recTime', 'REAL'],
                                                   ['info', 'TEXT']
                                                   )
                                       }
                            }
                   }
        

        self.defaults = {'casi': {'pes': {'timePerPoint': 2e-9,
                                          'triggerOffset': 0,
                                          'timeOffset': 0, # 63e-9,
                                          'flightLength': 1.6
                                          }
                                  }
                         }
        
        '''
        Mdata reference: 'key': [type|value list, spectype list, obligatory]
        Only keys listed are allowed in mdata. Should prevent mdata from being tainted with typos.
        '''
        'TODO: mdata version, status key for gauged, fitted, subtracted?'
        self.mdataReference = {'casi': {'tags': [list, ['ms', 'pes', 'pfs'], True],
                                        'info': [str, ['ms', 'pes', 'pfs'], True],
                                        'sha1': [str, ['ms', 'pes', 'pfs'], True],
                                        'machine': [['casi'], ['ms', 'pes', 'pfs'], True],
                                        'recTime': [float, ['ms', 'pes', 'pfs'], True],
                                        'clusterBaseUnit': [str, ['ms', 'pes', 'pfs'], True],
                                        'clusterBaseUnitNumber': [int, ['pes', 'pfs'], True],
                                        'clusterBaseUnitNumberStart': [int,['ms'], True],
                                        'clusterBaseUnitNumberEnd': [int,['ms'], True],
                                        'clusterBaseUnitMass': [float,['ms'], True],
                                        'clusterDopant': [str, ['ms', 'pes', 'pfs'], True],
                                        'clusterDopantNumber': [int, ['ms', 'pes', 'pfs'], True],
                                        'specType': [['ms', 'pes', 'pfs'], ['ms', 'pes', 'pfs'], True],
                                        'ionType': [['+','-'], ['ms', 'pes', 'pfs'], True],
                                        'waveLength': [[157e-9, 193e-9, 248e-9, 308e-9, 800e-9],['pes', 'pfs'], True], # 193.35e-9
                                        'flightLength': [[1.6],['pes'], True],
                                        'referenceMass': [float,['ms'], True],
                                        'referenceTime': [float,['ms'], True],
                                        'timeOffset': [float,['ms','pes'], True],
                                        'triggerOffset':[float,['ms','pfs'], True],
                                        'trapTemp': [float, ['ms', 'pes', 'pfs'], False],
                                        'fitPeakPos': [list, ['pes'], False],
                                        'fitPeakPosTof': [list, ['pes'], False],
                                        'fitPar0': [np.ndarray, ['pes'], False],
                                        'fitPar': [np.ndarray, ['pes'], False],
                                        'fitCovar': [np.ndarray, ['pes'], False],
                                        'fitInfo': [list, ['pes'], False],
                                        'fitCutoff': [float, ['pes'], False],
                                        'fitGauged': [[True,False], ['pes'], False],
                                        'fitSubtractBg': [[True,False], ['pes'], False],
                                        'fitPar0Tof': [np.ndarray, ['pes'], False],
                                        'fitParTof': [np.ndarray, ['pes'], False],
                                        'fitCovarTof': [np.ndarray, ['pes'], False],
                                        'fitInfoTof': [list, ['pes'], False],
                                        'fitCutoffTof': [float, ['pes'], False],
                                        'fitGaugedTof': [[True,False], ['pes'], False],
                                        'fitSubtractBgTof': [[True,False], ['pes'], False],                                        
                                        'gaugeRef': [str, ['pes'], False],
                                        'gaugePar': [dict, ['pes'], False],
                                        'bgFile': [str, ['ms', 'pes', 'pfs'], False],
                                        'specFile': [str, ['ms', 'pes', 'pfs'], False]
                                        }
                               }
        
        
        self.ptPeakPar = {308e-9: [(2.128, 1.00, 0.01),
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
        
        
        self.ptPeakParAlt = {308e-9: [(2.12800, 1.00, 0.01),
                                      (2.22420, 0.87, 0.01),
                                      (2.23010, 0.08, 0.01),
                                      (2.88926, 0.47, 0.01),
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
#        self.ptLevelNist = [2.12800, 2.22420, 2.23010, 2.88926, 2.94227, 3.38232,
#                            3.38421, 3.80133, 4.04998, 4.42995, 4.85157, 5.43077,
#                            5.86699, 6.17236, 6.30385, 6.35860, 6.50733, 6.62818,
#                            6.68834, 6.69616, 6.75783, 6.78865, 6.81076, 6.90588,
#                            6.94056, 7.11145, 7.15138, 7.18505, 7.19567, 7.20764,
#                            7.31087, 7.41719, 7.48260, 7.57657, 7.63695, 7.63840,
#                            7.67385, 7.75668, 7.85240, 7.88327, 7.88507, 7.90845]



