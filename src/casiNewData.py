import numpy as np
from hashlib import sha1
from os.path import splitext,abspath
from os import stat

class CasiNewData():
    def __init__(self, datafile_path):
        self.xdata, self.ydata = self.read_data(self.datafile_path)
        self.metadata = {'datFileOrig': abspath(datafile_path),
                         'tags': [],
                         'systemTags': [],
                         'userTags': [],
                         'evalTags': [],
                         'machine': 'casi',
                         'delayState': {},
                         'info': ''}


    def read_data(self, datafile_path):
        x,y = np.loadtxt(datafile_path,
                         converters={0: lambda i: float(i.decode('utf').replace(',','.'))},
                         unpack=True)
        
        return x,y
    
    
    def parse_filename(self, fname):
        y, m, d, element, idx, data_type = splitext(fname)[0].split('_')
        
        return int(y), int(m), int(d), element, int(idx), data_type
    
    
    def get_rectime(self, datafile_path):
        time_stamp = stat(datafile_path).st_mtime
        
        return time_stamp
    
    
    def get_sha1(self, datafile_path):
        with open(datafile_path, 'rb') as f:
            cksum = sha1(f.read()).hexdigest()
        
        return cksum
