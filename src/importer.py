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
#sys.path.append(os.path.normpath(os.path.join(os.getcwd(), '../../delay/src')))
from filestorage import load_xml, load_pickle, load_json
#import config
from abc import ABCMeta, abstractmethod




'''
#######################################################
# Class importer
# This is a class defining the interface all classes 
# used in ._-+=Clusis=+-_. for importing a single file 
# containing measurement data need to implement,
# and contains some useful functions
#######################################################
'''
class importer():
    
    '''
#######################################################
# Obviously a constructor,
# it needs to know 
#   - which fileToImport 
#   - a configuration object
#   - a spectrumtype spectype
#######################################################'''
    def __init__(self, fileToImport, cfg, spectype=None, commonMdata={}):
        if spectype in cfg.mdata_ref['spec']['specType'][0]:
            print('Got valid spectype: {}'.format(spectype))
            self.spectype = spectype
        else:
            raise ValueError('Unknown spectype: {}'.format(spectype))
        self.datfile_orig = os.path.abspath(fileToImport)

        self.metadata = cfg.get_metadata()
        self.metadata['specType'] = self.spectype

        self.cfg = cfg
        self.header = []
        self.data = []
    

    '''    
#######################################################
# add a sha1 hash of the current File 
# to self.metadata['sha1']
#
#######################################################
    '''
    def get_sha1(self):
        with open(self.metadata['datFileOrig'], 'rb') as f:
            sha1 = hashlib.sha1(f.read()).hexdigest()
        
        self.metadata['sha1'] = sha1
 

    '''
#######################################################
# extract a timestamp 
# from the current file
#
#######################################################
    '''
    def get_recTime(self, spectype):
        '''
        Checks the recording time from time stamp against filename. 
        pes, ms data files only (for now).
        '''
        timeStamp = os.stat(self.metadata['datFileOrig']).st_mtime        
        if spectype in ['generic', 'ms', 'tof']:
            self.metadata['recTime'] = timeStamp
            

#######################################################
# parse the current file
#
#
####################################################### 
    def parse_file(self, fileToImport):
        """Reads from a file and generates a header list and a data
        ndarray.
        """
        try:
            with open(fileToImport) as f:
                for line in f:
                    self.parse_line(line)
        except IOError as e:
            print('Reading ' + fileToImport + ' failed.')
            print("I/O error({0}): {1}".format(e.errno, e.strerror))
        else:
            self.data = np.array(self.data[:-1]) # last point has sometimes a strange value like 32768. Skip it!


#######################################################
#
# parsing the file on a line to line level
#
#######################################################                      
    def parse_line(self,line):
        if re.search('^-{0,1}\d+.{0,1}\d*$',line.strip()) == None: # line contains data other than a numbers, thus supposedly its part of a header
            self.header.extend(line.split())
        elif re.search('^-{0,1}\d+.{0,1}\d*[e|E]{0,1}-{0,1}\d*$',line.strip()):
            self.data.append(float(line.strip()))
    
    
    @abstractmethod    
    def set_metadata_from_config(self):
        pass
