from __future__ import unicode_literals
import os.path
import numpy as np


class Cfg():
    def __init__(self,userStorageDir):
        if not os.path.isabs(userStorageDir):
            raise ValueError, 'Please enter absolute path.'
        'cfg and base dir absolute'
        cfgDir = os.path.join(os.path.expanduser('~'), '.cludb')
        baseDir = os.path.join(userStorageDir, 'cludb')
        'we keep the internal dir structure relative'
        dataStorageDir = 'data'
        archiveStorageDir = 'archive'
        
        self.path = {'cfg': cfgDir,
                'base': baseDir,
                'data': dataStorageDir,
                'archive': archiveStorageDir
                }
                     
        self.db = {'casi': {'path': self.path['base'], # path should always be absolute
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
                                  }
                       }
              } 
        
        
        self.defaults = {'casi': {'pes': {'timePerPoint': 2e-9,
                                          'triggerOffset': 0,
                                          'timeOffset': 63e-9,
                                          'flightLength': 1.6
                                          }
                                  }
                         }
        
        '''
        Mdata reference: 'key': [type|value list, spectype list, obligatory]
        '''
        self.mdataReference = {'casi': {'tags': [list, ['ms', 'pes', 'pfs'], True],
                                        'sha1': [str, ['ms', 'pes', 'pfs'], True],
                                        'machine': [['casi'], ['ms', 'pes', 'pfs'], True],
                                        'recTime': [float, ['ms', 'pes', 'pfs'], True],
                                        'clusterBaseUnit': [str, ['ms', 'pes', 'pfs'], True],
                                        'clusterDopant': [str, ['ms', 'pes', 'pfs'], True],
                                        'clusterDopantNumber': [str, ['ms', 'pes', 'pfs'], True],
                                        'specType': [['ms', 'pes', 'pfs'], ['ms', 'pes', 'pfs'], True],
                                        'ionType': [['+','-'], ['ms', 'pes', 'pfs'], True],
                                        'clusterBaseUnitNumber': [int, ['pes', 'pfs'], True],
                                        'waveLength': [[157e-9, 193e-9, 248e-9, 308e-9, 800e-9],['pes', 'pfs'], True],
                                        'flightLength': [[1.6],['pes'], True],
                                        'referenceMass': [float,['ms'], True],
                                        'referenceTime': [float,['ms'], True],
                                        'timeOffset': [float,['ms','pes'], True],
                                        'clusterBaseUnitNumberStart': [int,['ms'], True],
                                        'clusterBaseUnitNumberEnd':[int,['ms'], True],
                                        'trapTemp': [float, ['ms', 'pes', 'pfs'], False],
                                        'fitPeakPos': [list, ['pes'], False],
                                        'fitPar0': [list, ['pes'], False],
                                        'fitPar': [np.ndarray, ['pes'], False],
                                        'fitCovar': [np.ndarray, ['pes'], False],
                                        'fitInfo': [list, ['pes'], False],
                                        'fitCutoff': [float, ['pes'], False]
                                        }
                               }
        
        
        self.ptPeakPar = {308e-9: [(2.128, 1.00, 0.01),
                              (2.224, 0.87, 0.01),
                              (2.889, 0.08, 0.01),
                              (2.942, 0.47, 0.01),
                              (3.384, 0.27, 0.01), 
                              (3.801, 1.14, 0.001)
                              ]
                     }
        
        
        
