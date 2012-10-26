'''Just some tags for git'''

import os.path


'''
Adapting the following line should generally suffice.
'''
mainStorageDir = '/home/kiran/uni/python/ClusterBib_old'


'''
Only change the following if you know what you do
'''
dataStorageDir = os.path.join(mainStorageDir, 'data')
archiveStorageDir = os.path.join(dataStorageDir, 'archive')

path = {'base': mainStorageDir,
        'data': dataStorageDir,
        'archive': archiveStorageDir
        }
             
db = {'casi': {'path': path['data'],
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


defaults = {'casi': {'pes': {'timePerPoint': 2e-9,
                             'triggerOffset': 0,
                             'timeOffset': 63e-9,
                             'flightLength': 1.6
                             }
                     }
            }


ptPeakPar = {308e-9: [(2.128, 1.00, 0.01),
                      (2.224, 0.87, 0.01),
                      (2.889, 0.08, 0.01),
                      (2.942, 0.47, 0.01),
                      (3.384, 0.27, 0.01), 
                      (3.801, 1.14, 0.001)
                      ]
             }



