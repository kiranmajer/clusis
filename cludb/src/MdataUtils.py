from __future__ import unicode_literals
import numpy as np

class Mdata(object):
    
    
    def __init__(self, mdataDict, cfg):
        self.__reference = cfg.mdataReference[mdataDict['machine']]
        self.__mdata = mdataDict
    
     
    def __keyValid(self, key):
        '''
        True if key is a valid mdata key for this spec type.
        '''
        if key in self.__reference.keys() and self.__mdata['specType'] in self.__reference[key][1]:
            return True
        else:
            return False
     
     
    def __validValue(self, key, value):
        '''
        Returns a valid value or raises an error.
        '''
        #print 'Checking: ', key, value
        #print 'type: ', type(value)
        ref = self.__reference
        if ref[key][0] is np.ndarray and type(value) is np.ndarray:
            return value
        elif type(ref[key][0]) is type:
            return ref[key][0](value)
        elif type(ref[key][0]) is list and value in ref[key][0]:
            return value
        elif type(ref[key][0]) is list and float(value) in ref[key][0]:
            return float(value)
        else:
            raise ValueError('Key: %s has wrong value or type: %s'  % (key, value))
    
    
    
    def __askForKeyValue(self, key):
        value = raw_input('Value of %s is missing or has wrong type. Please insert: ' % (key))
        return {key: value}
     
     
    def data(self, key=None):
        '''
        Getter method to read mdata via .data()
        '''
        if key == None:
            return self.__mdata
        else:
            return self.__mdata[key]
     
     
    def checkIfComplete(self):
        '''
        '''
        ref = self.__reference
        mdata = self.__mdata
        if 'specType' in mdata:
            hasChanged = True
            while hasChanged:
                for k, v in ref.iteritems():
                    if mdata['specType'] in v[1] and v[2]:
                        if mdata.has_key(k):
                            try:
                                mdata[k] = self.__validValue(k, mdata[k])
                                hasChanged = False
                            except:
                                mdata.update(self.__askForKeyValue(k))
                                hasChanged = True
                                
                        else:
                            mdata.update(self.__askForKeyValue(k))
                            hasChanged = True
                                  
        else:
            raise ValueError('No specType: Can not perform sanity check.')
        
        
        
    def add(self, newMdata):
        """
        Safely add new meta data to the mdata dict. Only accepts valid key, value pairs
        for the given spec type.
        """
        mdata = self.__mdata
        if type(newMdata) is dict:
            #self.failedKeys = {}
            mdataToAdd = dict(newMdata) # make a copy so we can use popitem()
            while len(mdataToAdd) > 0:
                k,v = mdataToAdd.popitem()
                if self.__keyValid(k): 
                    if k not in mdata:
                        mdata[k]=self.__validValue(k, v)
                    elif k == 'tags': # special case tags
                        if type(v) is list:
                            mdata[k].extend(v)
                        else:
                            mdata[k].append(v)
                        
                    else:
                        v = self.__validValue(k, v)
                        overwrite=''
                        while overwrite not in ['y', 'n']:
                            q = 'Key "%s" already exists. Overwrite "%s" with "%s"? [y|n]: ' % (k, str(mdata[k]), str(v))
                            overwrite = raw_input(q)
                        if overwrite == 'y':# else keep
                            mdata[k]=self.__validValue(k, v)
                else:
                    print 'Failed to add "%s: %s". Key not allowed.' % (k, str(v))
          
        else:
            raise ValueError('Expected a dict. Got a %s instead.' % type(newMdata).__name__)

    
    
    def rm(self, key):
        del self.__mdata[key]
        
        
        
        