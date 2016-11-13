import glob
import numpy as np
import os
import re
import time
import hashlib
from mdata import Mdata
import sys



'''
#############################
# Parse the content of a file
# created with Picoscope
#############################'''
def parse_picoscope(fileToImport):
    """Reads from a file and generates a header list and a data
    ndarray.
    """
    try:
        with open(fileToImport) as f:
            ''' 
                The head of picoscope datafile looks like this:

                Time,Channel A,Channel B,Invert A
                (ms),(V),(V),(V)

                therefore the reading
            '''
            column_name=f.readline().strip('\n').split(',')
            column_unit=f.readline().strip('\n').split(',')
    except IOError as e:
        print('Reading ' + fileToImport + ' failed.')
        print("I/O error({0}): {1}".format(e.errno, e.strerror))

    ''' Use numpy readin'''
    spec_data = np.genfromtxt(fileToImport, skip_header=2, delimiter=',', unpack=True)

    ''' Factor to convert to SI units'''
    si_factor = {'s': 1,
                 'ms': 1e-3,
                 'us': 1e-6,
                 'ns': 1e-9,
                 'V': 1,
                 'mV': 1e-3,
                }
    column_unit=[u.lstrip('(').rstrip(')') for u in column_unit]

    data_t = spec_data[column_name.index('Time')]*si_factor[column_unit[column_name.index('Time')]]
    data_ch1 = spec_data[column_name.index('Channel A')]*si_factor[column_unit[column_name.index('Channel A')]]
    data_ch2 = spec_data[column_name.index('Channel B')]*si_factor[column_unit[column_name.index('Channel B')]]
    return [data_t,data_ch1,data_ch2]