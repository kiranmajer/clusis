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
        
    
    def update_mdata_reference(self, specTypeClass, cfg):
        self.mdata_ref.update(cfg.mdata_ref[specTypeClass])
    
    
    def commit_db(self, update=True):
        with Db(self.mdata.data('machine'), self.cfg) as db:
            db.add(self, update=update)
        
        
    def commit_pickle(self):
        '''
        Stores the self.mdata.data(), self.xdata, self.ydata dicts in a pickle file under the path:
        config.path['data']/<year>/<recTime>_<sha1>.pickle
        '''
        pickleFile = os.path.join(self.cfg.path['base'], self.mdata.data('pickleFile'))
        pickleDir = os.path.dirname(pickleFile)
        if not os.path.exists(pickleDir):
            os.mkdir(pickleDir)   
        with open(pickleFile, 'wb') as f:
            pickle.dump((self.mdata.data(), self.xdata, self.ydata), f)
            
            
    def commit(self, update=True):
        self.commit_pickle()
        self.commit_db(update=update)
        
    '''TODO: make privat'''    
    def calc_tof(self, time_offset=0):
        self.xdata['tof'] = self.xdata['idx']*self.mdata.data('timePerPoint')-self.mdata.data('triggerOffset')-time_offset

    def photon_energy(self, waveLength):
        """Calculates photon energy in eV for a given wave length.
        
        Returns: float."""
        photon_energy = constants.h*constants.c/(constants.e*waveLength)
        return photon_energy
        
    def _fix_neg_intensities(self, ydataKey='rawIntensity', newKey='intensity'):
        """
        The Oscilloscope sets the value for bins without counts to the value of the frame of display.
        So it's safe to set them to 0. 
        """
        fixedIntensity = (self.ydata[ydataKey] + np.abs(self.ydata[ydataKey]))/2
        self.ydata[newKey] = fixedIntensity
    
    def __calc_sub_intensities(self, bgSpec):
        self.ydata['intensitySubRaw'] = self.ydata['intensity'] - bgSpec.ydata['intensity']
        self._fix_neg_intensities('intensitySubRaw', 'intensitySub')
    
    def subtract_bg(self, bgFile, isUpDown=False):
        bgSpec = load.load_pickle(self.cfg, bgFile)
        if not self.mdata.data('specType') == bgSpec.mdata.data('specType'):
            raise ValueError('Background file has different spec type.')
        self.mdata.update({'subtract_bgBgFile': bgFile})
        'TODO: tag managment. Right now the same tag(s) is(are) added, each time subtract_bg is called.'
        if isUpDown:
            bgSpec.mdata.update({'tags': ['background', 'up/down'], 'subtract_bgSpecFile': self.mdata.data('pickleFile')})
            self.mdata.update({'tags': ['up/down']})
        else:
            bgSpec.mdata.update({'tags': ['background'], 'subtract_bgSpecFile': self.mdata.data('pickleFile')})
        self.__calc_sub_intensities(bgSpec)
        self.commit()
        bgSpec.commit()


        

class SpecPe(Spec):
    def __init__(self, mdata, xdata, ydata, cfg):
        print('__init__: Init SpecPe')
        Spec.__init__(self, mdata, xdata, ydata, cfg)
        self.update_mdata_reference(mdata['specTypeClass'], cfg)
        self._pFactor = constants.m_e/(2*constants.e)*(self.mdata.data('flightLength'))**2
        self._hv = self.photon_energy(self.mdata.data('waveLength'))
        if len(self.xdata) == 1:
            self.calc_spec_data()
        #print 'Assigning view.ViewPes'
        self.view = view.ViewPes(self)
        
    def ebin(self, t, gauge_scale=1, gauge_offset=0):
        return (self._hv-self._pFactor/t**2 - gauge_offset)/gauge_scale

    def ekin(self, t, gauge_scale=1, gauge_offset=0):
        return self._hv - self.ebin(t, gauge_scale, gauge_offset)
        
    def calc_tof_gauged(self, t, gauge_scale, gauge_offset):
        return np.sqrt(self._pFactor/self.ekin(t, gauge_scale, gauge_offset))
        
    def jtrans(self, intensity, t):
        return intensity*t**3/(2*self._pFactor)
    
    def jtrans_inv(self, intensity, t):
        return intensity*2*self._pFactor/t**3
    
    
    def __calc_ekin(self, newKey='ekin', gauge_scale=1, gauge_offset=0):
        self.xdata[newKey] = self.ekin(self.xdata['tof'], gauge_scale, gauge_offset) 
        #self.xdata['ekin'] = constants.m_e/(2*constants.e)*(self.mdata.data('flightLength')/self.xdata['tof'])**2
    
    def __calc_ebin(self, newKey='ebin', gauge_scale=1, gauge_offset=0):
        self.xdata[newKey] = self.ebin(self.xdata['tof'], gauge_scale, gauge_offset)
        #self.xdata['ebin'] = self.photon_energy(self.mdata.data('waveLength')) - self.xdata['ekin']
        
    def __calc_jacoby_intensity(self, newKey='jIntensity', intensityKey='intensity', tofKey='tof'):
        self.ydata[newKey] = self.jtrans(self.ydata[intensityKey], self.xdata[tofKey])
        #self.ydata[newKey] = self.ydata[ydataKey]/(2*self.xdata['ekin']/self.xdata['tof'])
        
#    def __calcEbinGauged(self):
#        self.xdata['ebinGauged'] = (self.xdata['ebin'] - self.mdata.data('gaugePar')['offset'])/self.mdata.data('gaugePar')['scale']
        
    
    def calc_spec_data(self):
        self.calc_tof(self.mdata.data('timeOffset'))
        self.__calc_ekin()
        self.__calc_ebin()
        self._fix_neg_intensities()
        self.__calc_jacoby_intensity()
        
        
    def gauge(self, gaugeRef):
        self.mdata.update({'gaugeRef': gaugeRef})
        gaugeSpec = load.load_pickle(self.cfg, gaugeRef)
        scale, offset = gaugeSpec.mdata.data('fitPar')[-2:]
        self.mdata.update({'gaugePar': {'scale': scale, 'offset': offset}})
        # calc xdata gauged
        self.__calc_ebin(newKey='ebinGauged', gauge_scale=scale, gauge_offset=offset)
        self.__calc_ekin(newKey='ekinGauged', gauge_scale=scale, gauge_offset=offset)
        self.xdata['tofGauged'] = self.calc_tof_gauged(self.xdata['tof'], gauge_scale=scale, gauge_offset=offset)
        # calc ydata gauged
        self.__calc_jacoby_intensity(newKey='jIntensityGauged', intensityKey='intensity', tofKey='tofGauged')
        if 'jIntensitySub' in list(self.ydata.keys()):
            self.__calc_jacoby_intensity(newKey='jIntensityGaugedSub',
                                       intensityKey='intensitySub', tofKey='tofGauged')
        self.commit_pickle()
        del gaugeSpec
        
    def subtract_bg(self, bgFile, isUpDown=True):
        Spec.subtract_bg(self, bgFile, isUpDown=isUpDown)
        self.__calc_jacoby_intensity(newKey='jIntensitySub', intensityKey='intensitySub')
        if 'gaugePar' in list(self.mdata.data().keys()):
            self.__calc_jacoby_intensity(newKey='jIntensityGaugedSub',
                                       intensityKey='intensitySub', tofKey='tofGauged')
            
        self.commit_pickle()
        
        
class SpecPePt(SpecPe):
    def __init__(self, mdata, xdata, ydata, cfg):
        SpecPe.__init__(self, mdata, xdata, ydata, cfg)
        self.update_mdata_reference(mdata['specTypeClass'], cfg)
        self.view = view.ViewPt(self)
             
        
    def __fit_peak_pos(self, peakPar):
        return [p[0] for p in peakPar]
    
    
    def __fit_peak_pos_trans(self, peakPar):
        return [np.sqrt(self._pFactor/(self._hv-p[0])) for p in peakPar]
    
    
    def __fit_par_init(self, peakPar, yscale, scale, offset):
        l = [i for p in peakPar if p[0] for i in [p[1]*yscale,p[2]]]
        l.extend([scale,offset])
        #l.extend([scale,offset])
        return np.array(l)


    def __fit_par_init_trans(self, peakPar, yscale, Eoff, toff, lscale):
        l = [i for p in peakPar if p[0] for i in [p[1]*yscale,p[2]]]
        #l = [i for p in peakPar if p[0] for i in [self.jtrans_inv(p[1]*yscale, np.sqrt(self._pFactor/(self._hv-p[0]))),p[2]]]
        l.extend([Eoff, toff, lscale])
        #print(l)
        return np.array(l)
    
    
    def __get_y_scale(self, xdata, ydata, xcenter, xinterval):
        xlb = np.abs(xdata-(xcenter-xinterval/2)).argmin()
        xub = np.abs(xdata-(xcenter+xinterval/2)).argmin()
        return ydata[xlb:xub].max()
    
    
    def multi_gauss(self, x, peak_pos, parList):
        plist = list(parList)
        xlist = list(peak_pos)
        gauss = lambda x, m,A,sigma,scale,offset: A*np.exp(-(x-(scale*m+offset))**2/(2*sigma**2))
        offset = plist.pop()
        scale = plist.pop()
        mgauss = 0
        while len(plist) > 0:
            sigma = plist.pop()
            A = plist.pop()
            m = xlist.pop()
            mgauss += gauss(x, m, A, sigma, scale, offset)
        return mgauss
    
    
    def multi_gauss_trans(self, t, peak_pos, parList):
        plist = list(parList)
        xlist = list(peak_pos)
        #gaussTrans = lambda t,m,A,s,toff,Eoff: A*np.exp(-(self._hv - self._pFactor*(1/(t + toff)**2 + 1/Eoff**2) - m)**2/(2*s**2))*2*self._pFactor/(t + toff)**3
        #gaussTrans = lambda t,m,A,sigma,toff,Eoff,lscale: A*np.exp(-(-self._pFactor*(1/(t)**2 + 1/Eoff**2 - 1/(l*m + toff)**2))**2/(2*s**2))*2*self._pFactor/(t)**3
        #gaussTrans = lambda t,m,A,sigma,toff,Eoff,lscale: A*2*self._pFactor/(t)**3*np.exp(-(self._pFactor*(1/(1/np.sqrt(1/t**2-Eoff/self._pFactor)-toff)**2/lscale**2 - 1/m**2))**2/(2*sigma**2))
        gaussTrans = lambda t,m,A,sigma,toff,Eoff,lscale: A*2*self._pFactor/(t)**3*np.exp(-(self._pFactor*(1/(1/(lscale*np.sqrt(1/t**2 - Eoff/self._pFactor)) - toff)**2 - 1/m**2))**2/(2*sigma**2))
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
    
    
    def __err_multi_gauss(self, p,x,y,peak_pos):
        return self.multi_gauss(x, peak_pos, p)-y
    
    
    def __err_multi_gauss_trans(self, p,t,y,peak_pos, constrain_par, constrain):
        'TODO: move to cfg or specify, when called.'
        c_par = constrain_par # -1: lscale, -2: toff, -3: Eoff
        c = constrain
        if c[0]<p[c_par]<c[1]: # only allow fits with toff (47-5)ns +- 5ns
        #if 1.0<p[-1]<1.007: # limit effective flight length to a maximum +0.007% 
            return self.multi_gauss_trans(t, peak_pos, p)-y
        else:
            return 1e6
#        return self.multi_gauss_trans(t, peak_pos, p)-y
    
    
    def __fit_multi_gauss(self, peakParRef, scale, offset, rel_y_min, cutoff):
        xdata = self.xdata['ebin']
        ydata = self.ydata['jIntensity']
        if cutoff == None:
            ebin_max = self.xdata['ebin'].max()
        elif 0 < cutoff < self.xdata['ebin'].max():
            ebin_max =cutoff
        else:
            raise ValueError('cutoff must be between 0 and %.2f'%(self.xdata['ebin'].max()))
        peakPar = [p for p in peakParRef if p[0]<ebin_max and p[1]>rel_y_min]
        fitValues = {'fitPeakPos': self.__fit_peak_pos(peakPar)}
        xcenter = fitValues['fitPeakPos'][0]
        yscale = self.__get_y_scale(xdata, ydata, xcenter, 0.2)
        fitValues['fitPar0'] = self.__fit_par_init(peakPar, yscale, scale, offset)
        p, covar, info, mess, ierr = leastsq(self.__err_mGauss, fitValues['fitPar0'],args=(xdata,ydata,fitValues['fitPeakPos']), full_output=True)
        fitValues.update({'fitPar': p, 'fitCovar': covar, 'fitInfo': [info, mess, ierr]})
        
        return fitValues


    def __fit_multi_gauss_trans(self, peakParRef, Eoff, toff, lscale, rel_y_min, cutoff, constrain_par, constrain):
        xdata = self.xdata['tof']
        ydata = self.ydata['intensity']
        if cutoff == None:
            tof_max = self.xdata['tof'].max()
        elif 0 < cutoff < self.xdata['tof'].max():
            tof_max =cutoff
        else:
            raise ValueError('cutoff must be between 0 and %.2f. Got %.1f instead.'%(self.xdata['tof'].max(), cutoff))
        peakPar = [p for p in peakParRef if np.sqrt(self._pFactor/(self._hv-p[0]))<tof_max and p[1]>rel_y_min]
        fitValues = {'fitPeakPosTof': self.__fit_peak_pos_trans(peakPar)}
        xcenter = peakParRef[0][0]
        yscale = self.__get_y_scale(self.xdata['ebin'], self.ydata['jIntensity'], xcenter, 0.4)
        fitValues['fitPar0Tof'] = self.__fit_par_init_trans(peakPar, yscale, Eoff, toff, lscale)
        try:
            p, covar, info, mess, ierr = leastsq(self.__err_mGaussTrans, fitValues['fitPar0Tof'], 
                                                 args=(xdata,ydata,
                                                       fitValues['fitPeakPosTof'],
                                                       constrain_par, constrain),
                                                 full_output=True)
        except:
            return fitValues
            raise
        else:
            fitValues.update({'fitParTof': p, 'fitCovarTof': covar, 'fitInfoTof': [info, mess, ierr]})
        
            return fitValues
       

    def gauge(self, specType,
              offset=0, rel_y_min=0, scale=1,
              lscale=1, Eoff=0, toff=42e-9, constrain_par=-2, constrain=[37e-9, 47e-9], 
              cutoff=None):
        'TODO: consistency of parameters.'
        '''
        Fits a multiple gauss to the pes.
        constrain_par: which parameter to constrain:  -1: lscale, -2: toff, -3: Eoff
        offset, scale: fit parameter
        rel_y_min: minimum peak height of reference peaks (cfg.pt_peakpar) to be included in the fit.
        '''
        peakParRef = self.cfg.pt_peakpar[self.mdata.data('waveLength')]
        try:
            if specType == 'ebin':
                fitValues = self.__fit_multi_gauss(peakParRef, scale, offset, rel_y_min, cutoff)
            elif specType == 'tof':
                fitValues = self.__fit_multi_gauss_trans(peakParRef, Eoff, toff, lscale, rel_y_min, cutoff,
                                                  constrain_par, constrain)
            else:
                raise ValueError('specType must be one of: "tof" or "ebin".')                
        except:
            #self.mdata.update(fitValues)
            raise
        else:
            self.mdata.update(fitValues)
            self.mdata.add_tag('gauged')



class SpecPeWater(SpecPe):
    def __init__(self, mdata, xdata, ydata, cfg):
        SpecPe.__init__(self, mdata, xdata, ydata, cfg)
        self.update_mdata_reference(mdata['specTypeClass'], cfg)
        self.view = view.ViewWater(self)


    def __gl(self, x, xmax, A, sg, sl):
        y = np.zeros(x.shape)
        y[x<=xmax] = A*np.exp(-(x[x<=xmax]-xmax)**2/(2*sg**2))
        y[x>xmax] = A/((x[x>xmax]-xmax)**2/(2*sl**2)+1)
        return y
    

    def __gl_trans(self, t, tmax, At, sg, sl):
        y = np.zeros(t.shape)
        q = constants.m_e/(2*constants.e)*(self.mdata.data('flightLength'))**2
        hv = self.photon_energy(self.mdata.data('waveLength'))
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
        self.update_mdata_reference(mdata['specTypeClass'], cfg)
        if len(self.xdata) == 1:
            self.calc_spec_data() 
        self.view = view.ViewMs(self)
        
        
    def calc_ms(self, xkey='amu', clusterBaseUnitMass=1):
#        self.xdata[xkey] = ((self.xdata['tof']/
#                             (self.mdata.data('referenceTime') - self.mdata.data('timeOffset'))
#                             )**2)*self.mdata.data('referenceMass')/clusterBaseUnitMass
        self.xdata[xkey] = ((self.xdata['tof']/
                             self.mdata.data('referenceTime'))**2)*self.mdata.data('referenceMass')/clusterBaseUnitMass
        
    
    def calc_spec_data(self):
        self.calc_tof(self.mdata.data('timeOffset'))
        self._fix_neg_intensities()
        self.calc_ms()
        self.calc_ms(xkey='ms', clusterBaseUnitMass=self.mdata.data('clusterBaseUnitMass'))
        
        
    def gauge(self, unit='cluster'):
        '''Simple gauge function. Needs to query for t1, t2, dn.
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
        self.mdata.update({'timeOffset':0, 'referenceTime':0})
        self.calc_tof(self.mdata.data('timeOffset'))
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





