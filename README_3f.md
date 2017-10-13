# clusis
A python framework for a cluster spectra information system.

# Prerequisites
python 3
matplotlib

# Usage

create config with path to write to

from initcdb import *
cfg = init_cludb("/home/simond/Documents/measurements/clusisdata","test")

# import raw data, e.g.
import_rawdata_3f(cfg, ls("/home/simond/Documents/measurements/MobileQuelle/capacitor_masspecs/hvamp/tofs"),spectype="tof", commonMdata={'deflectorVoltage' : 55 , 'ionType' : '-'})

# list mass spectra
ml=SpecMList(cfg)

# list tof spectra
tl=SpecTofList(cfg)