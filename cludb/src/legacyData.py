import glob
import numpy as np
import os
#import pickle
import re
import time
import hashlib
from mdata import Mdata
from ase.atoms import Atoms
#import config



class LegacyData(object):
    
    def __init__(self, fileToImport, cfg, spectype=None, commonMdata={}, machine='casi'):
        self.spectype = spectype
        self.datfile_orig = os.path.abspath(fileToImport)
        self.metadata = {'datFileOrig': os.path.abspath(fileToImport),
                         'tags': [],
                         'systemTags': [],
                         'userTags': [],
                         'machine': machine,
                         'delayTimings': {},
                         'info': ''}
        self.cfg = cfg
        self.header = []
        self.data = []
        
        print('Parsing dat file ...')
        self.parse_file(fileToImport)
        print('Evaluating header ...')
        self.eval_header()
        print('Setting up meta data ...')
        self.get_sha1()
        self.get_recTime(self.spectype)
        print('Evaluating cfg file ...')
        self.eval_cfgfile()
        print('Setting specType ...')
        self.set_spectype(self.spectype)
        self.set_storage_paths()
        self.add_default_mdata()
        if self.metadata['specType'] not in ['generic']:
            print('Parsing dir structure ...')
            self.parse_dir_structure()
            if self.metadata['specType'] in ['ms']:
                print('Parsing ms datfile name ...')
                self.parse_datfile_name()
                self.metadata['clusterBaseUnitMass'] = Atoms(self.metadata['clusterBaseUnit']).get_masses().sum()
        self.set_spectype_class()
        print('Convert metadata to Mdata object ...')
        self.mdata = Mdata({}, self.cfg.mdata_ref[self.metadata['specTypeClass']]) 
        self.mdata.add(self.metadata)
        if len(commonMdata) > 0:
            #print 'Importing commonMdata', commonMdata
            self.mdata.add(commonMdata)
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
                pattern_groups = re.compile(r'(^\d{4})(\d{2})(\d{2})_')
                year, month, day = pattern_groups.search(datFileName).groups()
                
            if self.datafile_type in ['pes', 'ms']:
                startDate = '%s %s %s' % (day, month, year)
                dayStarts = time.mktime(time.strptime(startDate, '%d %m %Y'))
                dayEnds = dayStarts + 86400
                if dayStarts <= timeStamp <= dayEnds:
                    self.metadata['recTime'] = timeStamp
                else:
                    self.metadata['recTime'] = dayStarts
                    self.metadata['userTags'].append('Import warning: Invalid time stamp')
                    print('Warning: %s has invalid time stamp. Got recTime from filename.' % (datFileName))
            else:
                self.metadata['recTime'] = timeStamp


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
     
    
    def parse_cfgfile(self, cfgfile):
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
                    self.metadata['delayTimings']['ch{}'.format(ch_idx)] = [int(pair[0]*20e-9),
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
                        self.metadata['userTags'].append('clusterBaseUnitNumber ambiguous')
                else:
                    raise ValueError('Unexpected file name: ' + cfgfile_name)

    
    def eval_cfgfile(self):
        """Tries to find corresponding cfg files and adds unambiguous data to mdata
        """
        self.find_cfgfile()
        if 'cfgFileOrig' in self.metadata.keys():
            self.parse_cfgfile(self.metadata['cfgFileOrig'])

    
    
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
        if self.metadata['machine'] in self.metadata['datFileOrig'].split('/'):
            splitted_path = self.metadata['datFileOrig'].split('/')[self.metadata['datFileOrig'].split('/').index(self.metadata['machine']) + 1:]
            if len(splitted_path) == 5 or len(splitted_path) == 6:
                self.metadata['clusterBaseUnit'] = splitted_path[0].title()
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
        fname_parts = os.path.splitext(os.path.basename(self.metadata['datFileOrig']))[0].split('_')
        if len(fname_parts) == 4:
            self.metadata['clusterBaseUnitNumberStart'] = fname_parts[2].split('-')[0]
            self.metadata['clusterBaseUnitNumberEnd'] = fname_parts[2].split('-')[-1]
            self.metadata['trapTemp'] = int(fname_parts[3].split('K')[0])
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
        elif self.metadata['specType'] == 'pes' and self.metadata['clusterBaseUnit'] in ['H2O', 'D2O']:
            self.metadata['specTypeClass'] = 'specPeWater'
        else:
            self.metadata['specTypeClass'] = classtype_map[self.metadata['specType']]























#
#
#
#def cleanup_raw_files(mdata, rawDataArchiveDir):
#    """Move raw data file(s) *.dat (and *.cfg) to raw data archive.
#    Update mdata with file location.
#    
#    Returns: dictionary."""
#    os.rename(mdata['datFile'],
#              os.path.join(rawDataArchiveDir, mdata['datFileName']))
#    del mdata['datFile']
#    del mdata['daFileDir']
#    mdata['rawDataArchiveDir'] = rawDataArchiveDir
#    
#    if 'cfgFileName' in mdata:
#        os.rename(os.path.join(mdata['cfgFileDir'], mdata['cfgFileName']),
#                  os.path.join(rawDataArchiveDir, mdata['cfgFileName']))
#        del mdata['cfgFileDir']
#        
#    return mdata
#
#
#def is_numeric(string):
#    """Return 'int' or 'float', if string can be converted, else raise
#    ValueError exception'.
#    
#    Returns: string."""
#    try:
#        int(string)
#        return 'int'
#    except ValueError:
#        pass
#    try:
#        float(string)
#        return 'float'
#    except ValueError:
#        pass
#
#
#def fix_number_type(mdata):
#    """Convert strings which represent numbers to int or float.
#    
#    Returns: dictionary."""
#    for k,v in mdata.iteritems():
#        if type(v) == str and is_numeric(v) == 'int':
#            mdata[k] = int(v)
#        elif type(v) == str and is_numeric(v) == 'float':
#            mdata[k] = float(v)
#            
#    return mdata
#
#
#def write_data_file(mdata, data_dir, spectrum, fileVersion = 0.1):
#    dataFileName = str(mdata['recTime'].tm_year) + '_' + \
#    str(mdata['recTime'].tm_mon) + '_' + \
#    str(mdata['recTime'].tm_mday) + '-' + \
#    str(mdata['recTime'].tm_hour) + '_' + \
#    str(mdata['recTime'].tm_min) + '_' + \
#    str(mdata['recTime'].tm_sec) + '.dat'
#    mdata['dataFileName'] = dataFileName
#    mdata['dataFileDir'] = os.path.join(data_dir,
#                                           str(mdata['recTime'].tm_year))
#    mdata['dataFile'] = os.path.join(mdata['dataFileDir'], dataFileName)
#   
#    with open(mdata['dataFile'], "w") as f:
#        f.write('# ClusterBib spectrum file, v. ' + str(fileVersion) + '\n')
#        f.write('#\n')
#        f.write('########## begin mdata ##########\n')
#        # reduce mdata
#        mdata['recTime'] = time.strftime("%d %b %Y %H:%M:%S",
#                                                  mdata['recTime'])
#        for key, value in mdata.iteritems():
#            f.write('# ' + key + ' = ' + str(value) + ' ' +
#                    str(type(value)) + '\n')
#            f.write('########## end mdata ##########\n')
#            for line in spectrum:
#                f.write(str(line) + '\n')
#                
#    mdata['recTime'] = time.strptime(mdata['recTime'],
#                                              "%d %b %Y %H:%M:%S")
#    return mdata
#
#def write_pickle_file(mdata, pickle_dir):
#    '''
#    Stores the mdata dict in a pickle file under the path:
#    pickle_dir/<year>/<dat_time>.pickle
#    
#    @param mdata:
#    @param pickle_dir:
#    '''
#    pickle_file_name = str(mdata['recTime'].tm_year) + '_' + \
#    str(mdata['recTime'].tm_mon) + '_' +\
#    str(mdata['recTime'].tm_mday) + '-' + \
#    str(mdata['recTime'].tm_hour) + '_' + \
#    str(mdata['recTime'].tm_min) + '_' + \
#    str(mdata['recTime'].tm_sec) + '.pickle'
#    mdata['pickleFileName'] = pickle_file_name
#    mdata['pickleFileDir'] = os.path.join(pickle_dir,
#                                             str(mdata['recTime'].tm_year))
#    mdata['pickleFile'] = os.path.join(mdata['pickleFileDir'],
#                                          pickle_file_name)
#    if not os.path.exists(mdata['pickleFileDir']):
#        os.makedirs(mdata['pickleFileDir'])
#    with open(mdata['pickleFile'], 'wb') as f:
#        pickle.dump(mdata, f)
#
#
#class LegacyImport(object):
#    def __init__(self, dat_file_name, dat_file_dir, common_values,
#                 pickle_dir = '../rawdata/data',
#                 archive_dir = '../rawdata/archive'):
#        datfile = os.path.join(dat_file_dir, dat_file_name)
#        try:
#            with open(datfile) as f:
#                raw_mdata, spectrum = strip_file(f)
#            mdata = eval_dat_file(raw_mdata, spectrum)
#            mdata = mdata_basics(dat_file_name, dat_file_dir, mdata)
#            if mdata['specType'] == 'pes':
#                mdata = verify_recTime(mdata)
#                mdata = find_cfgfile(mdata['datFileName'],mdata['datFileDir'], mdata)
#                if 'cfgFileName' in mdata:
#                    mdata = parse_cfgfile(mdata['cfgFileName'],mdata['cfgFileDir'], mdata)
#            mdata = parse_dir_structure(mdata)
#            mdata = set_common_values(mdata, common_values)
#            mdata = complete_mdata(mdata)
#            mdata['spectrum'] = spectrum
#            mdata = fix_number_type(mdata)
#            write_pickle_file(mdata, os.path.abspath(pickle_dir))
#            self.data = mdata
#        except:
#            print 'Import of ' + dat_file_name + ' failed.'
#
#
#
#
#
#
#if __name__ == "__main__":
#    dat_file_name='040304_57.dat'
#    dat_file_dir='/home/kiran/python/ClusterBib/rawdata'
#        
#    mdata = mdata_basics(dat_file_name, dat_file_dir)
#    raw_mdata, spectrum = strip_file(mdata['datFile'])
#    mdata = eval_dat_file(raw_mdata, mdata)
#    mdata = find_cfgfile(mdata['datFileName'], 
#                             mdata['datFileDir'], mdata)
#    if 'cfgFileName' in mdata:
#        mdata = parse_cfgfile(mdata['cfgFileName'],
#                                  mdata['cfgFileDir'], mdata)
#    mdata = complete_mdata(mdata)
#    mdata['spectrum'] = spectrum
#    mdata = fix_number_type(mdata)
#    write_pickle_file(mdata, '../rawdata/data')
#    
#    
#    