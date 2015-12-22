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


        

class SpecPe(Spec):
    def __init__(self, mdata, xdata, ydata, cfg):
        #print('__init__: Init SpecPe')
        Spec.__init__(self, mdata, xdata, ydata, cfg)
        self._update_mdata_reference('specPe')
        self._pFactor = constants.m_e/(2*constants.e)*(self.mdata.data('flightLength'))**2
        self._hv = self._photon_energy(self.mdata.data('waveLength'))
        if len(self.xdata) == 1:
            self.calc_spec_data()
        #print 'Assigning view.ViewPes'
        self.view = view.ViewPes(self)
        
#     def __del__(self):
#         Spec.__del__(self)
#         print('Deleting SpecPe-object')
    
    # basic methods    
    def _idx2time(self, idx, time_per_point, trigger_offset, lscale, Eoff, toff):
        #return 1/np.sqrt(lscale*(1/(idx*time_per_point - trigger_offset)**2 - Eoff/self._pFactor)) - toff
        ta = 1/np.sqrt(lscale*(1/(idx*time_per_point - trigger_offset)**2 - Eoff/self._pFactor)) - toff
        #print('maximum in time array:', np.nanmax(ta))
        hasNaNs = np.isnan(ta) # check for NaNs introduced by gauging with high Eoff
        ta[hasNaNs] = np.nanmax(ta) # setting all NaNs to maximum valid time
        return ta
        
        #return 1/np.sqrt(1/(lscale*(idx*time_per_point - trigger_offset + toff)**2) - Eoff/self._pFactor)
    
    def ekin(self, t):  #, lscale, Eoff, toff):
        return self._pFactor/t**2
        #return self._pFactor/(lscale**2*(t + toff)**2) - Eoff
        #return self._hv - self.ebin(t, gauge_scale, gauge_offset)
        
    def ebin(self, t):  #, lscale, Eoff, toff):
        return self._hv - self.ekin(t)
        #return self._hv - (self._pFactor/(lscale**2*(t + toff)**2) - Eoff)
        #return (self._hv-self._pFactor/t**2 - gauge_offset)/gauge_scale
        
    def jtrans(self, intensity, t):
        return intensity*t**3/(2*self._pFactor)
    
    def jtrans_inv(self, intensity, t):
        return intensity*2*self._pFactor/t**3
        
    # recursive methods        
    def _calc_time_data(self, timedata_key, lscale, Eoff, toff):
        self.xdata[timedata_key] = self._idx2time(idx=self.xdata['idx'],
                                                  time_per_point=self.mdata.data('timePerPoint'),
                                                  trigger_offset=self.mdata.data('triggerOffset'),
                                                  lscale=lscale,
                                                  Eoff=Eoff,
                                                  toff=toff)           
    
    def _calc_ekin(self, new_key, timedata_key):  #, lscale, Eoff, toff):
        self.xdata[new_key] = self.ekin(self.xdata[timedata_key])  #, lscale, Eoff, toff) 
        #self.xdata['ekin'] = constants.m_e/(2*constants.e)*(self.mdata.data('flightLength')/self.xdata['tof'])**2
    
    def _calc_ebin(self, new_key, timedata_key):  #, lscale, Eoff, toff):
        self.xdata[new_key] = self.ebin(self.xdata[timedata_key])  #, lscale, Eoff, toff)
        #self.xdata['ebin'] = self._photon_energy(self.mdata.data('waveLength')) - self.xdata['ekin']
        
    def _calc_jacoby_intensity(self, new_key='jIntensity', intensity_key='intensity', timedata_key='tof'):
        self.ydata[new_key] = self.jtrans(self.ydata[intensity_key], self.xdata[timedata_key])
        #self.ydata[new_key] = self.ydata[ydataKey]/(2*self.xdata['ekin']/self.xdata['tof'])
        
#    def __calcEbinGauged(self):
#        self.xdata['ebinGauged'] = (self.xdata['ebin'] - self.mdata.data('gaugePar')['offset'])/self.mdata.data('gaugePar')['scale']
        
    
    def calc_spec_data(self, lscale_key='flightLengthScale', Eoff_key='energyOffset', toff_key='timeOffset'):
        'TODO: decide which data will be generated (e.g. now one generate the same data in tof and tofGauged)! '
        lscale = self.mdata.data(lscale_key)
        Eoff = self.mdata.data(Eoff_key)
        toff = self.mdata.data(toff_key)
        self._calc_time_data(timedata_key='tof', lscale=lscale, Eoff=Eoff, toff=toff)
        self._calc_ekin(new_key='ekin', timedata_key='tof')  #, lscale=lscale, Eoff=Eoff, toff=toff)
        self._calc_ebin(new_key='ebin', timedata_key='tof')  #, lscale=lscale, Eoff=Eoff, toff=toff)
        self._calc_fixed_intensities()
        self._calc_jacoby_intensity()
        
        
    def gauge(self, gaugeRef, ignore_wavelength=False):
        gaugeSpec = load.load_pickle(self.cfg, gaugeRef)
        if gaugeSpec.mdata.data('specTypeClass') not in ['specPePt']:
            raise ValueError('Gauge reference is not a Pt-spectrum.')
        if not gaugeSpec.mdata.data('waveLength') == self.mdata.data('waveLength') and not ignore_wavelength:
            raise ValueError('Gauge reference has different laser wavelength.')
        elif not gaugeSpec.mdata.data('waveLength') == self.mdata.data('waveLength') and ignore_wavelength:
            self.mdata.add_tag('gauge ref has different wave length')
        lscale = gaugeSpec.mdata.data('fitPar')[-1]
        toff = gaugeSpec.mdata.data('fitPar')[-2]
        Eoff = gaugeSpec.mdata.data('fitPar')[-3]
        self.mdata.update({'gaugeRef': gaugeSpec.mdata.data('pickleFile'),
                           'flightLengthScale': lscale,
                           'timeOffset': toff,
                           'energyOffset': Eoff})
        self.mdata.add_tag('gauged', 'systemTags')
        # calc xdata gauged
        self._calc_time_data(timedata_key='tofGauged', lscale=lscale, Eoff=Eoff, toff=toff)
        self._calc_ekin(new_key='ekinGauged', timedata_key='tofGauged')  #, lscale=lscale, Eoff=Eoff, toff=toff)
        self._calc_ebin(new_key='ebinGauged', timedata_key='tofGauged')  #, lscale=lscale, Eoff=Eoff, toff=toff)
        # calc ydata gauged
        self._calc_jacoby_intensity(new_key='jIntensityGauged',
                                    intensity_key='intensity', timedata_key='tofGauged')
        if 'subtracted' in self.mdata.data('systemTags'):
            self._calc_jacoby_intensity(new_key='jIntensityGaugedSub',
                                        intensity_key='intensitySub', timedata_key='tofGauged')
        self.commit()
        gaugeSpec.mdata.add_tag('gauge reference')
        gaugeSpec.commit()
        del gaugeSpec
        self._ea_changed_warning()
        
    def subtract_bg(self, bgFile, isUpDown=True):
        Spec.subtract_bg(self, bgFile, isUpDown=isUpDown)
        self._calc_jacoby_intensity(new_key='jIntensitySub', intensity_key='intensitySub')
        if 'gauged' in self.mdata.data('systemTags'):
            self._calc_jacoby_intensity(new_key='jIntensityGaugedSub',
                                        intensity_key='intensitySub', timedata_key='tofGauged')    
        self._commit_pickle()
        
    def _ea_changed_warning(self, reason='Gauging'):
        if 'electronAffinity' in self.mdata.data().keys():
            change_ea = None
            while change_ea not in ['y', 'n']:
                q = '{} may have changed the value of the electron affinity ({} eV). Adapt it?'.format(reason, self.mdata.data('electronAffinity'))
                change_ea = input(q)
            if change_ea == 'y':
                ea = None
                while type(ea) is not float: 
                    q = 'Insert new value (eV):'
                    ea = input(q)      
                self.mdata.update({'electronAffinity': ea})  
                
    def attach_comp_spec(self, comp_spec_id):
        if self.view.comp_spec_data:
            self.mdata.update({'compSpecs': {comp_spec_id: dict(self.view.comp_spec_data)}})
        else:
            raise ValueError('No spectrum added yet. Use one of the add_* methods to add one.')
        
    def remove_comp_spec(self, comp_spec_id):
        compspecs = self.mdata.data('compSpecs')
        del compspecs[comp_spec_id]
        self.mdata.update({'compSpecs': compspecs})
        
        
class SpecPePt(SpecPe):
    def __init__(self, mdata, xdata, ydata, cfg):
        SpecPe.__init__(self, mdata, xdata, ydata, cfg)
        self._update_mdata_reference('specPePt')
        self.view = view.ViewPt(self)
             
        
#    def __fit_peak_pos(self, peakPar):
#        return [p[0] for p in peakPar]
    
    
    def __fit_peakpos_trans(self, peakPar):
        return [np.sqrt(self._pFactor/(self._hv-p[0])) for p in peakPar]
    
#     def __fit_peakpos(self, peakPar):
#         return [p[0] for p in peakPar]
    
    
#    def __fit_par_init(self, peakPar, yscale, scale, offset):
#        l = [i for p in peakPar if p[0] for i in [p[1]*yscale,p[2]]]
#        l.extend([scale,offset])
#        #l.extend([scale,offset])
#        return np.array(l)


    def __fit_par0_trans(self, peakPar, yscale, Eoff, toff, lscale):
        l = [i for p in peakPar if p[0] for i in [p[1]*yscale,p[2]]]
        #l = [i for p in peakPar if p[0] for i in [self.jtrans_inv(p[1]*yscale, np.sqrt(self._pFactor/(self._hv-p[0]))),p[2]]]
        l.extend([Eoff, toff, lscale])
        #print(l)
        return np.array(l)
    
    
    def __get_y_scale(self, xdata, ydata, xcenter, xinterval):
        #print('xcenter:', xcenter)
        xlb = np.abs(xdata-(xcenter-xinterval/2)).argmin()
        xub = np.abs(xdata-(xcenter+xinterval/2)).argmin()
        #print('Calculated y_scale:', ydata[xlb:xub].max())
        return ydata[xlb:xub].max()
    
    
#    def multi_gauss(self, x, peak_pos, parList):
#        plist = list(parList)
#        xlist = list(peak_pos)
#        gauss = lambda x, m,A,sigma,scale,offset: A*np.exp(-(x-(scale*m+offset))**2/(2*sigma**2))
#        offset = plist.pop()
#        scale = plist.pop()
#        mgauss = 0
#        while len(plist) > 0:
#            sigma = plist.pop()
#            A = plist.pop()
#            m = xlist.pop()
#            mgauss += gauss(x, m, A, sigma, scale, offset)
#        return mgauss
    
    
#    def _gauss_trans(self, t,m,A,sigma,toff,Eoff,lscale):
        
    
    
    def _multi_gauss_trans(self, t, peak_pos, parList):
        '''
        Multiple Gauss at peak_pos with parameter from parList transformed into time domain
        '''
        plist = list(parList)
        xlist = list(peak_pos)
        # orig working version
        gaussTrans = lambda t,m,A,sigma,toff,Eoff,lscale: A*2*self._pFactor/(t)**3*np.exp(-(self._pFactor*(1/(1/np.sqrt(lscale*(1/t**2 - Eoff/self._pFactor)) - toff)**2 - 1/m**2))**2/(2*sigma**2))
        # replace q/m**2 by hv-m 
        #gaussTrans = lambda t,m,A,sigma,toff,Eoff,lscale: A*2*self._pFactor/(t)**3*np.exp(-(self._pFactor*(1/(1/np.sqrt(lscale*(1/t**2 - Eoff/self._pFactor)) - toff)**2 - (self._hv - m)))**2/(2*sigma**2))
        
        lscale =plist.pop()
        toff = plist.pop()
        Eoff = plist.pop()
        mgaussTrans = 0
        while len(plist) > 0:
            sigma = plist.pop()
            A = plist.pop()
            m = xlist.pop()
            #print('Calling gaussTrans ...')
            #gt = np.where(lscale*(1/t**2 - Eoff/self._pFactor) > 0, gaussTrans(t, m, A, sigma, toff, Eoff, lscale), 0.3)
            gt = gaussTrans(t, m, A, sigma, toff, Eoff, lscale)
            #print(gt)
            gt_fixed = np.nan_to_num(gt)
            mgaussTrans += gt_fixed
            #mgaussTrans += gaussTrans(t, m, A, sigma, toff, Eoff)
        return mgaussTrans
    
    
#    def __err_multi_gauss(self, p,x,y,peak_pos):
#        return self.multi_gauss(x, peak_pos, p)-y
    
    
    def __err_multi_gauss_trans(self, p,t,y,peak_pos, constrain_par, constrain):
        c_par = constrain_par # -1: lscale, -2: toff, -3: Eoff
        c = constrain
        if c[0]<p[c_par]<c[1]: # only allow fits with toff (47-5)ns +- 5ns
        #if 1.0<p[-1]<1.007: # limit effective flight length to a maximum +0.007% 
            return self._multi_gauss_trans(t, peak_pos, p)-y
        else:
            return 1e6
#        return self._multi_gauss_trans(t, peak_pos, p)-y
    
    
#    def __fit_multi_gauss(self, peakParRef, scale, offset, rel_y_min, cutoff):
#        xdata = self.xdata['ebin']
#        ydata = self.ydata['jIntensity']
#        if cutoff == None:
#            ebin_max = self.xdata['ebin'].max()
#        elif 0 < cutoff < self.xdata['ebin'].max():
#            ebin_max =cutoff
#        else:
#            raise ValueError('cutoff must be between 0 and %.2f'%(self.xdata['ebin'].max()))
#        peakPar = [p for p in peakParRef if p[0]<ebin_max and p[1]>rel_y_min]
#        fitValues = {'fitPeakPos': self.__fit_peak_pos(peakPar)}
#        xcenter = fitValues['fitPeakPos'][0]
#        yscale = self.__get_y_scale(xdata, ydata, xcenter, 0.2)
#        fitValues['fitPar0'] = self.__fit_par_init(peakPar, yscale, scale, offset)
#        p, covar, info, mess, ierr = leastsq(self.__err_mGauss, fitValues['fitPar0'],args=(xdata,ydata,fitValues['fitPeakPos']), full_output=True)
#        fitValues.update({'fitPar': p, 'fitCovar': covar, 'fitInfo': [info, mess, ierr]})
#        
#        return fitValues


    def __fit_multi_gauss_trans(self, xdata_key, ydata_key, peakParRef, Eoff, toff, lscale, rel_y_min, cutoff, constrain_par, constrain):
        xdata = self.xdata[xdata_key]
        ydata = self.ydata[ydata_key]
        constrain_par_map = {'lscale': -1, 'toff': -2,'Eoff': -3}
        if cutoff == None:
            'TODO: How do we handle peaks near the border, when tof is quite off?'
            tof_max = xdata.max() 
        elif 0 < cutoff < xdata.max():
            tof_max =cutoff
        else:
            raise ValueError('cutoff must be between 0 and %.2f. Got %.1f instead.'%(xdata.max(), cutoff))
        peakPar = [p for p in peakParRef if np.sqrt(self._pFactor/(self._hv-p[0]))<tof_max and p[1]>rel_y_min]
        fitValues = {'fitPeakPos': self.__fit_peakpos_trans(peakPar),
        #fitValues = {'fitPeakPos': [p[0] for p in peakPar],  # self.__fit_peakpos_trans(peakPar),
                     'fitXdataKey': xdata_key, 'fitYdataKey': ydata_key,
                     'fitConstrains': {constrain_par: constrain},
                     'fitCutoff': cutoff}
        xcenter = peakParRef[0][0]
        yscale = self.__get_y_scale(self.xdata['ebin'], self.ydata['jIntensity'], xcenter, .6) # better use actual intensity values
        fitValues['fitPar0'] = self.__fit_par0_trans(peakPar, yscale, Eoff, toff, lscale)
        try:
            p, covar, info, mess, ierr = leastsq(self.__err_multi_gauss_trans, fitValues['fitPar0'], 
                                                 args=(xdata,ydata,
                                                       fitValues['fitPeakPos'],
                                                       constrain_par_map[constrain_par],
                                                       constrain),
                                                 full_output=True)
        except:
            return fitValues
            raise
        else:
            fitValues.update({'fitPar': p, 'fitCovar': covar, 'fitInfo': [info, mess, ierr]})
        
            return fitValues
       

    def gauge(self, xdata_key=None, ydata_key=None, rel_y_min=0, lscale=1.007, Eoff=0, toff=42e-9,
              constrain_par='toff', constrain=[30e-9, 70e-9], cutoff=None, peakpar_ref=None):
        'TODO: data_key parameters usage is not foolproof'
        '''
        Fits a multiple gauss to the pes in time domain.
        data_key: which xy-data to use for the fit
        constrain_par: which parameter to constrain:  lscale, toff, Eoff
        constrain: [constrain_par_min, constrain_par_min]
        rel_y_min: minimum peak height of reference peaks (cfg.pt_peakpar) to be included in the fit.
        peakpar_ref: dict with list of tuples with reference peak parameter,
                     e.g. {wave length: [(E_bin, I_rel, sigma), ...]}
        '''
        # choose data_keys if not given
        if xdata_key is None:
            xdata_key = 'tof'
        if ydata_key is None and 'subtracted' in self.mdata.data('systemTags'):
            ydata_key = 'intensitySub'
        elif ydata_key is None:
            ydata_key = 'intensity'
        if peakpar_ref is None:
            peakpar_ref = self.cfg.pt_peakpar[self.mdata.data('waveLength')]
        fitValues = self.__fit_multi_gauss_trans(xdata_key, ydata_key, peakpar_ref, Eoff, toff, lscale, rel_y_min, cutoff,
                                                  constrain_par, constrain)
        self.mdata.update(fitValues)
        self.mdata.add_tag('fitted', tagkey='systemTags')
        
    def _regauge(self, rel_y_min=None, cutoff=None):
        '''
        cutoff can be one of:
        * cutoff time
        * None: use previous value
        * 'reset': remove cutoff
        '''
        if 'fitted' not in self.mdata.data('systemTags'):
            raise ValueError('This spec was not gauged before.')
        if rel_y_min is None: # find value of previously used rel_y_min, if any
            if self.mdata.data('fitCutoff') is None:
                'TODO: How do we handle peaks near the border, when tof is quite off?'
                xdata = self.xdata[self.mdata.data('fitXdataKey')]
                tof_max = xdata.max()
            else:
                tof_max = self.mdata.data('fitCutoff')
            peak_ref_hights = [p[1] for p in self.cfg.pt_peakpar[self.mdata.data('waveLength')] if np.sqrt(self._pFactor/(self._hv-p[0]))<tof_max]
            if len(self.mdata.data('fitPeakPos')) < len(peak_ref_hights):
                print('Previously fitted peaks: {}, number of peaks in peak ref: {}'.format(len(self.mdata.data('fitPeakPos')), len(peak_ref_hights)))
                print('Some peaks were skipped during last fit.')
                dn = len(peak_ref_hights) - len(self.mdata.data('fitPeakPos'))
                peak_ref_hights.sort()
                rel_y_min = peak_ref_hights[dn -1]
                print('Setting rel_y_min to ', rel_y_min)
            else:
                rel_y_min = 0
                
        if cutoff is None:
            cutoff=self.mdata.data('fitCutoff')
        elif cutoff == 'reset':
            cutoff = None
                
        self.gauge(xdata_key=self.mdata.data('fitXdataKey'), ydata_key=self.mdata.data('fitYdataKey'),
                   rel_y_min=rel_y_min,
                   lscale=self.mdata.data('fitPar')[-1],
                   Eoff=self.mdata.data('fitPar')[-3],
                   toff=self.mdata.data('fitPar')[-2],
                   constrain_par=next(iter(self.mdata.data('fitConstrains').keys())), 
                   constrain=next(iter(self.mdata.data('fitConstrains').values())),
                   cutoff=cutoff,
                   peakpar_ref=None)



class SpecPeIr(SpecPePt):
    def __init__(self, mdata, xdata, ydata, cfg):
        SpecPePt.__init__(self, mdata, xdata, ydata, cfg)
        self._update_mdata_reference('specPePt')
        self.view = view.ViewPt(self)




class SpecPeWater(SpecPe):
    def __init__(self, mdata, xdata, ydata, cfg):
        SpecPe.__init__(self, mdata, xdata, ydata, cfg)
        self._update_mdata_reference('specPeWater')
        self.view = view.ViewWater(self)
        
#     def __del__(self):
#         SpecPe.__del__(self)
#         print('Deleting SpecPeWater-object')


    def __gl(self, x, xmax, A, sg, sl):
        y = np.zeros(x.shape)
        y[x<=xmax] = A*np.exp(-(x[x<=xmax]-xmax)**2/(2*sg**2))
        y[x>xmax] = A/((x[x>xmax]-xmax)**2/(sl**2)+1)
        return y
    

    def __gl_trans(self, t, tmax, At, sg, sl):
        y = np.zeros(t.shape)
        q = constants.m_e/(2*constants.e)*(self.mdata.data('flightLength'))**2
        hv = self._photon_energy(self.mdata.data('waveLength'))
        ebin = lambda t: hv - q/t**2
        xmax = ebin(tmax)
        A = At*tmax/(2*(hv-xmax))
        y[t<=tmax] = A*np.exp(-(ebin(t[t<=tmax])-xmax)**2/(2*sg**2))*2*q/t[t<=tmax]**3
        y[t>tmax] = A/((ebin(t[t>tmax])-xmax)**2/(sl**2)+1)*2*q/t[t>tmax]**3
        return y
    
    
    def multi_gl(self, x, par):
        plist = list(par)
        mgl = 0
        sl = plist.pop()
        sg = plist.pop()
        while len(plist) > 0:
            A = plist.pop()
            xmax = plist.pop()
            mgl+=self.__gl(x, xmax, A, sg, sl)
        return mgl
    
    def multi_gl_trans(self, x, par):
        plist = list(par)
        mgl = 0
        sl = plist.pop()
        sg = plist.pop()
        while len(plist) > 0:
            A = plist.pop()
            xmax = plist.pop()
            mgl+=self.__gl_trans(x, xmax, A, sg, sl)
        return mgl    
    
    
    def __err_multi_gl(self, par, x, y):
        return self.multi_gl(x, par)-y
    
    def __err_multi_gl_trans(self, par, x, y, asym_par):
        if np.all(par[1:-2:2] > 0): # keep peak maximum positive
            return self.multi_gl_trans(x, par)-y
        else:
            return 1e6
        
    def __err_multi_gl_trans_asym(self, par, x, y, asym_par):
        if np.all(par[1:-2:2] > 0) and par[-1] > par[-2]+asym_par: # keep peak maximum positive and sigma_g < sigma_l
            return self.multi_gl_trans(x, par)-y
        else:
            print('par reached bounderies.')
            return 1e6
    
    
    def __fit_gl(self, xdata_key, ydata_key, fitPar0, cutoff):
#        if gauged:
#            ebin_key = 'ebinGauged'
#        else:
#            ebin_key = 'ebin'
#            
#        if subtract_bg:
#            int_key = 'jIntensitySub'
#        else:
#            int_key = 'jIntensity'
            
        if type(cutoff) in [int,float]:
            xdata = self.xdata[xdata_key][self.xdata[xdata_key]<cutoff]
            ydata = self.ydata[ydata_key][:len(xdata)]
        elif cutoff == None:
            xdata = self.xdata[xdata_key]
            ydata = np.copy(self.ydata[ydata_key])
        else:
            raise ValueError('Cutoff must be int or float')
        
        fit_values = {'par0': fitPar0, 'cutoff': cutoff, 'xdataKey': xdata_key, 'ydataKey': ydata_key}
        try:
            p, covar, info, mess, ierr = leastsq(self.__err_multi_gl, fit_values['par0'],
                                                 args=(xdata,ydata), full_output=True)
        except:
            return fit_values
            raise
        else:
            # calculate chi squared
            chisq = sum(info['fvec']*info['fvec'])
            fit_values.update({'par': p, 'covar': covar, 'info': [chisq, info, mess, ierr]})
            return fit_values
 
 
    def __fit_gl_trans(self, xdata_key, ydata_key, fitPar0, cutoff, asym_par=None):
        'TODO: merge with __fit_gl.'
#        if gauged:
#            tof_key = 'tofGauged'
#        else:
#            tof_key = 'tof'
#            
#        if subtract_bg:
#            int_key = 'intensitySub'
#        else:
#            int_key = 'intensity'
        if asym_par is None:
            err_func = self.__err_multi_gl_trans
        elif type(asym_par) in [int, float]:
            if fitPar0[-1] > fitPar0[-2] + asym_par:
                err_func = self.__err_multi_gl_trans_asym
            else:
                raise ValueError('par0 does not fullfil boundary conditions.')
        else:
            raise ValueError('asym_par must be an integer or float or None')
          
        if type(cutoff) in [int,float]:
            xdata = self.xdata[xdata_key][self.xdata[xdata_key]<cutoff]
            ydata = self.ydata[ydata_key][:len(xdata)]
        elif cutoff == None:
            xdata = self.xdata[xdata_key]
            ydata = np.copy(self.ydata[ydata_key])
        else:
            raise ValueError('Cutoff must be int or float')
        
        fit_values = {'par0': fitPar0, 'cutoff': cutoff, 'xdataKey': xdata_key, 'ydataKey': ydata_key}
        try:
            p, covar, info, mess, ierr = leastsq(err_func,
                                                 fit_values['par0'],
                                                 args=(xdata,ydata, asym_par),
                                                 full_output=True)
        except:
            print('Warning: Fit did not converge.')
            return fit_values
            """TODO: This won't work. Better raise an error and leave handling of the start parameter
            par0 to the higher fit method."""
            raise
        else:
            # calculate chi squared
            chisq = sum(info['fvec']*info['fvec'])
            fit_values.update({'par': p, 'covar': covar, 'info': [chisq, info, mess, ierr]})
            return fit_values 
    
    
    def fit(self, fitPar0, fit_id='default_fit', fit_type='time', xdata_key='auto', ydata_key='auto',
            cutoff=None, asym_par=None):
        fitPar0 = np.array(fitPar0)
        # choose data_keys if not given
        if fit_type in ['time']:
            key_deps = {'tof': ['intensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw'],
                        'tofGauged': ['intensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw']}
            xdata_key, ydata_key = self._auto_key_selection(xdata_key=xdata_key, ydata_key=ydata_key, key_deps=key_deps)
            fit_values = self.__fit_gl_trans(xdata_key, ydata_key, fitPar0, cutoff, asym_par)
        elif fit_type in ['energy']:
            key_deps = {'ebin': ['jIntensity', 'jIntensitySub'],
                        'ebinGauged': ['jIntensityGauged', 'jIntensityGaugedSub']}
            xdata_key, ydata_key = self._auto_key_selection(xdata_key=xdata_key, ydata_key=ydata_key, key_deps=key_deps)
            fit_values = self.__fit_gl(xdata_key, ydata_key, fitPar0, cutoff)
        else:
            raise ValueError("fit_type must be one of 'time' or 'energy'.")
        
        print('Fit converged with:')
        print('   chi squared:', fit_values['info'][0])
        print('   reduced chi squared:', fit_values['info'][0]/(len(self.xdata[xdata_key]) - len(fit_values['par'])))
        print('Updating mdata...')
        self.mdata.update({'fitData': {fit_id: fit_values}})
        self.mdata.add_tag('fitted', tagkey='systemTags')
        
        
    def remove_fit(self, fit_id):
        self.mdata._rm_fit_data(fit_id)
        
    def _ask_for_refit(self, reason, refit=None, commit_after=False):
        if 'fitted' in self.mdata.data('systemTags'):
            print("Warning: {} will most likely make previous fit useless.".format(reason))
            #refit=''
            while refit not in ['y', 'n']:
                q = 'Fit again using previous fit parameters as start parameter [y|n]?: '
                refit = input(q)
            if refit == 'y':
                for fid in self.mdata.data('fitData').keys():
                    self._refit(fit_id=fid, commit_after=commit_after)
                    
                    
    def _refit(self, fit_id, fit_par=None, cutoff=None, asym_par=None, commit_after=False):
        if 'fitted' not in self.mdata.data('systemTags'):
            raise ValueError('This spec was not fitted before.')
        if 'tof' in self.mdata.data('fitData')[fit_id]['xdataKey']:
            fit_type = 'time'
        else:
            fit_type = 'energy'
        if fit_par is None:
            fit_par = self.mdata.data('fitData')[fit_id]['par']
            #fit_par[-2:] = [0.2, 0.2]
        if cutoff is None:
            cutoff = self.mdata.data('fitData')[fit_id]['cutoff']
        elif cutoff is 'reset':
            cutoff = None
        self.fit(fitPar0=fit_par,
                 fit_id=fit_id,
                 fit_type=fit_type,
                 cutoff=cutoff,
                 asym_par=asym_par)
        if commit_after:
            self.commit()
        
    def _get_peak_width(self, fit_par, fit_id):
        '''
        Returns the peak width (fwhm) of the given fit parameter set:
                ________
        fwhm = V 2*ln(2)*s_g + s_l
        ''' 
        fwhm = np.sqrt(2*np.log(2))*np.abs(self.mdata.data('fitData')[fit_id][fit_par][-2]) + np.abs(self.mdata.data('fitData')[fit_id][fit_par][-1])
        return fwhm
    
    def __isomer_binding_energy_limit(self, lpar, inv_size):
        '''Returns the binding energy limit at inv_size for an isomer class spicified by lpar''' 
        limit = None
        i = 1
        while i < len(lpar) and inv_size:
            if inv_size >= lpar[i][0]:
                limit = (lpar[i][1] - lpar[i-1][1])/np.abs(lpar[i][0] - lpar[i-1][0])*(inv_size - lpar[i-1][0]) - lpar[i-1][1]
                inv_size = None
                i += 1
            else:
                i += 1
                 
        if not limit:
            i -= 1
            limit = (lpar[i][1] - lpar[i-1][1])/np.abs(lpar[i][0] - lpar[i-1][0])*(inv_size - lpar[i-1][0]) - lpar[i-1][1]
        
        return limit
    
    
    def _assort_fit_peaks(self, fit_id, fit_par_key='par'):
        '''returns a dict containing {'isomer class name': (ebin, intensity), ...}'''
        inv_size = self.mdata.data('clusterBaseUnitNumber')**(-1/3)
        lin_par = self.cfg.water_isomer_limits[self.mdata.data('clusterBaseUnit')]
        peaks = zip(self.mdata.data('fitData')[fit_id][fit_par_key][:-2:2],
                    self.mdata.data('fitData')[fit_id][fit_par_key][1:-2:2])
        isomer_classes = {}
        for peak in peaks:
            # TODO: find corect unit of peak[0] (tof, ebin, etc.)
            tof, intensity = peak[0], peak[1]
            p, h = self.ebin(tof), self.jtrans(intensity, tof)
            if -1*p > self.__isomer_binding_energy_limit(lin_par['2'], inv_size):
                isomer_classes['2'] = (p,h)
            elif self.__isomer_binding_energy_limit(lin_par['2'], inv_size) >= -1*p > self.__isomer_binding_energy_limit(lin_par['1a'], inv_size):
                isomer_classes['1a'] = (p,h)
            elif self.__isomer_binding_energy_limit(lin_par['1a'], inv_size) >= -1*p > self.__isomer_binding_energy_limit(lin_par['1b'], inv_size):
                isomer_classes['1b'] = (p,h)
            else:
                isomer_classes['vib'] = (p,h)
                
        return isomer_classes
        
        
        
    def gauge(self, gaugeRef, refit=None, commit_after=False, ignore_wavelength=False):
        SpecPe.gauge(self, gaugeRef, ignore_wavelength=ignore_wavelength)
        self._ask_for_refit('gauging', refit=refit, commit_after=commit_after)

                    
                    
    def subtract_bg(self, bgFile, isUpDown=True):
        SpecPe.subtract_bg(self, bgFile, isUpDown=isUpDown)
        self._ask_for_refit('subtracting background')
        




           
#        if xdata_key is None:
#            xdata_key = 'tof'
#        if ydata_key is None and 'subtracted' in self.mdata.data('systemTags'):
#            ydata_key = 'intensitySub'
#        elif ydata_key is None:
#            ydata_key = 'intensity'
#        '''If subtract_bg and/or gauged are None, try to find useful defaults.'''
#        if subtract_bg == None:
#            if 'subtract_bgBgFile' in list(self.mdata.data().keys()):
#                subtract_bg = True
#            else:
#                subtract_bg = False
#        if gauged == None:
#            if 'gaugeRef' in list(self.mdata.data().keys()):
#                gauged = True
#            else:
#                gauged =False        
#        try:
#            if specType == 'ebin':
#                fitValues = self.__fit_gl(fitPar0, cutoff, subtract_bg, gauged)
#            elif specType == 'tof':
#                fitValues = self.__fit_gl_trans(fitPar0, cutoff, subtract_bg, gauged)
#            else:
#                raise ValueError('specType must be one of: "tof" or "ebin".')
#        except:
#            #self.mdata.update(fitValues)
#            raise
#        else:
#            print('Fit completed, Updating mdata...')
#            self.mdata.update(fitValues)


#    def fitTof(self, fitPar0, cutoff=None, subtract_bg=None, gauged=None):
#        '''If subtract_bg and/or gauged are None, try to find useful defaults.'''
#        if subtract_bg == None:
#            if 'subtract_bgBgFile' in self.mdata.data().keys():
#                subtract_bg = True
#            else:
#                subtract_bg = False
#        if gauged == None:
#            if 'gaugeRef' in self.mdata.data().keys():
#                gauged = True
#            else:
#                gauged =False
#        
#        try:
#            fitValues = self.__fit_gl_trans(fitPar0, cutoff, subtract_bg, gauged)
#        except:
#            #self.mdata.update(fitValues)
#            raise
#        else:
#            print 'Fit completed, Updating mdata...'
#            self.mdata.update(fitValues)



class SpecMs(Spec):
    def __init__(self, mdata, xdata, ydata, cfg):
        print('__init__: Init SpecMs')
        Spec.__init__(self, mdata, xdata, ydata, cfg)
        self._update_mdata_reference('specMs')
        if len(self.xdata) == 1:
            self.calc_spec_data() 
        self.view = view.ViewMs(self)
        
#     def _mass(self, t, t_ref, m_ref, m_baseunit):
#         return ((t/t_ref)**2)*m_ref/m_baseunit
    def _mass(self, t, k, m_baseunit):
        return k/m_baseunit*t**2
        
#     def _calc_ms(self, mass_key, time_key, t_ref, m_baseunit):
#         self.xdata[mass_key] = self._mass(self.xdata[time_key],
#                                           t_ref=t_ref,
#                                           m_ref=self.mdata.data('referenceMass'),
#                                           m_baseunit=m_baseunit)
        
    def _calc_ms(self, mass_key, time_key, k, m_baseunit):
        self.xdata[mass_key] = self._mass(self.xdata[time_key],
                                          k=k,
                                          m_baseunit=m_baseunit)
    
    'TODO: use *Import mdata keys or dont?'
    def calc_spec_data(self):
        self._calc_time_data( time_data_key='tof', time_offset=self.mdata.data('timeOffset'))
#         print('xdata.keys after _calc_time_data: ', self.xdata.keys())
        self._calc_fixed_intensities()
        self._calc_ms(mass_key='u', time_key='tof',
#                       t_ref=self.mdata.data('referenceTime'),
                      k=self.mdata.data('referenceTime'),                
                      m_baseunit=1)
        self._calc_ms(mass_key='s_u', time_key='tof',
#                       t_ref=self.mdata.data('referenceTime'),
                      k=self.mdata.data('referenceTime'),                
                      m_baseunit=self.mdata.data('clusterBaseUnitMass')/round(self.mdata.data('clusterBaseUnitMass')))
        self._calc_ms(mass_key='cluster', time_key='tof',
#                       t_ref=self.mdata.data('referenceTime'),
                      k=self.mdata.data('referenceTime'),
                      m_baseunit=self.mdata.data('clusterBaseUnitMass'))
        
        
    def gauge(self, unit='cluster'):
        '''
        Simple gauge function. Needs to query for t1, t2, dn.
        unit: one of 'cluster' or 'amu'
        '''
        if unit == 'cluster':
            m_unit = self.mdata.data('clusterBaseUnitMass')
            mass_key = 'ms'
        elif unit == 'amu':
            m_unit = 1
            mass_key = 'amu'
        else:
            raise ValueError('unit must be one of [cluster/amu].')
        t_off = lambda n,dn,t1,t2: (np.sqrt(1-float(dn)/n)*t2 - t1)/(np.sqrt(1-float(dn)/n)-1)
        t_ref = lambda m_unit,dn,t1,t2,t_off: np.sqrt(193.96/(m_unit*dn)*((t2-t_off)**2 - (t1-t_off)**2))
        self._calc_time_data(time_offset=0)
        self.view.show_tof()
        # Ask for t1,t2,dn
        no_valid_input = True
        while no_valid_input:
            q = 'Enter t1, t2, and dn separated by comma: '
            ui = input(q)
            ui_list = ui.split(',')
            t1 = float(ui_list[0].strip())
            t2 = float(ui_list[1].strip())
            dn = int(ui_list[2].strip())
            if t1<t2:
                no_valid_input = False
            else:
                print('t1, t2 should be numbers with t1<t2.')
                
        
        start_size = max(dn + 1, round(self.mdata.data('clusterBaseUnitNumberStart')*self.mdata.data('clusterBaseUnitMass')/m_unit))
        X = np.arange(32, #start_size,
                      320000, #round(self.mdata.data('clusterBaseUnitNumberEnd')*self.mdata.data('clusterBaseUnitMass')/m_unit),
                      1)
        min_delta_n = 100
#         is_min = False
        t1_position = np.abs(self.xdata['tof']-t1).argmin()
        t2_position = np.abs(self.xdata['tof']-t2).argmin()        
#         while len(X) > 0:
        Y = t_off(X, dn, t1, t2)
        n = X[np.abs(Y).argmin()]
#         n = X[0]
#             print('n is now: ', n)
        to = t_off(n, dn, t1, t2)
        tr = t_ref(m_unit,dn,t1,t2,to)
        print('n, to, tr: ', n, to, tr)
        self.mdata.update({'timeOffset': to, 'referenceTime': tr})
        self.calc_spec_data()
#             t1_position = np.abs(self.xdata['tof']-t1).argmin()
#             t2_position = np.abs(self.xdata['tof']-t2).argmin()
        m_t1 = self.xdata[mass_key][t1_position]
        m_t2 = self.xdata[mass_key][t2_position]
#             print('m_t1, m_t2: ', m_t1, m_t2)
        dm = m_t2 - m_t1
        print('Gauging resulted in dm=', dm)
#             raise
#         delta_n = np.abs(dn - dm)
#         if delta_n < min_delta_n:
# #                 print('Nothing new')
# #                 last_delta_n = delta_n
# # #                 t_off_min_pos = np.abs(Y).argmin()
# # #                 Y = np.delete(Y, t_off_min_pos)
# # #                 X = np.delete(X, t_off_min_pos)
# #             else:
# #                 print('Found new min delta_n.')
#             min_delta_n = delta_n
#             min_dm = dm
#             min_to = to
#             min_tr = tr
# #                 t_off_min_pos = np.abs(Y).argmin()
# #                 Y = np.delete(Y, t_off_min_pos)
# #                 X = np.delete(X, t_off_min_pos)
# #                 is_min = True
# #         return X, Y
#         X = np.delete(X, 0)
#         Y = np.delete(Y, 0)
#         print('min_delta_n found: ', min_delta_n)  
#         print('min_dm: ', min_dm)  
#         self.mdata.update({'timeOffset': min_to, 'referenceTime': min_tr})
#         self.calc_spec_data()        

    def gauge_new(self, dn_unit='cluster', view_unit='tof', p0=(5e9, 1.6e-7),
                  manual_offset=False, dn_unit_mass=None, use_idx=False, detail_run=False):
        '''
        TODO: Elements with isotopes needs special treatment, since 'center of mass'-mass doesn't work
              so well.
        Usage:
            * gauge_new()
            * divide estimated offset by cluster mass (simplified): e.g. 1432/39
            * round to full cluster number: e.g. round(1432/39)*39
            * use as offset for gauge_new(manual_offset=True)
        '''
        if dn_unit == 'cluster':
            dn_unit = self.mdata.data('clusterBaseUnitMass')
            #mass_key = 'ms'
        elif dn_unit == 's_u' and dn_unit_mass is None:
            dn_unit = self.mdata.data('clusterBaseUnitMass')/round(self.mdata.data('clusterBaseUnitMass'))
            #mass_key = 'amu'
        elif dn_unit == 's_u':
            dn_unit = dn_unit_mass/round(dn_unit_mass)
        else:
            raise ValueError('dn_unit must be one of [cluster/s_u].')        
        
        def get_pos_and_dn():
            # Ask for positions and dn
            no_valid_input = True
            while no_valid_input:
                q = 'Enter pos1, dn1, pos2, dn2, and pos3 separated by comma: '
                ui = input(q)
                ui_list = ui.split(',')
                p1 = float(ui_list[0].strip())
                dn1 = int(ui_list[1].strip())
                p2 = float(ui_list[2].strip())
                dn2 = int(ui_list[3].strip())
                p3 = float(ui_list[4].strip())
                if p1<p2<p3 and dn1>1 and dn2>1:
                    no_valid_input = False
                else:
                    print('p1, p2, p3 must be floats with p1<p2<p3 and dn1, dn2 > 1.')
            return p1, dn1, p2, dn2, p3
                
        def time_from_m(m, k, toff, m_unit):
            return toff + np.sqrt(m_unit*m/k)
        
        # reuse fit parameter from previous fit
        if p0 == 'current':
            p0 = (self.mdata.data('referenceTime'), self.mdata.data('timeOffset'))
        
        # view mode
        if view_unit == 'tof':
            self._calc_time_data(time_offset=0)
            self.view.show_tof()
            p1, dn1, p2, dn2, p3 = get_pos_and_dn()
            t1, t2, t3 = p1*1e-6, p2*1e-6, p3*1e-6
        elif view_unit in ['s_u', 'cluster']:
            self._calc_time_data(time_offset=p0[1])
            if view_unit == 'cluster':
                m_baseunit = self.mdata.data('clusterBaseUnitMass')
                self._calc_ms(mass_key=view_unit, time_key='tof', k=p0[0], m_baseunit=m_baseunit)
            else:
                m_baseunit = self.mdata.data('clusterBaseUnitMass')/round(self.mdata.data('clusterBaseUnitMass'))
                self._calc_ms(mass_key=view_unit, time_key='tof', k=p0[0], m_baseunit=m_baseunit)
            self.view.show_ms(mass_key=view_unit)                
            p1, dn1, p2, dn2, p3 = get_pos_and_dn()
            t1 = time_from_m(p1, p0[0], p0[1], m_baseunit)
            t2 = time_from_m(p2, p0[0], p0[1], m_baseunit)
            t3 = time_from_m(p3, p0[0], p0[1], m_baseunit)
        else:
            raise ValueError('view_unit must be one of [cluster/s_u].')
        
        # get index of peaks
        i1 = np.abs(self.xdata[view_unit] - p1).argmin()
        i2 = np.abs(self.xdata[view_unit] - p2).argmin()
        i3 = np.abs(self.xdata[view_unit] - p3).argmin()
        
        def mass(t, k, toff):
            m_unit = self.mdata.data('clusterBaseUnitMass')/round(self.mdata.data('clusterBaseUnitMass'))
            return k/m_unit*(t - toff)**2
        

        def err_mass(p, t, m):
            k=p[0]
            toff=p[1]
            dn=p[2]
            # limit |toff| < 1e-6
#             if np.abs(toff) > 1e-6:
#                 return np.abs(mass(t, k, toff) - m - dn + 1e6)
#             else: 
            return mass(t, k, toff) - m - dn
        
        def err2_mass(p, t, m):
            k=p[0]
            toff=p[1]
            # limit |toff| < 1e-6
#             if np.abs(toff) > 1e-6:
#                 return np.abs(mass(t, k, toff) - m + 1e6)
#             else: 
            return mass(t, k, toff) - m
        
        
        
        def mass_idx(idx, k, toff):
            m_unit = self.mdata.data('clusterBaseUnitMass')/round(self.mdata.data('clusterBaseUnitMass'))
            return k/m_unit*(self._idx2time(idx, self.mdata.data('timePerPoint'), self.mdata.data('triggerOffset'), toff))**2
        

        def err_mass_idx(p, idx, m):
            k=p[0]
            toff=p[1]
            dn=p[2]
            # limit |toff| < 1e-6
#             if np.abs(toff) > 1e-6:
#                 return np.abs(mass(t, k, toff) - m - dn + 1e6)
#             else: 
            return mass_idx(idx, k, toff) - m - dn
        
        def err2_mass_idx(p, idx, m):
            k=p[0]
            toff=p[1]
            # limit |toff| < 1e-6
#             if np.abs(toff) > 1e-6:
#                 return np.abs(mass(t, k, toff) - m + 1e6)
#             else: 
            return mass_idx(idx, k, toff) - m        
        
        
            
        p0=(p0[0], p0[1], 0)
        isu = round(self.mdata.data('clusterBaseUnitMass'))/self.mdata.data('clusterBaseUnitMass')
        dm1, dm2 = dn1*isu*dn_unit, dn2*isu*dn_unit
        t_array = np.array([t1, t2, t3])
        m_array = np.array([0, dm1, dm1+dm2]) + 1
        
        if manual_offset:
            print('\nSet offset manually. Skipping step 1 fit.')
            no_valid_input = True
            while no_valid_input:
                q = 'Enter offset: '
                offset = int(input(q))
                if offset>0:
                    no_valid_input = False
                else:
                    print('offset must be int > 0.')
        else:
            # get offset dn
            print('\nStep 1: Fitting with: ', t_array, m_array)
            p, covar, info, mess, ierr = leastsq(err_mass, p0, args=(t_array, m_array), full_output=True)
            offset = int(round(p[2]+1))
            print('Step 1: Fit resulted in mass offset of: ', offset)
            d_offset = round(np.abs(p[2]+1 - offset), 1)
            print('Step 1: Offset int quality: ', d_offset)
            if d_offset > 0.2:
                print('Step 1: Warning: offset int quality is bad!')
            print('Step 1: Fit parameter: ', p)            
                           
        m_array = np.array([offset, offset+dm1, offset+dm1+dm2])
        print('\nStep 2: Fitting with: ', t_array, m_array, m_array/self.mdata.data('clusterBaseUnitMass'))
        p, covar, info, mess, ierr = leastsq(err2_mass, (p0[0], p0[1]), args=(t_array, m_array), full_output=True)
        # calculate chi squared
        chisq = sum(info['fvec']*info['fvec'])
        print('Step 2: Fit resulted in gauge parameter:', p, 'with chisq:', chisq)

        # indece fit
        print('\nFit using indeces:')
        idx_array = np.array([i1, i2, i3])
        m_array = np.array([0, dm1, dm1+dm2]) + 1
        
        if manual_offset:
            print('Set offset manually. Skipping step 1 fit.')
            no_valid_input = True
            while no_valid_input:
                q = 'Enter offset: '
                offset = int(input(q))
                if offset>0:
                    no_valid_input = False
                else:
                    print('offset must be int > 0.')
        else:
            # get offset dn
            tidx_array = self._idx2time(idx_array, self.mdata.data('timePerPoint'), self.mdata.data('triggerOffset'))
            print('Step 1: Fitting with: ', idx_array, tidx_array, m_array)
            p_idx, covar, info, mess, ierr = leastsq(err_mass_idx, p0, args=(idx_array, m_array), full_output=True)
            offset = int(round(p_idx[2]+1))
            print('Step 1: Fit resulted in mass offset of: ', offset)
            d_offset = round(np.abs(p_idx[2]+1 - offset), 1)
            print('Step 1: Offset int quality: ', d_offset)
            if d_offset > 0.2:
                print('Step 1: Warning: offset int quality is bad!')
            print('Step 1: Fit parameter: ', p_idx)            
             
        if not detail_run:
            for offset in range(offset-3,offset+4):
                print('\n########################\nStarting test for offset:', offset)              
                m_array = np.array([offset, offset+dm1, offset+dm1+dm2])
                print('\nStep 2: Fitting with: ', idx_array, m_array, m_array/self.mdata.data('clusterBaseUnitMass'))
                p_idx, covar, info, mess, ierr = leastsq(err2_mass_idx, (p0[0], p0[1]), args=(idx_array, m_array), full_output=True)
                # calculate chi squared
                chisq = sum(info['fvec']*info['fvec'])
                print('Step 2: Fit resulted in gauge parameter:', p_idx, 'with chisq:', chisq)
                
                # get offset dn
                print('\nRefitting with new parameter:', p_idx)
                p_idx = (p_idx[0], p_idx[1], 0)
                m_array = np.array([0, dm1, dm1+dm2]) + 1
                tidx_array = self._idx2time(idx_array, self.mdata.data('timePerPoint'), self.mdata.data('triggerOffset'))
                print('Step 1: Fitting with: ', idx_array, tidx_array, m_array)
                p_idx, covar, info, mess, ierr = leastsq(err_mass_idx, p_idx, args=(idx_array, m_array), full_output=True)
                new_offset = int(round(p_idx[2]+1))
                print('Step 1: Fit resulted in mass offset of: ', new_offset)
                d_offset = round(np.abs(p_idx[2]+1 - new_offset), 1)
                print('Step 1: Offset int quality: ', d_offset)
                if d_offset > 0.2:
                    print('Step 1: Warning: offset int quality is bad!')
                print('Step 1: Fit parameter: ', p_idx)
                
                m_array = np.array([new_offset, new_offset+dm1, new_offset+dm1+dm2])
                print('\nStep 2: Fitting with: ', idx_array, m_array, m_array/self.mdata.data('clusterBaseUnitMass'))
                p_idx, covar, info, mess, ierr = leastsq(err2_mass_idx, (p_idx[0], p_idx[1]), args=(idx_array, m_array), full_output=True)
                # calculate chi squared
                chisq = sum(info['fvec']*info['fvec'])
                print('Step 2: Fit resulted in gauge parameter:', p_idx, 'with chisq:', chisq)
            
            
        
        if use_idx:
            p = p_idx
        
        self.mdata.update({'timeOffset': p[1], 'referenceTime': p[0]})
        self.calc_spec_data()






class SpecPf(Spec):
    def calc_spec_data(self):
        self.__calc_tof()





