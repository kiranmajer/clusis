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
sys.path.append(os.path.normpath(os.path.join(os.getcwd(), '../../delay/src')))
from filestorage import load_xml, load_pickle, load_json
#import config



class LegacyData(object):
    
    def __init__(self, fileToImport, cfg, spectype=None, commonMdata={}, machine='casi',
                 prefer_filename_mdata=False):
        self.spectype = spectype
        self.datfile_orig = os.path.abspath(fileToImport)
        self.metadata = {'datFileOrig': os.path.abspath(fileToImport),
                         'tags': [],
                         'systemTags': [],
                         'userTags': [],
                         'evalTags': [],
                         'machine': machine,
                         'delayState': {},
                         'info': ''}
        self.cfg = cfg
        self.header = []
        self.data = []
        
        print('Parsing dat file ...')
        self.parse_file(fileToImport)
        print('Evaluating header ...')
        if self.spectype == 'generic':
            self.eval_header(min_line_count=90)
        else:
            self.eval_header()
        print('Setting up meta data ...')
        self.get_sha1()
        self.get_recTime(self.spectype)
        statedict = self.find_statefile()
        if statedict is None:
            print('No statefile, evaluating cfg file instead ...')
            self.eval_cfgfile(prefer_filename_mdata)
        else:
            self.eval_statedict(statedict)
#             if self.spectype not in ['generic']:
#                 print('Parsing dir structure ...')
#                 self.parse_dir_structure()
#                 print('... completed.')

        print('Setting specType ...')
        self.set_spectype(self.spectype)
        print('... {}'.format(self.metadata['specType']))
        self.set_storage_paths()
        self.add_default_mdata()
        if self.metadata['specType'] not in ['generic']:
            print('Parsing dir structure ...')
            self.parse_dir_structure()
            print('... completed.')
            if self.metadata['specType'] in ['ms']:
                print('Parsing ms datfile name ...')
                try:
                    self.parse_datfile_name()
                except:
                    for k in ['clusterBaseUnitNumberStart', 'clusterBaseUnitNumberEnd', 'trapTemp']:
                        if k in self.metadata.keys():
                            del self.metadata[k]
                
        print('Evaluating element name: ', self.metadata['clusterBaseUnit'])
        cbu = self.eval_element_name(self.metadata['clusterBaseUnit'], chemical_symbols)
        self.metadata['clusterBaseUnit'] = cbu
        print('Element name changed to: ', self.metadata['clusterBaseUnit'])
        if self.metadata['specType'] in ['ms']:
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
        self.mdata.add(self.metadata)
        if len(commonMdata) > 0:
            print('Importing commonMdata', commonMdata)
            self.mdata.add(commonMdata)
            #self.metadata.update(commonMdata)
        self.mdata.check_completeness()
    
    def parse_file(self, fileToImport):
        """Reads from a file and generates a header list and a data
        ndarray.
        """
        try:
            with open(fileToImport) as f:
                for line in f:
                    if re.search('^-{0,1}\d+.{0,1}\d*$',line.strip()) == None: # line contains more than a number
                        self.header.extend(line.split())
                    elif re.search('^-{0,1}\d+.{0,1}\d*[e|E]{0,1}-{0,1}\d*$',line.strip()):
                        self.data.append(float(line.strip()))
        except IOError as e:
            print('Reading ' + fileToImport + ' failed.')
            print("I/O error({0}): {1}".format(e.errno, e.strerror))
        else:
            self.data = np.array(self.data[:-1]) # last point has sometimes a strange value like 32768. Skip it!
            
    def eval_header(self, min_line_count=250):
        """Checks and makes a very basic analysis of header for key words:
            'Wellenlaenge:' -> pes
            'Trigger_Offset[s]' -> ms
        """
        if 'Wellenlaenge:' in self.header and len(self.data) > min_line_count:
            '''TODO: adapt for more machines'''
            self.datafile_type = 'pes'                
        elif 'Trigger_Offset[s]' in self.header and len(self.data) > min_line_count:
            self.datafile_type = 'ms'
            if self.header[1] == 'Trigger_Offset[s]':
                self.metadata['triggerOffset'] = float(self.header[0])
            if self.header[3] == 'Zeit_pro_Punkt[s]':
                self.metadata['timePerPoint'] = float(self.header[2])
            if self.header[5] == 'Eichmasse':
                self.metadata['referenceMass'] = float(self.header[4])
            if self.header[7] == 'Eichzeit[s]':
                self.metadata['referenceTime'] = float(self.header[6])
                self.metadata['referenceTimeImport'] = float(self.header[6])
            if self.header[9] == 'Time_Offset[s]':
                self.metadata['timeOffset'] = float(self.header[8])
                self.metadata['timeOffsetImport'] = float(self.header[8])
        else:
            raise ValueError('%s: Not a valid data file.'%self.metadata['datFileOrig'])
        
        
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
        if spectype in ['generic']:
            self.metadata['recTime'] = timeStamp
        else:
            datFileName = os.path.basename(self.metadata['datFileOrig'])
            if self.datafile_type == 'pes':
                pattern_groups = re.compile(r'(^\d{2})(\d{2})(\d{2})_')
                day, month, year = pattern_groups.search(datFileName).groups()
                if int(year) < 80: 
                    year = 2000 + int(year)
                else:
                    year = 1900 + int(year)
            elif self.datafile_type == 'ms':
                try:
                    pattern_groups = re.compile(r'(^\d{4})(\d{2})(\d{2})_')
                    year, month, day = pattern_groups.search(datFileName).groups()
                except:
                    year, month, day = 1970, 1, 1 # dummy date
                
            if self.datafile_type in ['pes', 'ms']:
                startDate = '%s %s %s' % (day, month, year)
                dayStarts = time.mktime(time.strptime(startDate, '%d %m %Y'))
                dayEnds = dayStarts + 86400
                if dayStarts <= timeStamp <= dayEnds or dayStarts == time.mktime(time.strptime('1 1 1970', '%d %m %Y')):
                    self.metadata['recTime'] = timeStamp
                else:
                    self.metadata['recTime'] = dayStarts
                    self.metadata['userTags'].append('Import warning: Invalid time stamp')
                    print('Warning: %s has invalid time stamp. Got recTime from filename.' % (datFileName))
            else:
                self.metadata['recTime'] = timeStamp

    
    def find_statefile(self):
        dat_file_name = os.path.splitext(os.path.basename(self.metadata['datFileOrig']))[0]
        dat_file_dir = os.path.dirname(self.metadata['datFileOrig'])
        statefile_json = os.path.join(dat_file_dir, dat_file_name + '.json')
        statefile_xml = os.path.join(dat_file_dir, dat_file_name + '.xml')
        statefile_pickle = os.path.join(dat_file_dir, dat_file_name + '.pickle')
        if os.path.isfile(statefile_json):
            state_dict = load_json(statefile_json)
            self.metadata['cfgFileOrig'] = statefile_json
        elif os.path.isfile(statefile_xml):
            state_dict = load_xml(statefile_xml)
            self.metadata['cfgFileOrig'] = statefile_xml
        elif os.path.isfile(statefile_pickle):
            state_dict = load_pickle(statefile_pickle)
            self.metadata['cfgFileOrig'] = statefile_pickle
        else:
            state_dict = None
            print('Could not find state file.')
        
        return state_dict
    
    def eval_statedict(self, statedict):
        self.metadata['delayState'] = statedict
            
    
    def find_cfgfile(self):
        """Gets the date and number out of the pes dat filename and searches
        for the associated cfg file: *ddmmyy_nn.cfg. Or searches for a cfg
        file with the same basename as the ms dat file.
        """
        dat_file_name = os.path.basename(self.metadata['datFileOrig'])
        dat_file_dir = os.path.dirname(self.metadata['datFileOrig'])
        if self.datafile_type == 'pes':
            pattern_groups = re.compile(r'(\d{6})_(\d+)')
            dat_fileDate, dat_fileNumber = pattern_groups.search(dat_file_name).groups()
            cfgfile = glob.glob(os.path.join(dat_file_dir,'*' + '_' + 
                                              dat_fileNumber + '_' + dat_fileDate 
                                              + '.cfg'))
            if len(cfgfile) == 0:
                cfgfile = glob.glob(os.path.join(dat_file_dir,'*' + dat_fileDate 
                                                  + '_' + dat_fileNumber + '.cfg'))
        elif self.datafile_type == 'ms':
            dat_fileShortname = os.path.splitext(dat_file_name)[0]
            cfgfile = glob.glob(os.path.join(dat_file_dir, dat_fileShortname + '.cfg'))
        else:
            raise ValueError('No specType specified.')
            
        if len(cfgfile) == 1:
            self.metadata['cfgFileOrig'] = cfgfile[0]
        elif len(cfgfile) == 0 and self.datafile_type == 'ms':
            print('No cfg. But for ms it is not vital. Skipping...')
            self.metadata['userTags'].append('Could not find cfg file')
        elif len(cfgfile) == 0 and self.datafile_type == 'pes':
            raise ValueError('Could not find cfg file.')
        else:
            self.metadata['userTags'].append('Several cfg files: ' + str(cfgfile))
            raise ValueError('Found more than 1 cfg file.')
     
    
    def parse_cfgfile(self, cfgfile, prefer_filename_mdata):
        """Extracts all information of cfgfile and its filename.
        """
#        cfg_data_map = ['ch1Tstart', 'ch1Tstop', 'ch2Tstart', 'ch2Tstop',
#                        'ch3Tstart', 'ch3Tstop', 'ch4Tstart', 'ch4Tstop',
#                        'ch5Tstart', 'ch5Tstop', 'ch6Tstart', 'ch6Tstop',
#                        'ch7Tstart', 'ch7Tstop', 'ch8Tstart', 'ch8Tstop',
#                        'clusterBaseUnitNumber']
        try:
            with open(cfgfile) as cfg:
                cfg_data = cfg.readlines()[0].split()
        except IOError as e:
            print("I/O error({0}): {1}".format(e.errno, e.strerror))
        else: # cfg file exist and is readable
            if len(cfg_data) == 17: # normal case
                self.metadata['clusterBaseUnitNumber'] = int(cfg_data.pop())
                ch_idx=1
                for pair in list(zip(cfg_data[::2],cfg_data[1::2])):
                    self.metadata['delayState']['ch{}'.format(ch_idx)] = [int(pair[0])*20e-9,
                                                                            (int(pair[1])-int(pair[0]))*20e-9]
                    ch_idx+=1

#                for i in range(len(cfg_data)-1):
#                    self.metadata[cfg_data_map[i]] = int(cfg_data[i])*20e-9
#                    
#                if self.datafile_type in ['pes']:
#                    self.metadata[cfg_data_map[-1]] = int(cfg_data[-1])
            elif len(cfg_data) == 1: # sometimes it contains only the cluster size
                self.metadata['clusterBaseUnitNumber'] = int(cfg_data.pop())              
#                if self.datafile_type in ['pes']:
#                    self.metadata[cfg_data_map[-1]] = int(cfg_data[-1])
            else:
                raise ValueError('{} does not contain valid data.'.format(cfgfile))
                    
            """Get information from file name (pes only)
            """
            if self.datafile_type in ['pes']:
                cfgfile_name_map = ['clusterBaseUnit', 'clusterBaseUnitNumber',
                              'cfgFileNumber', 'cfgFileDate.cfg']
                cfgfile_name = os.path.basename(self.metadata['cfgFileOrig'])
                if len(cfgfile_name.split('_')) == 4:
                    cfgfile_nameData = dict([(cfgfile_name_map[i], cfgfile_name.split('_')[i])
                                              for i in range(len(cfgfile_name_map))])
                    self.metadata['clusterBaseUnit'] = cfgfile_nameData['clusterBaseUnit']
                    """Test if cluster size in file and file name differs"""
                    if self.metadata['clusterBaseUnitNumber'] != int(cfgfile_nameData['clusterBaseUnitNumber']):
                        self.metadata['clusterBaseUnitNumberFromFileName'] = int(cfgfile_nameData['clusterBaseUnitNumber'])
                        if self.metadata['clusterBaseUnitNumber'] == 0 or prefer_filename_mdata:
                            self.metadata['userTags'].append('clusterBaseUnitNumber ambiguous ({})'.format(self.metadata['clusterBaseUnitNumber']))
                            self.metadata['clusterBaseUnitNumber'] = self.metadata['clusterBaseUnitNumberFromFileName']
                        else:
                            self.metadata['userTags'].append('clusterBaseUnitNumber ambiguous ({})'.format(self.metadata['clusterBaseUnitNumberFromFileName']))
                else:
                    raise ValueError('Unexpected file name: ' + cfgfile_name)

    
    def eval_cfgfile(self, prefer_filename_mdata):
        """Tries to find corresponding cfg files and adds unambiguous data to mdata
        """
        self.find_cfgfile()
        if 'cfgFileOrig' in self.metadata.keys():
            self.parse_cfgfile(self.metadata['cfgFileOrig'], prefer_filename_mdata=prefer_filename_mdata)


    def eval_element_name(self, element, reference):
        '''Returns a well capitalized string of an element name, if in reference.
        '''
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
        
    
    
    def parse_dir_structure(self):
        '''
        If the the full filepath contains self.metadata['machine'], try to extract some metadata
        from the dir structure and add it to mdata
        '''
        print('>>> parse_dir_structure <<<')
        if self.metadata['machine'] in self.metadata['datFileOrig'].split('/'):
            splitted_path = self.metadata['datFileOrig'].split('/')[self.metadata['datFileOrig'].split('/').index(self.metadata['machine']) + 1:]
            if len(splitted_path) == 5 or len(splitted_path) == 6:
                'TODO: we need a better conversion to ase understandable Atoms strings!'
                #cbu = 
                self.metadata['clusterBaseUnit'] = splitted_path[0]
                self.metadata['ionType'] = splitted_path[1]
                if splitted_path[2] == 'pure':
                    self.metadata['clusterDopant'] = None
                    self.metadata['clusterDopantNumber'] = 0
                else:
                    dopant_pattern = re.compile(r'(^[A-Za-z]{1,2})(\d{0,1})')
                    self.metadata['clusterDopant'] = dopant_pattern.search(splitted_path[2]).group(1).title()
                    if dopant_pattern.search(splitted_path[2]).group(2).isdigit():
                        self.metadata['clusterDopantNumber'] = int(dopant_pattern.search(splitted_path[2]).group(2))
                    else:
                        self.metadata['clusterDopantNumber'] = 1 
                self.datafile_type = splitted_path[3]
                if len(splitted_path) == 6 and splitted_path[4].replace('_', ' ') not in self.metadata['userTags']:
                    self.metadata['userTags'].append(splitted_path[4].replace('_', ' '))

                    
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
                         'ms': 'specMs',
                         'pes': 'specPe',
                         'pfs': 'specPf'}
        if self.metadata['specType'] == 'pes' and self.metadata['clusterBaseUnit'] in ['Pt']:
            self.metadata['specTypeClass'] = 'specPePt'
        elif self.metadata['specType'] == 'pes' and self.metadata['clusterBaseUnit'] in ['Ir']:
            self.metadata['specTypeClass'] = 'specPeIr'
        elif self.metadata['specType'] == 'pes' and self.metadata['clusterBaseUnit'] in ['H2O', 'D2O']:
            self.metadata['specTypeClass'] = 'specPeWater'
        else:
            self.metadata['specTypeClass'] = classtype_map[self.metadata['specType']]
            
    def build_mdata_ref(self, spec_type_class):
        ref_map = {'spec': ['spec'],
                   'specMs': ['spec', 'specMs'],
                   'specPe': ['spec', 'specPe'],
                   'specPePt': ['spec', 'specPe', 'specPePt'],
                   'specPeIr': ['spec', 'specPe', 'specPePt'],
                   'specPeWater': ['spec', 'specPe', 'specPeWater'],
                   'specPf': ['spec', 'specPf']}
        mdata_ref = {}
        for k in ref_map[spec_type_class]:
            mdata_ref.update(self.cfg.mdata_ref[k])
        return mdata_ref
        


