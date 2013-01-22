import glob
import numpy as np
import os
#import pickle
import re
import time
import hashlib
import MdataUtils
#import config



class LegacyData(object):
    
    def __init__(self, fileToImport, cfg, commonMdata={}, machine='casi'):
        self.metadata = {'datFileOrig': os.path.abspath(fileToImport),
                         'tags': [],
                         'machine': machine}
        self.cfg = cfg
        self.header = []
        self.data = []
        
        
        self.parseFile(fileToImport)
        self.evalHeader()
        self.addSha1()
        self.getRecTime()
        self.mdataBasics()
        self.evalCfgFile()
        self.parseDirStructure()
        # convert metadata to Mdata object
        self.mdata = MdataUtils.Mdata(self.metadata, self.cfg)
        if len(commonMdata) > 0:
            #print 'Importing commonMdata', commonMdata
            self.mdata.add(commonMdata)
        self.mdata.checkIfComplete()
    
    def parseFile(self, fileToImport):
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
            
    def evalHeader(self, min_line_count=250):
        """Checks and makes a very basic analysis of header for key words:
            'Wellenlaenge:' -> pes
            'Trigger_Offset[s]' -> ms
        """
        
        if 'Wellenlaenge:' in self.header and len(self.data) > min_line_count:
            '''TODO: adapt for more machines'''
            self.metadata['specType'] = 'pes'
            for k,v in self.cfg.defaults[self.metadata['machine']]['pes'].items():
                if k not in list(self.metadata.keys()):
                    self.metadata[k] = v
        elif 'Trigger_Offset[s]' in self.header and len(self.data) > min_line_count:
            self.metadata['specType'] = 'ms'
            if self.header[1] == 'Trigger_Offset[s]':
                self.metadata['triggerOffset'] = float(self.header[0])
            if self.header[3] == 'Zeit_pro_Punkt[s]':
                self.metadata['timePerPoint'] = float(self.header[2])
            if self.header[5] == 'Eichmasse':
                self.metadata['referenceMass'] = float(self.header[4])
            if self.header[7] == 'Eichzeit[s]':
                self.metadata['referenceTime'] = float(self.header[6])
            if self.header[9] == 'Time_Offset[s]':
                self.metadata['timeOffset'] = float(self.header[8])
        else:
            raise ValueError('%s: Not a valid data file.'%self.metadata['datFileOrig'])
    
        
        
    def addSha1(self):
        with open(self.metadata['datFileOrig'], 'rb') as f:
            sha1 = hashlib.sha1(f.read()).hexdigest()
        
        self.metadata['sha1'] = sha1
    
    
    def getRecTime(self):
        '''
        Checks the recording time from time stamp against filename. 
        pes, ms data files only (for now).
        '''
        datFileName = os.path.basename(self.metadata['datFileOrig'])
        if self.metadata['specType'] == 'pes':
            pattern_groups = re.compile(r'(^\d{2})(\d{2})(\d{2})_')
            day, month, year = pattern_groups.search(datFileName).groups()
            if int(year) < 80: 
                year = 2000 + int(year)
            else:
                year = 1900 + int(year)
        elif self.metadata['specType'] == 'ms':
            pattern_groups = re.compile(r'(^\d{4})(\d{2})(\d{2})_')
            year, month, day = pattern_groups.search(datFileName).groups()
            
        timeStamp = os.stat(self.metadata['datFileOrig']).st_mtime
        if self.metadata['specType'] in ['pes', 'ms']:
            startDate = '%s %s %s' % (day, month, year)
            dayStarts = time.mktime(time.strptime(startDate, '%d %m %Y'))
            dayEnds = dayStarts + 86400
            if dayStarts <= timeStamp <= dayEnds:
                self.metadata['recTime'] = timeStamp
            else:
                self.metadata['recTime'] = dayStarts
                self.metadata['tags'].append('Import warning: Invalid time stamp')
                print('Warning: %s has invalid time stamp. Got recTime from filename.' % (datFileName))
        else:
            self.metadata['recTime'] = timeStamp

    
    
    def mdataBasics(self):
        """Adds to the mdata dictionary some basic data: 
           tags, recTime ...
        """
        self.metadata['datFile'] = os.path.join(self.cfg.path['archive'],
                                                self.metadata['machine'],
                                                os.path.basename(self.metadata['datFileOrig']))
        #self.metadata['tags'] = []
        ''' build pickle file name and path according following scheme:
        config.path['data']/<year>/<recTime>_<sha1>.pickle'''
        y = str(time.localtime(self.metadata['recTime']).tm_year)
        m = str(time.localtime(self.metadata['recTime']).tm_mon)
        d = str(time.localtime(self.metadata['recTime']).tm_mday)
        pickleFileName = '%s-%s-%s_%s.pickle' % (y,m,d,self.metadata['sha1'])
        pickleFileDir = os.path.join(self.cfg.path['data'], y)
        self.metadata['pickleFile'] = os.path.join(pickleFileDir, pickleFileName)


    def findCfgFile(self):
        """Gets the date and number out of the pes dat filename and searches
        for the associated cfg file: *ddmmyy_nn.cfg. Or searches for a cfg
        file with the same basename as the ms dat file.
        """
        dat_file_name = os.path.basename(self.metadata['datFileOrig'])
        dat_file_dir = os.path.dirname(self.metadata['datFileOrig'])
        if self.metadata['specType'] == 'pes':
            pattern_groups = re.compile(r'(\d{6})_(\d+)')
            dat_fileDate, dat_fileNumber = pattern_groups.search(dat_file_name).groups()
            cfg_file = glob.glob(os.path.join(dat_file_dir,'*' + '_' + 
                                              dat_fileNumber + '_' + dat_fileDate 
                                              + '.cfg'))
            if len(cfg_file) == 0:
                cfg_file = glob.glob(os.path.join(dat_file_dir,'*' + dat_fileDate 
                                                  + '_' + dat_fileNumber + '.cfg'))
        elif self.metadata['specType'] == 'ms':
            dat_fileShortname = os.path.splitext(dat_file_name)[0]
            cfg_file = glob.glob(os.path.join(dat_file_dir, dat_fileShortname + '.cfg'))
        else:
            raise ValueError('No specType specified.')
            
        if len(cfg_file) == 1:
            self.metadata['cfgFileOrig'] = cfg_file[0]
        elif len(cfg_file) == 0:
            raise ValueError('Could not find cfg file.')
        else:
            self.metadata['tags'].append('Several cfg files: ' + str(cfg_file))
            raise ValueError('Found more than 1 cfg file.')
     
    
    def parseCfgFile(self, cfg_file):
        """Extracts all information of cfg_file and its filename.
        """
        cfg_data_map = ['ch1Tstart', 'ch1Tstop', 'ch2Tstart', 'ch2Tstop',
                        'ch3Tstart', 'ch3Tstop', 'ch4Tstart', 'ch4Tstop',
                        'ch5Tstart', 'ch5Tstop', 'ch6Tstart', 'ch6Tstop',
                        'ch7Tstart', 'ch7Tstop', 'ch8Tstart', 'ch8Tstop',
                        'clusterBaseUnitNumber']
        try:
            with open(cfg_file) as cfg:
                cfg_data = cfg.readlines()[0].split()
        except IOError as e:
            print("I/O error({0}): {1}".format(e.errno, e.strerror))
        else: # cfg file exist and is readable
            if len(cfg_data) == 17: # normal case
                try:
                    for i in range(len(cfg_data)-1):
                        self.metadata[cfg_data_map[i]] = int(cfg_data[i]) * 20e-9
                except:
                    raise
                else:
                    self.metadata[cfg_data_map[-1]] = int(cfg_data[-1])
            elif len(cfg_data) == 1: # sometimes it contain only the cluster size
                self.metadata[cfg_data_map[-1]] = int(cfg_data[-1])
            else:
                raise ValueError(cfg_file + ' does not contain valid data.')
                    
            """Get information from file name
            """
            cfg_file_name_map = ['clusterBaseUnit', 'clusterBaseUnitNumber',
                          'cfgFileNumber', 'cfgFileDate.cfg']
            cfg_file_name = os.path.basename(self.metadata['cfgFileOrig'])
            if len(cfg_file_name.split('_')) == 4:
                cfg_file_nameData = dict([(cfg_file_name_map[i], cfg_file_name.split('_')[i])
                                          for i in range(len(cfg_file_name_map))])
                self.metadata['clusterBaseUnit'] = cfg_file_nameData['clusterBaseUnit']
                """Test if cluster size in file and file name differs"""
                if self.metadata['clusterBaseUnitNumber'] != int(cfg_file_nameData['clusterBaseUnitNumber']):
                    self.metadata['clusterBaseUnitNumberFromFileName'] = int(cfg_file_nameData['clusterBaseUnitNumber'])
                    self.metadata['tags'].append('clusterBaseUnitNumber ambiguous')
            else:
                raise ValueError('Unexpected file name: ' + cfg_file_name)

    
    def evalCfgFile(self):
        """Tries to find corresponding cfg files and adds unambiguous data to mdata
        """
        try:
            self.findCfgFile()
            self.parseCfgFile(self.metadata['cfgFileOrig'])
        except:
            raise #ValueError('Importing cfg file failed.')
        else:
            self.metadata['cfgFile'] = os.path.join(self.cfg.path['archive'],
                                                    self.metadata['machine'],
                                                    os.path.basename(self.metadata['cfgFileOrig']))
    
    
    def parseDirStructure(self):
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
                self.metadata['specType'] = splitted_path[3]
                if len(splitted_path) == 6 and splitted_path[4].replace('_', ' ') not in self.metadata['tags']:
                    self.metadata['tags'].append(splitted_path[4].replace('_', ' '))




      























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
#                mdata = find_cfg_file(mdata['datFileName'],mdata['datFileDir'], mdata)
#                if 'cfgFileName' in mdata:
#                    mdata = parse_cfg_file(mdata['cfgFileName'],mdata['cfgFileDir'], mdata)
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
#    mdata = find_cfg_file(mdata['datFileName'], 
#                             mdata['datFileDir'], mdata)
#    if 'cfgFileName' in mdata:
#        mdata = parse_cfg_file(mdata['cfgFileName'],
#                                  mdata['cfgFileDir'], mdata)
#    mdata = complete_mdata(mdata)
#    mdata['spectrum'] = spectrum
#    mdata = fix_number_type(mdata)
#    write_pickle_file(mdata, '../rawdata/data')
#    
#    
#    