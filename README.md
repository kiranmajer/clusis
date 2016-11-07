# clusis
A python framework for a cluster spectra information system.

# Prerequisites
python 3
matplotlib

# Usage

from load import *
from initcdb import *
create config with path to write to
e.g. cfg = init_cludb(outpath, outfolder)

then read data, e.g.
(spectype is important!!)
import_rawdata_3f(cfg, ls("/home/simond/Documents/measurements/MobileQuelle/capacitor_masspecs/hvamp/massspecs"),spectype="ms")
from speclist_3f import *
get list: l = SpecMList(cfg)
 get spec :s= get_spec()

# usage

from load import *
from initcdb import *
create config with path to write to
e.g. cfg = config_3f.Cfg3f(outpath, outfolder)
cfg = config_3f.Cfg3f("/home/simond/Documents/measurements/clusisdata", "tes")
initialize Db from config
init_cludb(cfg)



then read data, e.g.
(spectype is important!!)
import_rawdata_3f(cfg, ls("/home/simond/Documents/measurements/MobileQuelle/capacitor_masspecs/hvamp/massspecs"),spectype="ms")
from speclist_3f import *
get list: l = SpecMList(cfg)
 get spec :s= get_spec()


from load import *
from initcdb import *
from config_casi import *
casi_cfg = CfgCasi("/home/simond/Documents/measurements/clusisdata", "casi")
init_cludb(casi_cfg)
import_rawdata(casi_cfg, ls("/tmp/testdata/casi/ag/",suffix=".dat", recursive=True),commonMdata = {'waveLength' : 590e-9, 'clusterBaseUnitNumberEnd' : 100 , 'clusterBaseUnitNumberStart' : 1 , 'clusterDopantMass' : 16})


# read from database
from load import *
from initcdb import *
from config_3f import *
cfg = config_3f.Cfg3f("/home/simond/Documents/measurements/clusisdata", "trd")
