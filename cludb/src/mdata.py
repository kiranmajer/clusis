import numpy as np
import re

class Mdata(object):
    
    
    def __init__(self, mdataDict, mdata_ref, systemtags_ref):
        self.__reference = mdata_ref
        self.__mdata = mdataDict
        self.__systemtags_ref = systemtags_ref
    
     
#    def __key_isvalid(self, key):
#        '''
#        True if key is a valid mdata key for this spec type.
#        '''
#        return key in self.__reference.keys()
     
     
    def __validate_value(self, key, value):
        '''
        Returns a valid value or raises an error.
        '''
#         print('Starting new validation run.')
#         print('Checking: ', key, value)
#         print('type: ', type(value))
        ref = self.__reference
        if ref[key][0] is np.ndarray and type(value) is np.ndarray:
            v = value
        elif ref[key][0] is str or float and value is None:
            v = value
        elif type(ref[key][0]) is type:
            v = ref[key][0](value)
        elif type(ref[key][0]) is list and value in ref[key][0]:
            v = value
        elif type(ref[key][0]) is list and float(value) in ref[key][0]:
            v = float(value)
        else:
            raise ValueError('Key: %s has wrong value or type: %s'  % (key, value))
        return v
    
    
    def __ask_for_key_value(self, key):
        value = input('Value of {} is missing or has wrong type. Please insert: '.format(key))
        return {key: value}
     
     
    def data(self, key=None):
        '''
        Getter method to read mdata via .data()
        '''
        'TODO: for mutable types, like list,dict return copy! Prevents altering mdata from outside.'
        if key == None:
            return self.__mdata
        else:
            return self.__mdata[key]
     
     
    def check_completeness(self):
        '''
        '''
        print('Starting mdata check ...')
        ref = self.__reference
        mdata = self.__mdata
        for k, v in ref.items():
            if v[1]: # obligatory?
                print('{} is obligatory. Checking value ...'.format(k))
                hasChanged = True
                while hasChanged:
                    if k in mdata:
                        try:
                            mdata[k] = self.__validate_value(k, mdata[k])
                            hasChanged = False
                            print('{}: exists and has a valid value.'.format(k))
                        except:
                            mdata.update(self.__ask_for_key_value(k))
                            hasChanged = True
                            
                    else:
                        print('Missing obligatory mdata detected: {}'.format(k))
                        mdata.update(self.__ask_for_key_value(k))
                        hasChanged = True

        
    
    def add_tag(self, tag, tagkey='userTags'):
        tag = str(tag)
        if tag in self.__systemtags_ref:
            tagkey = 'systemTags'
        if tagkey == 'systemTags' and tag not in self.__systemtags_ref:
            raise ValueError('{} not a valid system tag.'.format(tag))
        current_tags = self.__mdata[tagkey]
        if current_tags.count(tag) == 0:
            current_tags.append(tag)
            self.__update_tags()
        else:
            print('Tag already exists.')
    
    def rename_tag(self, parents, tag, newTag, tagkey='userTags'):
        'TODO: better parent handling.'
        current_tags = self.__mdata[tagkey]
        self.__mdata[tagkey] = [t.replace(tag,newTag) if re.search('(^|/)%s/?%s(/|$)'%(parents,tag), t) is not None else t for t in current_tags]
        self.__update_tags()
       
    def remove_tag(self, tag, tagkey='userTags'):    
        'TODO: add method remove a whole tag tree at once.'
        tag = str(tag)
        current_tags = self.__mdata[tagkey]
        if tag in current_tags:
            current_tags.remove(tag)
            self.__update_tags()
        else:
            raise ValueError('Tag does not exist: {}'.format(tag))
        
    def __update_tags(self):
        'For db usage: Merges userTags and systemTags and add keys of "compSpecs".'
        self.__mdata['tags'] = list(set(self.__mdata['systemTags'])|set(self.__mdata['userTags']))
        if 'compSpecs' in self.__mdata.keys() and self.__mdata['compSpecs'].keys():
            for k in self.__mdata['compSpecs'].keys():
                self.__mdata['tags'].append('CompSpec: {}'.format(k))
            
    
    def add(self, newMdata, update=False):
        """
        Safely add new meta data to the mdata dict. Only accepts valid key, value pairs
        for the given spec type.
        
        TODO: if k == wavelength self._hv needs to be adapted and specdata needs to be recalculated!
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
                    elif k in ['tags', 'userTags']: # special case userTags, 'tags' is treated like 'userTags' 
                        if type(v) is list:
                            for t in v:
                                self.add_tag(t)
                        else:
                            self.add_tag(v)
                    elif k == 'compSpecs':
                        mdata[k].update(self.__validate_value(k, v))
                    elif k == 'info' and not mdata[k]: # info contains already a string
                        mdata[k] = mdata[k] + self.__validate_value(k, v)
                    elif update: #key exists, is not tags not compSpecs
                        mdata[k] = self.__validate_value(k, v)
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
            self.__update_tags()
        else:
            raise ValueError('Expected a dict. Got a %s instead.'%(type(newMdata).__name__))


    def update(self, newMdata):
        """
        Shortcut for add(newMdata, update=True)
        """
        self.add(newMdata, update=True)
        
    
    def rm(self, key):
        del self.__mdata[key]
        
        
    def eval_element_name(self, element, reference):
        '''Returns a well capitalized string of an element name, if in reference.
        '''
        i=0
        valid_name = None
        for e in reference:
            if element.lower() == e.lower():
                valid_name = reference[i]
                break
            i+=1   
        
        if valid_name is None:
            raise ValueError("Couldn't find valid name for ", element)
        else:
            return valid_name     
        
        