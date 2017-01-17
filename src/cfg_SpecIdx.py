'''
Mdata layout definition
cfg_* can be used to override/extent the layout definitions for the spec class *.
'''


mdata_ref = {'spec': {'timePerPoint': {'mdata_type': float, 
                                       'mdata_required': True,
                                       'db_included': False},
                      'timeOffset': {'mdata_type': float, 
                                     'mdata_required': True,
                                     'db_included': False},
                      'triggerOffset': {'mdata_type': float, 
                                        'mdata_required': True,
                                        'db_included': False},
                      'triggerFrequency': {'mdata_type': float, 
                                           'mdata_required': False,
                                           'db_included': False},
                      }
             }