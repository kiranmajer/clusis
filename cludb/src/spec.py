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
        self.mdata_ref = cfg.mdata_ref['spec']
        self.mdata = Mdata(mdata, self.mdata_ref)
        self.xdata = xdata
        self.ydata = ydata
        self.cfg = cfg
        self.view = view.View(self)        
        
    
    def _update_mdata_reference(self, specTypeClass, cfg):
        'Adapts mdata reference to the spec type class'
        print('Updating ref with {}'.format(specTypeClass))
        self.mdata_ref.update(cfg.mdata_ref[specTypeClass])
    
    
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
        
    def _idx2time(self, idx, time_per_point, trigger_offset, time_offset=0):
        #self.xdata['tof'] = self.xdata['idx']*self.mdata.data('timePerPoint')-self.mdata.data('triggerOffset')-time_offset
        return idx*time_per_point - trigger_offset - time_offset
    
    def _calc_time_data(self, time_data_key='tof', time_offset=0):
        self.xdata[time_data_key] = self._idx2time(idx=self.xdata['idx'],
                                                   time_per_point=self.mdata.data('timePerPoint'),
                                                   trigger_offset=self.mdata.data('triggerOffset'),
                                                   time_offset=time_offset)

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
        time range before subtraction!  
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


        

class SpecPe(Spec):
    def __init__(self, mdata, xdata, ydata, cfg):
        print('__init__: Init SpecPe')
        Spec.__init__(self, mdata, xdata, ydata, cfg)
        self._update_mdata_reference('specPe', cfg)
        self._pFactor = constants.m_e/(2*constants.e)*(self.mdata.data('flightLength'))**2
        self._hv = self._photon_energy(self.mdata.data('waveLength'))
        if len(self.xdata) == 1:
            self.calc_spec_data()
        #print 'Assigning view.ViewPes'
        self.view = view.ViewPes(self)
    
    # basic methods    
    def _idx2time(self, idx, time_per_point, trigger_offset, lscale, Eoff, toff):
        return 1/np.sqrt(lscale*(1/(idx*time_per_point - trigger_offset)**2 - Eoff/self._pFactor)) - toff
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
        lscale = self.mdata.data(lscale_key)
        Eoff = self.mdata.data(Eoff_key)
        toff = self.mdata.data(toff_key)
        self._calc_time_data(timedata_key='tof', lscale=lscale, Eoff=Eoff, toff=toff)
        self._calc_ekin(new_key='ekin', timedata_key='tof')  #, lscale=lscale, Eoff=Eoff, toff=toff)
        self._calc_ebin(new_key='ebin', timedata_key='tof')  #, lscale=lscale, Eoff=Eoff, toff=toff)
        self._calc_fixed_intensities()
        self._calc_jacoby_intensity()
        
        
    def gauge(self, gaugeRef):
        gaugeSpec = load.load_pickle(self.cfg, gaugeRef)
        if gaugeSpec.mdata.data('specTypeClass') not in ['specPePt']:
            raise ValueError('Gauge reference is not a Pt-spectrum.')
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
        del gaugeSpec
        
    def subtract_bg(self, bgFile, isUpDown=True):
        Spec.subtract_bg(self, bgFile, isUpDown=isUpDown)
        self._calc_jacoby_intensity(new_key='jIntensitySub', intensity_key='intensitySub')
        if 'gauged' in self.mdata.data('systemTags'):
            self._calc_jacoby_intensity(new_key='jIntensityGaugedSub',
                                        intensity_key='intensitySub', timedata_key='tofGauged')    
        self._commit_pickle()
        
        
        
class SpecPePt(SpecPe):
    def __init__(self, mdata, xdata, ydata, cfg):
        SpecPe.__init__(self, mdata, xdata, ydata, cfg)
        self._update_mdata_reference('specPePt', cfg)
        self.view = view.ViewPt(self)
             
        
#    def __fit_peak_pos(self, peakPar):
#        return [p[0] for p in peakPar]
    
    
    def __fit_peakpos_trans(self, peakPar):
        return [np.sqrt(self._pFactor/(self._hv-p[0])) for p in peakPar]
    
    
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
        xlb = np.abs(xdata-(xcenter-xinterval/2)).argmin()
        xub = np.abs(xdata-(xcenter+xinterval/2)).argmin()
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
    
    
    def _multi_gauss_trans(self, t, peak_pos, parList):
        '''
        Multiple Gauss at peak_pos with parameter from parList transformed into time domain
        '''
        plist = list(parList)
        xlist = list(peak_pos)
        #gaussTrans = lambda t,m,A,s,toff,Eoff: A*np.exp(-(self._hv - self._pFactor*(1/(t + toff)**2 + 1/Eoff**2) - m)**2/(2*s**2))*2*self._pFactor/(t + toff)**3
        #gaussTrans = lambda t,m,A,sigma,toff,Eoff,lscale: A*np.exp(-(-self._pFactor*(1/(t)**2 + 1/Eoff**2 - 1/(l*m + toff)**2))**2/(2*s**2))*2*self._pFactor/(t)**3
        #gaussTrans = lambda t,m,A,sigma,toff,Eoff,lscale: A*2*self._pFactor/(t)**3*np.exp(-(self._pFactor*(1/(1/np.sqrt(1/t**2-Eoff/self._pFactor)-toff)**2/lscale**2 - 1/m**2))**2/(2*sigma**2))
        # orig working version
        gaussTrans = lambda t,m,A,sigma,toff,Eoff,lscale: A*2*self._pFactor/(t)**3*np.exp(-(self._pFactor*(1/(1/np.sqrt(lscale*(1/t**2 - Eoff/self._pFactor)) - toff)**2 - 1/m**2))**2/(2*sigma**2))
        #gaussTrans = lambda t,m,A,sigma,toff,Eoff,lscale: A*2*self._pFactor/(t)**3*np.exp(-(self._pFactor/t**2-self._pFactor/(lscale*(m+toff)**2) - Eoff)**2/(2*sigma**2))
        #gaussTrans = lambda t,m,A,sigma,toff,Eoff,lscale: A*2*self._pFactor/(t)**3*np.exp(-(self._pFactor*(1/(1/(np.sqrt(1/(lscale**2*(t+toff)**2) + Eoff/self._pFactor)))**2 - 1/m**2))**2/(2*sigma**2))
        lscale =plist.pop()
        toff = plist.pop()
        Eoff = plist.pop()
        mgaussTrans = 0
        while len(plist) > 0:
            sigma = plist.pop()
            A = plist.pop()
            m = xlist.pop()
            mgaussTrans += gaussTrans(t, m, A, sigma, toff, Eoff, lscale)
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
            tof_max = xdata.max()
        elif 0 < cutoff < xdata.max():
            tof_max =cutoff
        else:
            raise ValueError('cutoff must be between 0 and %.2f. Got %.1f instead.'%(xdata.max(), cutoff))
        peakPar = [p for p in peakParRef if np.sqrt(self._pFactor/(self._hv-p[0]))<tof_max and p[1]>rel_y_min]
        fitValues = {'fitPeakPos': self.__fit_peakpos_trans(peakPar),
                     'fitXdataKey': xdata_key, 'fitYdataKey': ydata_key,
                     'fitConstrains': {constrain_par: constrain},
                     'fitCutoff': cutoff}
        xcenter = peakParRef[0][0]
        yscale = self.__get_y_scale(self.xdata['ebin'], self.ydata['jIntensity'], xcenter, 0.4) # better use actual intensity values
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
       

    def gauge(self, xdata_key=None, ydata_key=None, rel_y_min=0, lscale=1, Eoff=0, toff=42e-9,
              constrain_par='toff', constrain=[37e-9, 47e-9], cutoff=None):
        '''
        Fits a multiple gauss to the pes in time domain.
        data_key: which xy-data to use for the fit
        constrain_par: which parameter to constrain:  lscale, toff, Eoff
        constrain: [constrain_par_min, constrain_par_min]
        rel_y_min: minimum peak height of reference peaks (cfg.pt_peakpar) to be included in the fit.
        '''
        # choose data_keys if not given
        if xdata_key is None:
            xdata_key = 'tof'
        if ydata_key is None and 'subtracted' in self.mdata.data('systemTags'):
            ydata_key = 'intensitySub'
        elif ydata_key is None:
            ydata_key = 'intensity'
        peakParRef = self.cfg.pt_peakpar[self.mdata.data('waveLength')]
        fitValues = self.__fit_multi_gauss_trans(xdata_key, ydata_key, peakParRef, Eoff, toff, lscale, rel_y_min, cutoff,
                                                  constrain_par, constrain)
        self.mdata.update(fitValues)
        self.mdata.add_tag('fitted', tagkey='systemTags')



class SpecPeWater(SpecPe):
    def __init__(self, mdata, xdata, ydata, cfg):
        SpecPe.__init__(self, mdata, xdata, ydata, cfg)
        self._update_mdata_reference(mdata['specTypeClass'], cfg)
        self.view = view.ViewWater(self)


    def __gl(self, x, xmax, A, sg, sl):
        y = np.zeros(x.shape)
        y[x<=xmax] = A*np.exp(-(x[x<=xmax]-xmax)**2/(2*sg**2))
        y[x>xmax] = A/((x[x>xmax]-xmax)**2/(2*sl**2)+1)
        return y
    

    def __gl_trans(self, t, tmax, At, sg, sl):
        y = np.zeros(t.shape)
        q = constants.m_e/(2*constants.e)*(self.mdata.data('flightLength'))**2
        hv = self._photon_energy(self.mdata.data('waveLength'))
        ebin = lambda t: hv - q/t**2
        xmax = ebin(tmax)
        A = At*tmax/(2*(hv-xmax))
        y[t<=tmax] = A*np.exp(-(ebin(t[t<=tmax])-xmax)**2/(2*sg**2))*2*q/t[t<=tmax]**3
        y[t>tmax] = A/((ebin(t[t>tmax])-xmax)**2/(2*sl**2)+1)*2*q/t[t>tmax]**3
        return y
    
    
    def multi_gl(self, x, par):
        plist = list(par)
        mgl = 0
        sl =plist.pop()
        sg = plist.pop()
        while len(plist) > 0:
            A = plist.pop()
            xmax = plist.pop()
            mgl+=self.__gl(x, xmax, A, sg, sl)
        return mgl
    
    def multi_gl_trans(self, x, par):
        plist = list(par)
        mgl = 0
        sl =plist.pop()
        sg = plist.pop()
        while len(plist) > 0:
            A = plist.pop()
            xmax = plist.pop()
            mgl+=self.__gl_trans(x, xmax, A, sg, sl)
        return mgl    
    
    
    def __err_multi_gl(self, par, x, y):
        return self.multi_gl(x, par)-y
    
    def __err_multi_gl_trans(self, par, x, y):
        return self.multi_gl_trans(x, par)-y    
    
    
    def __fit_gl(self, fitPar0, cutoff, subtract_bg, gauged):
        if gauged:
            ebin_key = 'ebinGauged'
        else:
            ebin_key = 'ebin'
            
        if subtract_bg:
            int_key = 'jIntensitySub'
        else:
            int_key = 'jIntensity'
            
        if type(cutoff) in [int,float]:
            xdata = self.xdata[ebin_key][self.xdata[ebin_key]<cutoff]
            ydata = self.ydata[int_key][:len(xdata)]
        elif cutoff == None:
            xdata = self.xdata[ebin_key]
            ydata = np.copy(self.ydata[int_key])
        else:
            raise ValueError('Cutoff must be int or float')
        
        fitValues = {'fitPar0': fitPar0, 'fitCutoff': cutoff, 'fitGauged': gauged, 'fitsubtract_bg': subtract_bg}
        p, covar, info, mess, ierr = leastsq(self.__err_multi_gl, fitPar0, args=(xdata,ydata), full_output=True)
        fitValues.update({'fitPar': p, 'fitCovar': covar, 'fitInfo': [info, mess, ierr]})
        
        return fitValues
 
 
    def __fit_gl_trans(self, fitPar0, cutoff, subtract_bg, gauged):
        if gauged:
            tof_key = 'tofGauged'
        else:
            tof_key = 'tof'
            
        if subtract_bg:
            int_key = 'intensitySub'
        else:
            int_key = 'intensity'
            
        if type(cutoff) in [int,float]:
            xdata = self.xdata[tof_key][self.xdata[tof_key]<cutoff]
            ydata = self.ydata[int_key][:len(xdata)]
        elif cutoff == None:
            xdata = self.xdata[tof_key]
            ydata = np.copy(self.ydata[int_key])
        else:
            raise ValueError('Cutoff must be int or float')
        
        fitValues = {'fitPar0Tof': fitPar0, 'fitCutoffTof': cutoff, 'fitGaugedTof': gauged, 'fitsubtract_bgTof': subtract_bg}
        p, covar, info, mess, ierr = leastsq(self.__err_multi_gl_trans, fitPar0, args=(xdata,ydata), full_output=True)
        fitValues.update({'fitParTof': p, 'fitCovarTof': covar, 'fitInfoTof': [info, mess, ierr]})
        
        return fitValues 
    
    
    def fit(self, specType, fitPar0, cutoff=None, subtract_bg=None, gauged=None):
        fitPar0 = np.array(fitPar0)
        '''If subtract_bg and/or gauged are None, try to find useful defaults.'''
        if subtract_bg == None:
            if 'subtract_bgBgFile' in list(self.mdata.data().keys()):
                subtract_bg = True
            else:
                subtract_bg = False
        if gauged == None:
            if 'gaugeRef' in list(self.mdata.data().keys()):
                gauged = True
            else:
                gauged =False
        
        try:
            if specType == 'ebin':
                fitValues = self.__fit_gl(fitPar0, cutoff, subtract_bg, gauged)
            elif specType == 'tof':
                fitValues = self.__fit_gl_trans(fitPar0, cutoff, subtract_bg, gauged)
            else:
                raise ValueError('specType must be one of: "tof" or "ebin".')
        except:
            #self.mdata.update(fitValues)
            raise
        else:
            print('Fit completed, Updating mdata...')
            self.mdata.update(fitValues)


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
        self._update_mdata_reference(mdata['specTypeClass'], cfg)
        if len(self.xdata) == 1:
            self.calc_spec_data() 
        self.view = view.ViewMs(self)
        
    def _mass(self, t, t_ref, m_ref, m_baseunit):
        return ((t/t_ref)**2)*m_ref/m_baseunit
        
    def _calc_ms(self, mass_key, time_key, t_ref, m_baseunit):
        self.xdata[mass_key] = self._mass(self.xdata[time_key],
                                          t_ref=t_ref,
                                          m_ref=self.mdata.data('referenceMass'),
                                          m_baseunit=m_baseunit)
    
    'TODO: use *Import mdata keys or dont?'
    def calc_spec_data(self):
        self._calc_time_data(self.mdata.data('timeOffset'))
        self._calc_fixed_intensities()
        self._calc_ms(mass_key='amu', time_key='tof',
                      t_ref=self.mdata.data('referenceTime'),
                      m_baseunit=1)
        self._calc_ms(mass_key='ms', time_key='tof',
                      t_ref=self.mdata.data('referenceTime'),
                      m_baseunit=self.mdata.data('clusterBaseUnitMass'))
        
        
    def gauge(self, unit='cluster'):
        '''
        Simple gauge function. Needs to query for t1, t2, dn.
        unit: one of 'cluster' or 'amu'
        '''
        if unit == 'cluster':
            m_unit = self.mdata.data('clusterBaseUnitMass')
        elif unit == 'amu':
            m_unit = 1
        else:
            raise ValueError('unit must be one of [cluster/amu].')
        t_off = lambda n,dn,t1,t2: (np.sqrt(1-float(dn)/n)*t2 - t1)/(np.sqrt(1-float(dn)/n)-1)
        t_ref = lambda m_unit,dn,t1,t2,t_off: np.sqrt(193.96/(m_unit*dn)*((t2-t_off)**2 - (t1-t_off)**2))
        self._calc_time_data(time_off=0)
        self.view.showTof()
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
                
        start_size = max(dn + 1, self.mdata.data('clusterBaseUnitNumberStart'))
        X = np.arange(start_size,
                      self.mdata.data('clusterBaseUnitNumberEnd'))
        Y = t_off(X, dn, t1, t2)
        n = X[np.abs(Y).argmin()]
        to = t_off(n, dn, t1, t2)
        tr = t_ref(m_unit,dn,t1,t2,to)
        self.mdata.update({'timeOffset': to, 'referenceTime': tr})
        self.calc_spec_data()
        
        
        

class SpecPf(Spec):
    def calc_spec_data(self):
        self.__calc_tof()





