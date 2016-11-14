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
from



class RawData_3f(object):
    
    def __init__(self, fileToImport, cfg, spectype=None, commonMdata={}, cbu='Ag', machine='3f'):
        if spectype in cfg.mdata_ref['spec']['specType'][0]:
            #print('Got valid spectype: {}'.format(spectype))
            self.spectype = spectype
        else:
            raise ValueError('Unknown spectype: {}'.format(spectype))
        self.datfile_orig = os.path.abspath(fileToImport)
        self.metadata = {'datFileOrig': os.path.abspath(fileToImport),
                         'tags': [],
                         'systemTags': [],
                         'userTags': [],
                         'evalTags': [],
                         'machine': machine,
                         'info': '',
                         'clusterBaseUnit': cbu,
                         'specType': self.spectype,
                         }
        self.cfg = cfg
        self.header = []
        self.data = []
        
        #print('Parsing dat file ...')
        self.parse_file(fileToImport)
        self.get_time_metrics()
        self.verify_time_metrics()
        #print('Setting up meta data ...')
        self.get_sha1()
        self.get_recTime(self.spectype)
        self.set_storage_paths()
        self.add_default_mdata()
        if self.metadata['specType'] in ['ms', 'tof']:
            #print('Fetching clusterBaseUnit mass for {} ...'.format(self.metadata['clusterBaseUnit']))
            self.metadata['clusterBaseUnitMass'] = Atoms(self.metadata['clusterBaseUnit']).get_masses().sum()
        #print('Setting specTypeClass ...')
        self.set_spectype_class()
        #print('... {}'.format(self.metadata['specTypeClass']))
        #print('Converting metadata to Mdata object ...')
        #print('Building mdata reference...')
        self.mdata_ref = self.build_mdata_ref(self.metadata['specTypeClass'])
        #print('mdata ref.:', self.mdata_ref)
        self.mdata = Mdata({}, self.mdata_ref, cfg.mdata_systemtags)
        #del(self.metadata['datFileOrig'])
        self.mdata.add(self.metadata)
        if len(commonMdata) > 0:
            #print('Importing commonMdata', commonMdata)
            self.mdata.add(commonMdata)
            #self.metadata.update(commonMdata)
        self.mdata.check_completeness()
    
    def parse_file(self, fileToImport):
        """Reads from a file and generates a header list and a data
        ndarray.
        """
        try:
            with open(fileToImport) as f:
                column_name=f.readline().strip('\n').split(',')
                column_unit=f.readline().strip('\n').split(',')
#                 for line in f:
#                     if re.search('^-{0,1}\d+.{0,1}\d*$',line.strip()) == None: # line contains more than a number
#                         self.header.extend(line.split())
#                     elif re.search('^-{0,1}\d+.{0,1}\d*[e|E]{0,1}-{0,1}\d*$',line.strip()):
#                         self.data.append(float(line.strip()))
        except IOError as e:
            print('Reading ' + fileToImport + ' failed.')
            print("I/O error({0}): {1}".format(e.errno, e.strerror))
        
        spec_data = np.genfromtxt(fileToImport, skip_header=2, delimiter=',', unpack=True)
        
        si_factor = {'s': 1,
                     'ms': 1e-3,
                     'us': 1e-6,
                     'ns': 1e-9,
                     'V': 1,
                     'mV': 1e-3,
                    }
        column_unit=[u.lstrip('(').rstrip(')') for u in column_unit]
        
        self.data_t = spec_data[column_name.index('Time')]*si_factor[column_unit[column_name.index('Time')]]
        self.data_ch1 = spec_data[column_name.index('Channel A')]*si_factor[column_unit[column_name.index('Channel A')]]
        self.data_ch2 = spec_data[column_name.index('Channel B')]*si_factor[column_unit[column_name.index('Channel B')]]
            
            
    def get_time_metrics(self):
        self.metadata['triggerOffset'] = -1*self.data_t[0] # offset from idx = 0
        self.metadata['timePerPoint'] = np.round((self.data_t[-1] - self.data_t[0])/(len(self.data_t) - 1), 9)
        
    def verify_time_metrics(self, threshold=10e-6):
        idx = np.arange(0,len(self.data_ch1))
        data_t_calc = idx*self.metadata['timePerPoint'] - self.metadata['triggerOffset']
        if np.sum(data_t_calc - self.data_t) > threshold:
            raise ValueError('Difference of calculated time data from orignal time data exceeds threshold.')
        else:
            print('Time metrics verified (within threshold of {})'.format(threshold))
        
    def add_default_mdata(self):
        #print('>>> add_default_mdata <<<')
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
        
        datFileName = os.path.basename(self.metadata['datFileOrig'])
        if parseFilenameForDate(datFileName) is not False:
            year,month,day = parseFilenameForDate(datFileName)
        else:
            year, month, day = 1970, 1, 1 # dummy date
    
        startDate = '%s %s %s' % (day, month, year)
        dayStarts = time.mktime(time.strptime(startDate, '%d %m %Y'))
        dayEnds = dayStarts + 86400
        if dayStarts <= timeStamp <= dayEnds :
            self.metadata['recTime'] = timeStamp
        else:
            self.metadata['recTime'] = dayStarts
            self.metadata['userTags'].append('Import warning: Invalid time stamp')
            print('Warning: %s has invalid time stamp. Got recTime from filename.' % (datFileName))
        
    

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
        Adds data storage paths for *.dat, *.cfg, and specdata dir files to metadata
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
        ''' build specdata dir path according to following scheme:
        config.path['data']/<year>/<recTime>_<sha1>'''

        spec_data_dir_name = '{}-{}-{}_{}'.format(year, month, day, self.metadata['sha1'])
        data_dir_base_dir = os.path.join(self.cfg.path['data'],
                                         self.metadata['machine'],
                                         self.metadata['specType'],
                                         year)
        self.metadata['dataStorageLocation'] = os.path.join(data_dir_base_dir, spec_data_dir_name)
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
        











   