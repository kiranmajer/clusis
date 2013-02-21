import numpy as np
import re

class Mdata(object):
    
    
    def __init__(self, mdataDict, mdata_ref):
        self.__reference = mdata_ref
        self.__mdata = mdataDict
    
     
#    def __key_isvalid(self, key):
#        '''
#        True if key is a valid mdata key for this spec type.
#        '''
#        return key in self.__reference.keys()
     
     
    def __validate_value(self, key, value):
        '''
        Returns a valid value or raises an error.
        '''
        #print 'Checking: ', key, value
        #print 'type: ', type(value)
        ref = self.__reference
        if ref[key][0] is np.ndarray and type(value) is np.ndarray:
            return value
        elif ref[key][0] is str or float and value is None:
            return value
        elif type(ref[key][0]) is type:
            return ref[key][0](value)
        elif type(ref[key][0]) is list and value in ref[key][0]:
            return value
        elif type(ref[key][0]) is list and float(value) in ref[key][0]:
            return float(value)
        else:
            raise ValueError('Key: %s has wrong value or type: %s'  % (key, value))
    
    
    
    def __ask_for_key_value(self, key):
        value = input('Value of {} is missing or has wrong type. Please insert: '.format(key))
        return {key: value}
     
     
    def data(self, key=None):
        '''
        Getter method to read mdata via .data()
        '''
        if key == None:
            return self.__mdata
        else:
            return self.__mdata[key]
     
     
    def check_completeness(self):
        '''
        '''
        ref = self.__reference
        mdata = self.__mdata
        hasChanged = True
        while hasChanged:
            for k, v in ref.items():
                if v[1]: # obligatory?
                    if k in mdata:
                        try:
                            mdata[k] = self.__validate_value(k, mdata[k])
                            hasChanged = False
                        except:
                            mdata.update(self.__ask_for_key_value(k))
                            hasChanged = True
                            
                    else:
                        mdata.update(self.__ask_for_key_value(k))
                        hasChanged = True

        
    
    def add_tag(self, tag):
        'TODO: make more robust, e.g. check if tag is str.'
        l = self.__mdata['tags']
        if l.count(tag) == 0:
            l.append(tag)
        else:
            print('Tag already exists.')
    
    def rename_tag(self, parents, tag, newTag):
        l = self.__mdata['tags']
        self.__mdata['tags'] = [t.replace(tag,newTag) if re.search('(^|/)%s/?%s(/|$)'%(parents,tag), t) is not None else t for t in l]
       
    def remove_tag(self, tag):    
        'TODO: add method remove a whole tag tree at once.'
        l = self.__mdata['tags']
        if tag in l:
            l.remove(tag)
        else:
            raise ValueError('Tag does not exist: %s'%(str(tag)))
            
    
    def add(self, newMdata, update=False):
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
                if k in self.__reference.keys(): 
                    if k not in mdata.keys():
                        mdata[k] = self.__validate_value(k, v)
                    elif k == 'tags': # special case tags
                        if type(v) is list:
                            for t in v:
                                self.add_tag(t)
                        else:
                            self.add_tag(v)
                    elif update: #key exists, is not tags
                        mdata[k]=self.__validate_value(k, v)
                    else:
                        v = self.__validate_value(k, v)
                        overwrite=''
                        while overwrite not in ['y', 'n']:
                            q = 'Key "%s" already exists. Overwrite "%s" with "%s"? [y|n]: ' % (k, str(mdata[k]), str(v))
                            overwrite = input(q)
                        if overwrite == 'y':# else keep
                            mdata[k]=self.__validate_value(k, v)
                else:
                    print('Failed to add "%s: %s". Key not allowed.' % (k, str(v)))
          
        else:
            raise ValueError('Expected a dict. Got a %s instead.'%(type(newMdata).__name__))


    def update(self, newMdata):
        """
        Shortcut for add(newMdata, update=True)
        """
        self.add(newMdata, update=True)
        
    
    def rm(self, key):
        del self.__mdata[key]
        
        
        
        