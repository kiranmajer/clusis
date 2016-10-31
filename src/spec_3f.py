#from legacyData import *
import scipy.constants as constants
import numpy as np
from mdata import Mdata
import os.path
#from plotlibs import *
from dbshell import Db
#from recursive_import import *
#from pes_sheet import *
#from msplot import *
from scipy.optimize import leastsq
#from ase.atoms import Atoms
import view
import view_3f
import pickle
import load





class Spec(object):
    def __init__(self, mdata, xdata, ydata, cfg):
        self.mdata_ref = cfg.mdata_ref['spec'].copy()
        self.mdata = Mdata(mdata, self.mdata_ref, cfg.mdata_systemtags)
        self.xdata = xdata
        self.ydata = ydata
        self.cfg = cfg
        self.view = view.View(self)
        
#     def __del__(self):
#         print('Commiting ...')
#         self.commit()
#         print('before deleting spec object.')
        
    
    def _update_mdata_reference(self, specTypeClass):
        'Adapts mdata reference to the spec type class'
        self.mdata_ref.update(self.cfg.mdata_ref[specTypeClass])
        
    
    def _commit_db(self, update=True):
        with Db(self.mdata.data('machine'), self.cfg) as db:
            db.add(self, update=update)
        
        
    def _commit_pickle(self):
        '''
        Stores the self.mdata.data(), self.xdata, self.ydata dicts in a pickle file under the path:
        config.path['data']/<year>/<recTime>_<sha1>.pickle
        '''
        pickleFile = os.path.join(self.cfg.path['base'], self.mdata.data('pickleFile'))
        pickleDir = os.path.dirname(pickleFile)
        if not os.path.exists(pickleDir):
            os.makedirs(pickleDir)   
        with open(pickleFile, 'wb') as f:
            pickle.dump((self.mdata.data(), self.xdata, self.ydata), f)
            
            
    def commit(self, update=True):
        self._commit_pickle()
        self._commit_db(update=update)
        
    def _auto_key_selection(self, xdata_key, ydata_key, key_deps):
        #print('Searching for valid keys ...')
        def auto_xkey(key_deps):
            k_gauged = [i for i in key_deps.keys() if 'Gauged' in i]
            if 'gauged' in self.mdata.data('systemTags') and len(k_gauged) > 0:
                auto_x = k_gauged[0]
            else:
                auto_x = [i for i in key_deps.keys() if 'Gauged' not in i][0]
            return auto_x
        
        def auto_ykey(key_deps, xdata_key):
            k_sub = [i for i in key_deps[xdata_key] if 'Sub' in i]
            if 'subtracted' in self.mdata.data('systemTags') and len(k_sub) > 0:
                auto_y = k_sub[0]
            else:
                ydata_key_list = [i for i in key_deps[xdata_key] if 'Sub' not in i]
                ydata_key_list.reverse()
                auto_y =  ydata_key_list.pop()
                while auto_y not in self.ydata.keys():
                    auto_y =  ydata_key_list.pop()
            return auto_y
        
        if xdata_key in ['auto']:
            xdata_key = auto_xkey(key_deps)
        elif xdata_key not in key_deps.keys():
            raise ValueError("xdata_key must be one of: {}.".format(str(key_deps.keys())[11:-2]))
        if ydata_key in ['auto']:
            ydata_key = auto_ykey(key_deps, xdata_key)
        elif ydata_key not in key_deps[xdata_key]:
            raise ValueError("""ydata_key must be one of: {}.""".format(str(key_deps[xdata_key])[1:-1]))
        return xdata_key, ydata_key        

        
    def _idx2time(self, idx, time_per_point, trigger_offset, time_offset=0):
        #self.xdata['tof'] = self.xdata['idx']*self.mdata.data('timePerPoint')-self.mdata.data('triggerOffset')-time_offset
        return idx*time_per_point - trigger_offset - time_offset
    
    def _calc_time_data(self, time_data_key='tof', time_offset=0):
#         print('>>> _calc_time_data <<<')
        self.xdata[time_data_key] = self._idx2time(idx=self.xdata['idx'],
                                                   time_per_point=self.mdata.data('timePerPoint'),
                                                   trigger_offset=self.mdata.data('triggerOffset'),
                                                   time_offset=time_offset)
#         print(self.xdata[time_data_key])

    def _photon_energy(self, waveLength):
        """
        Calculates photon energy in eV for a given wave length.
        """
        return constants.h*constants.c/(constants.e*waveLength)

    def _set_neg_int_zero(self, int_data):
        return (int_data + np.abs(int_data))/2
    
    def _calc_fixed_intensities(self, int_key='rawIntensity', new_int_key='intensity'):
        """
        The Oscilloscope sets the value for bins without counts to the value of the frame of display.
        So it's safe to set them to 0. 
        """
        self.ydata[new_int_key] = self._set_neg_int_zero(self.ydata[int_key])
        
        
    def calc_spec_data(self):
        self._calc_time_data()
        self._calc_fixed_intensities()
    
#    def _subtract_intensities(self, background_spec):
#        self.ydata['intensitySubRaw'] = self.ydata['intensity'] - background_spec.ydata['intensity']
#        self._fix_neg_intensities('intensitySubRaw', 'intensitySub')
    
    def subtract_bg(self, bgFile, isUpDown=False):
        '''
        Subtracts one ydata-vector from another.
        
        Warning: This implies, that the corresponding xdata of both data sets has the 
        same gauge factors, that means the same toff, lscale, Eoff, trigger_offset,
        time_per_point etc.
        This is usually given, when spectra are measured in a time range, where one would
        apply the same gauge reference.
        
        In all other cases one needs to adjust both xdata and ydata sets to match a common 
        time range before subtraction! This is NOT covert by this method. 
        '''
        bgSpec = load.load_pickle(self.cfg, bgFile)
        if not self.mdata.data('specTypeClass') == bgSpec.mdata.data('specTypeClass'):
            raise ValueError('Background file has different spec type class.')
        self.mdata.update({'subtractBgRef': bgSpec.mdata.data('pickleFile')})
        bgSpec.mdata.update({'subtractBgRef': self.mdata.data('pickleFile')})
        bgSpec.mdata.add_tag('background', tagkey='systemTags')
        if isUpDown:
            bgSpec.mdata.add_tag('up/down', tagkey='systemTags')
            self.mdata.add_tag('up/down', tagkey='systemTags')
        # subtract background
        #self._subtract_intensities(bgSpec)
        self.ydata['intensitySubRaw'] = self.ydata['intensity'] - bgSpec.ydata['intensity']
        self._calc_fixed_intensities('intensitySubRaw', 'intensitySub')        
        self.mdata.add_tag('subtracted', tagkey='systemTags')
        self.commit()
        bgSpec.commit()
        
    def trash(self, reason):
        reason = str(reason)
        self.mdata.add_tag('trash', 'systemTags')
        self.mdata.update({'info': reason})
        
    def remove(self):
        # collect associated files
        fk = [k for k in self.mdata.data().keys() if 'File' in k]
        files = []
        for f in fk:
            files.append(os.path.join(self.cfg.path['base'], self.mdata.data(f)))
        'TODO: handle more securely.'
        for f in files:
            try:
                os.remove(f)
            except FileNotFoundError:
                print('\nWarning: {} does not exist.\n')
            except:
                print('\n##################\nRemoving of {} failed. Please remove manually.'.format(f))
                raise
        # remove db entry
        sha1 = self.mdata.data('sha1')
        tablename = self.mdata.data('specType')
        with Db(self.mdata.data('machine'), self.cfg) as db:
            db.remove(sha1, tablename)


        

class SpecTof(Spec):
    def __init__(self, mdata, xdata, ydata, cfg):
        #print('__init__: Init SpecPe')
        Spec.__init__(self, mdata, xdata, ydata, cfg)
        self._update_mdata_reference('specTof')
        #print 'Assigning view.ViewPes'
        self.view = view_3f.ViewTof(self)
     
class SpecMs(Spec):
    def __init__(self, mdata, xdata, ydata, cfg):
        print('__init__: Init SpecMs')
        Spec.__init__(self, mdata, xdata, ydata, cfg)
        self._update_mdata_reference('specMs')
        self.view = view_3f.ViewMs(self)
        


