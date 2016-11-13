import glob
import numpy as np
import os
#import pickle
import re
import time
import hashlib
from mdata import Mdata
from ase.atoms import Atoms
from ase.data import chemical_symbols
import sys
from scipy.stats.mstats_basic import threshold
sys.path.append(os.path.normpath(os.path.join(os.getcwd(), '../../delay/src')))
#from filestorage import load_xml, load_pickle, load_json
#import config
from importer import *





'''
####################################################
# Import data from mobile cluster source into 
# database
#
####################################################
'''
class RawDataMobileSource(importer):
    
    def __init__(self, fileToImport, cfg, parser, spectype=None, commonMdata={}):
   
        super().__init__(fileToImport, cfg, spectype=spectype, commonMdata=commonMdata)
        self.metadata['datFileOrig'] =  os.path.abspath(fileToImport)
        self.parser = parser
        
        '''
        Parse data file, generate time metrics and verify timemetrics
        '''
        print('Parsing dat file ...')
        self.parse_file(fileToImport)
        self.get_time_metrics()
        self.verify_time_metrics()
        
        
        print('Setting up meta data ...')
        self.get_sha1()
        self.get_recTime(self.spectype)
        self.set_storage_paths()
        self.add_default_mdata()
        if self.metadata['specType'] in ['ms', 'tof']:
            print('Fetching clusterBaseUnit mass for {} ...'.format(self.metadata['clusterBaseUnit']))
            self.metadata['clusterBaseUnitMass'] = Atoms(self.metadata['clusterBaseUnit']).get_masses().sum()
        print('Setting specTypeClass ...')
        self.set_spectype_class()
        print('... {}'.format(self.metadata['specTypeClass']))
        print('Converting metadata to Mdata object ...')
        print('Building mdata reference...')
        self.mdata_ref = self.build_mdata_ref(self.metadata['specTypeClass'])
        print('mdata ref.:', self.mdata_ref)
        self.mdata = Mdata({}, self.mdata_ref, cfg.mdata_systemtags)
        #del(self.metadata['datFileOrig'])
        self.mdata.add(self.metadata)
        if len(commonMdata) > 0:
            print('Importing commonMdata', commonMdata)
            self.mdata.add(commonMdata)
            #self.metadata.update(commonMdata)
        self.mdata.check_completeness()
    
    
    
    
    def set_metadata_from_config(self):
        return
    
    '''
####################################################
#
# parse the content of a  file
#
####################################################'''
    def parse_file(self, fileToImport):
        data = self.parser(fileToImport)
        
        self.data_t = data[0]
        self.data_ch1 = data[1]
        self.data_ch2 = data[2]
            
        
            
    '''
    ####################################################
    #
    # finding the relation between
    #
    ####################################################
    '''             
    def get_time_metrics(self):
        self.metadata['triggerOffset'] = -1*self.data_t[0] # offset from idx = 0
        self.metadata['timePerPoint'] = np.round((self.data_t[-1] - self.data_t[0])/(len(self.data_t) - 1), 9)
        
    def verify_time_metrics(self, threshold=10e-6):
        idx = np.arange(0,len(self.data_ch1))
        data_t_calc = idx*self.metadata['timePerPoint'] - self.metadata['triggerOffset']
        if np.sum(data_t_calc - self.data_t) > threshold:
            raise ValueError('Difference of calculated time data from orignal time data exceeds threshold.')
        else:
            print('Time metrics verified (within threshold of {}'.format(threshold))
        
    def add_default_mdata(self):
        print('>>> add_default_mdata <<<')
        # add default meta data to metadata 
        for k,v in self.cfg.defaults[self.metadata['machine']][self.metadata['specType']].items():
            if k not in list(self.metadata.keys()):
                self.metadata[k] = v
    
        
        
    def get_sha1(self):
        with open(self.metadata['datFileOrig'], 'rb') as f:
            sha1 = hashlib.sha1(f.read()).hexdigest()
        
        self.metadata['sha1'] = sha1
    
    
    def get_recTime(self, spectype):
        '''
        Checks the recording time from time stamp against filename. 
        pes, ms data files only (for now).
        '''
        timeStamp = os.stat(self.metadata['datFileOrig']).st_mtime        
        if spectype in ['generic', 'ms', 'tof']:
            self.metadata['recTime'] = timeStamp

    

    def eval_element_name(self, element, reference):
        '''Returns a well capitalized string of an element name, if in reference.
        '''
    #         i=0
    #         valid_name = None
    #         for e in reference:
    #             if element.lower() == e.lower():
    #                 valid_name = reference[i]
    #                 break
    #             i+=1   
        ref_lower = [e.lower() for e in reference]
        valid_name = ''
        pg=re.compile(r'(^\D+)(\d*)(\D*)(\d*)')
        eg = pg.search(element).groups()
        print('Using groups:', eg)
        for g in eg:
            if g.isdigit():
                valid_name += g
            elif g.lower() in ref_lower:
                valid_name += reference[ref_lower.index(g.lower())]
            elif g:
                raise ValueError("Couldn't find valid name for part", g)    
        if not valid_name:
            raise ValueError("Couldn't find valid name for ", element)
        else:
            return valid_name
    
    
    def set_storage_paths(self):
        """
        Adds data storage paths for *.dat, *.cfg, and *.pickle files to metadata
        """
        year = str(time.localtime(self.metadata['recTime']).tm_year)
        month = str(time.localtime(self.metadata['recTime']).tm_mon)
        day = str(time.localtime(self.metadata['recTime']).tm_mday)
        # dir for dat, cfg files
        
        archive_dir = os.path.join(self.cfg.path['archive'],
                                   self.metadata['machine'],
                                   self.metadata['specType'],
                                   year)
        
        self.metadata['datFile'] = os.path.join(archive_dir,
                                                os.path.basename(self.metadata['datFileOrig']))
        #self.metadata['userTags'] = []
        ''' build pickle file name and path according following scheme:
        config.path['data']/<year>/<recTime>_<sha1>.pickle'''
        
        pickleFileName = '{}-{}-{}_{}.pickle'.format(year, month, day, self.metadata['sha1'])
        pickleFileDir = os.path.join(self.cfg.path['data'],
                                     self.metadata['machine'],
                                     self.metadata['specType'],
                                     year)
        
        self.metadata['pickleFile'] = os.path.join(pickleFileDir, pickleFileName)
        if 'cfgFileOrig' in self.metadata.keys():
            self.metadata['cfgFile'] = os.path.join(archive_dir,
                                                    os.path.basename(self.metadata['cfgFileOrig']))

    
    
    def set_spectype(self, spectype):
        if spectype is None:
            self.metadata['specType'] = self.datafile_type
        elif spectype in self.cfg.mdata_ref['spec']['specType'][0]:
            self.metadata['specType'] = spectype
        else:
            raise ValueError('Unknown specType: {}'.format(spectype))
        
    
                   
    def parse_datfile_name(self):
        print('>>> parse_datfile_name <<<')
        fname_parts = os.path.splitext(os.path.basename(self.metadata['datFileOrig']))[0].split('_')
        print(fname_parts)
        if len(fname_parts) == 4:
            self.metadata['clusterBaseUnitNumberStart'] = fname_parts[2].split('-')[0]
            self.metadata['clusterBaseUnitNumberEnd'] = fname_parts[2].split('-')[-1]
            self.metadata['trapTemp'] = int(fname_parts[3].upper().split('K')[0])
        else:
            print('Warning: Could not parse file name (%s).'%(os.path.basename(self.metadata['datFileOrig'])))
            self.metadata['userTags'].append('Import warning: Could not parse file name.')


    def set_spectype_class(self):
        classtype_map = {'generic': 'spec',
                         'ms': 'specM',
                         'tof': 'specTof',
                         }
        self.metadata['specTypeClass'] = classtype_map[self.metadata['specType']]
            
    def build_mdata_ref(self, spec_type_class):
        ref_map = {'spec': ['spec'],
                   'specM': ['spec', 'specM'],
                   'specTof': ['spec', 'specTof'],
                   }
        mdata_ref = {}
        for k in ref_map[spec_type_class]:
            mdata_ref.update(self.cfg.mdata_ref[k])
        return mdata_ref
        











   