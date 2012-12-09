from __future__ import unicode_literals
from legacyData import *
import scipy.constants as constants
#from plotlibs import *
from dbshell import *
#from recursive_import import *
#from pes_sheet import *
#from msplot import *
from scipy.optimize import leastsq
import view
import pickle
import load





class Spec(object):
    def __init__(self, mdata, xdata, ydata, cfg):
        self.mdata = MdataUtils.Mdata(mdata, cfg)
        self.xdata = xdata
        self.ydata = ydata
        self.cfg = cfg
        
    
    
    def commitDb(self, update=True):
        with Db(self.mdata.data('machine'), self.cfg) as db:
            db.add(self, update=update)
        
        
    def commitPickle(self):
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
        self.commitPickle()
        self.commitDb(update=update)
        
    '''TODO: make privat'''    
    def calcTof(self):
        self.xdata['tof'] = self.xdata['idx']*self.mdata.data('timePerPoint')-self.mdata.data('triggerOffset')-self.mdata.data('timeOffset')

    def photonEnergy(self, waveLength):
        """Calculates photon energy in eV for a given wave length.
        
        Returns: float."""
        photonEnergy = constants.h*constants.c/(constants.e*waveLength)
        
        return photonEnergy
        
    def _fixNegIntensities(self, ydataKey='rawIntensity', newKey='intensity'):
        """
        The Oscilloscope sets the value for bins without counts to the value of the frame of display.
        So it's safe to set them to 0. 
        """
        fixedIntensity = (self.ydata[ydataKey] + np.abs(self.ydata[ydataKey]))/2
        self.ydata[newKey] = fixedIntensity
    
    def __calcSubIntensities(self, bgSpec):
        self.ydata['intensitySubRaw'] = self.ydata['intensity'] - bgSpec.ydata['intensity']
        self._fixNegIntensities('intensitySubRaw', 'intensitySub')
    
    def subtractBg(self, bgFile, isUpDown=False):
        bgSpec = load.loadPickle(self.cfg, bgFile)
        if not self.mdata.data('specType') == bgSpec.mdata.data('specType'):
            raise ValueError('Background file has different spec type.')
        self.mdata.update({'bgFile': bgFile})
        'TODO: tag managment. Right now the same tag(s) is(are) added, each time subtractGb is called.'
        if isUpDown:
            bgSpec.mdata.update({'tags': ['background', 'up/down'], 'specFile': self.mdata.data('pickleFile')})
            self.mdata.update({'tags': ['up/down']})
        else:
            bgSpec.mdata.update({'tags': ['background'], 'specFile': self.mdata.data('pickleFile')})
        self.__calcSubIntensities(bgSpec)
        self.commitPickle()
        bgSpec.commitPickle()


        

class peSpec(Spec):
    def __init__(self, mdata, xdata, ydata, cfg):
        print '__init__: Init peSpec'
        Spec.__init__(self, mdata, xdata, ydata, cfg)
        self._pFactor = constants.m_e/(2*constants.e)*(self.mdata.data('flightLength'))**2
        self._hv = self.photonEnergy(self.mdata.data('waveLength'))
        if len(self.xdata) == 1:
            self.calcSpec()
        #print 'Assigning view.ViewPes'
        self.view = view.ViewPes(self)
        
    def ebin(self, t, gauge_scale=1, gauge_offset=0):
        return (self._hv-self._pFactor/t**2 - gauge_offset)/gauge_scale

    def ekin(self, t, gauge_scale=1, gauge_offset=0):
        return self._hv - self.ebin(t, gauge_scale, gauge_offset)
        
    def tGauged(self, t, gauge_scale, gauge_offset):
        return np.sqrt(self._pFactor/self.ekin(t, gauge_scale, gauge_offset))
        
    def jTrans(self, intensity, t):
        return intensity*t**3/(2*self._pFactor)
    
    def jTransInv(self, intensity, t):
        return intensity*2*self._pFactor/t**3
    
    
    def __calcEkin(self, newKey='ekin', gauge_scale=1, gauge_offset=0):
        self.xdata[newKey] = self.ekin(self.xdata['tof'], gauge_scale, gauge_offset) 
        #self.xdata['ekin'] = constants.m_e/(2*constants.e)*(self.mdata.data('flightLength')/self.xdata['tof'])**2
    
    def __calcEbin(self, newKey='ebin', gauge_scale=1, gauge_offset=0):
        self.xdata[newKey] = self.ebin(self.xdata['tof'], gauge_scale, gauge_offset)
        #self.xdata['ebin'] = self.photonEnergy(self.mdata.data('waveLength')) - self.xdata['ekin']
        
    def __calcJacobyIntensity(self, newKey='jacobyIntensity', intensityKey='intensity', tofKey='tof'):
        self.ydata[newKey] = self.jTrans(self.ydata[intensityKey], self.xdata[tofKey])
        #self.ydata[newKey] = self.ydata[ydataKey]/(2*self.xdata['ekin']/self.xdata['tof'])
        
#    def __calcEbinGauged(self):
#        self.xdata['ebinGauged'] = (self.xdata['ebin'] - self.mdata.data('gaugePar')['offset'])/self.mdata.data('gaugePar')['scale']
        
    
    def calcSpec(self):
        self.calcTof()
        self.__calcEkin()
        self.__calcEbin()
        self._fixNegIntensities()
        self.__calcJacobyIntensity()
        
        
    def gauge(self, gaugeRef):
        self.mdata.update({'gaugeRef': gaugeRef})
        gaugeSpec = load.loadPickle(self.cfg, gaugeRef)
        scale, offset = gaugeSpec.mdata.data('fitPar')[-2:]
        self.mdata.update({'gaugePar': {'scale': scale, 'offset': offset}})
        # calc xdata gauged
        self.__calcEbin(newKey='ebinGauged', gauge_scale=scale, gauge_offset=offset)
        self.__calcEkin(newKey='ekinGauged', gauge_scale=scale, gauge_offset=offset)
        self.xdata['tofGauged'] = self.tGauged(self.xdata['tof'], gauge_scale=scale, gauge_offset=offset)
        # calc ydata gauged
        self.__calcJacobyIntensity(newKey='jacobyIntensityGauged', intensityKey='intensity', tofKey='tofGauged')
        if 'jacobyIntensitySub' in self.ydata.keys():
            self.__calcJacobyIntensity(newKey='jacobyIntensityGaugedSub',
                                       intensityKey='intensitySub', tofKey='tofGauged')
        self.commitPickle()
        del gaugeSpec
        
    def subtractBg(self, bgFile, isUpDown=True):
        Spec.subtractBg(self, bgFile, isUpDown=isUpDown)
        self.__calcJacobyIntensity(newKey='jacobyIntensitySub', intensityKey='intensitySub')
        if 'gaugePar' in self.mdata.data().keys():
            self.__calcJacobyIntensity(newKey='jacobyIntensityGaugedSub',
                                       intensityKey='intensitySub', tofKey='tofGauged')
            
        self.commitPickle()
        
        
class ptSpec(peSpec):
    def __init__(self, mdata, xdata, ydata, cfg):
        peSpec.__init__(self, mdata, xdata, ydata, cfg)
        self.view = view.ViewPt(self)
             
        
    def __fitPeakPos(self, peakPar):
        return [p[0] for p in peakPar]
    
    
    def __fitPeakPosTrans(self, peakPar):
        return [np.sqrt(self._pFactor/(self._hv-p[0])) for p in peakPar]
    
    
    def __fitParInit(self, peakPar, yscale, scale, offset, lscale):
        l = [i for p in peakPar if p[0] for i in [p[1]*yscale,p[2]]]
        l.extend([scale,offset,lscale])
        #l.extend([scale,offset])
        return l


    def __fitParInitTrans(self, peakPar, yscale, scale, offset):
        l = [i for p in peakPar if p[0] for i in [self.jTransInv(p[1]*yscale, np.sqrt(self._pFactor/(self._hv-p[0]))),p[2]]]
        l.extend([scale,offset])
        return l
    
    
    def __getScale(self, xdata, ydata, xcenter, xinterval):
        xlb = np.abs(xdata-(xcenter-xinterval/2)).argmin()
        xub = np.abs(xdata-(xcenter+xinterval/2)).argmin()
        return ydata[xlb:xub].max()
    
    
    def mGauss(self, x, peak_pos, parList):
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
    
    
    def mGaussTrans(self, t, peak_pos, parList):
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
    
    
    def __err_mGauss(self, p,x,y,peak_pos):
        return self.mGauss(x, peak_pos, p)-y
    
    
    def __err_mGaussTrans(self, p,t,y,peak_pos):
        'TODO: move to cfg.'
        #if p[-2]>50e-9: # only allow fits with toff > 50ns
        if 1.009<p[-1]<1.013:
            return self.mGaussTrans(t, peak_pos, p)-y
        else:
            return 1e6
#        return self.mGaussTrans(t, peak_pos, p)-y
    
    
    def __fitMgauss(self, peakParRef, scale, offset, rel_y_min, cutoff):
        xdata = self.xdata['ebin']
        ydata = self.ydata['jacobyIntensity']
        if cutoff == None:
            ebin_max = self.xdata['ebin'].max()
        elif 0 < cutoff < self.xdata['ebin'].max():
            ebin_max =cutoff
        else:
            raise ValueError('cutoff must be between 0 and %.2f'%(self.xdata['ebin'].max()))
        peakPar = [p for p in peakParRef if p[0]<ebin_max and p[1]>rel_y_min]
        fitValues = {'fitPeakPos': self.__fitPeakPos(peakPar)}
        xcenter = fitValues['fitPeakPos'][0]
        yscale = self.__getScale(xdata, ydata, xcenter, 0.2)
        fitValues['fitPar0'] = self.__fitParInit(peakPar, yscale, scale, offset)
        p, covar, info, mess, ierr = leastsq(self.__err_mGauss, fitValues['fitPar0'],args=(xdata,ydata,fitValues['fitPeakPos']), full_output=True)
        fitValues.update({'fitPar': p, 'fitCovar': covar, 'fitInfo': [info, mess, ierr]})
        
        return fitValues


    def __fitMgaussTrans(self, peakParRef, Eoff, toff, lscale, rel_y_min, cutoff):
        xdata = self.xdata['tof']
        ydata = self.ydata['intensity']
        if cutoff == None:
            tof_max = self.xdata['tof'].max()
        elif 0 < cutoff < self.xdata['tof'].max():
            tof_max =cutoff
        else:
            raise ValueError('cutoff must be between 0 and %.2f. Got %.1f instead.'%(self.xdata['tof'].max(), cutoff))
        peakPar = [p for p in peakParRef if np.sqrt(self._pFactor/(self._hv-p[0]))<tof_max and p[1]>rel_y_min]
        fitValues = {'fitPeakPosTof': self.__fitPeakPosTrans(peakPar)}
        xcenter = peakParRef[0][0]
        yscale = self.__getScale(self.xdata['ebin'], self.ydata['jacobyIntensity'], xcenter, 0.4)
        fitValues['fitPar0Tof'] = self.__fitParInit(peakPar, yscale, Eoff, toff, lscale)
        p, covar, info, mess, ierr = leastsq(self.__err_mGaussTrans, fitValues['fitPar0Tof'], 
                                             args=(xdata,ydata,fitValues['fitPeakPosTof']), full_output=True)
        fitValues.update({'fitParTof': p, 'fitCovarTof': covar, 'fitInfoTof': [info, mess, ierr]})
        
        return fitValues
       

    def gauge(self, specType, offset=0, rel_y_min=0, scale=1, lscale=1, Eoff=0, toff=63e-9, cutoff=None):
        '''
        Fits a multiple gauss to the pes.
        offset, scale: fit parameter
        rel_y_min: minimum peak height of reference peaks (cfg.ptPeakPar) to be included in the fit.
        '''
        peakParRef = self.cfg.ptPeakPar[self.mdata.data('waveLength')]
        try:
            if specType == 'ebin':
                fitValues = self.__fitMgauss(peakParRef, scale, offset, rel_y_min, cutoff)
            elif specType == 'tof':
                fitValues = self.__fitMgaussTrans(peakParRef, Eoff, toff, lscale, rel_y_min, cutoff)
            else:
                raise ValueError('specType must be one of: "tof" or "ebin".')                
        except:
            #self.mdata.update(fitValues)
            raise
        else:
            self.mdata.update(fitValues)
            self.mdata.addTag('gauged')



class waterSpec(peSpec):
    def __init__(self, mdata, xdata, ydata, cfg):
        peSpec.__init__(self, mdata, xdata, ydata, cfg)
        self.view = view.ViewWater(self)


    def __gl(self, x, xmax, A, sg, sl):
        y = np.zeros(x.shape)
        y[x<=xmax] = A*np.exp(-(x[x<=xmax]-xmax)**2/(2*sg**2))
        y[x>xmax] = A/((x[x>xmax]-xmax)**2/(2*sl**2)+1)
        return y
    

    def __glTrans(self, t, tmax, At, sg, sl):
        y = np.zeros(t.shape)
        q = constants.m_e/(2*constants.e)*(self.mdata.data('flightLength'))**2
        hv = self.photonEnergy(self.mdata.data('waveLength'))
        ebin = lambda t: hv - q/t**2
        xmax = ebin(tmax)
        A = At*tmax/(2*(hv-xmax))
        y[t<=tmax] = A*np.exp(-(ebin(t[t<=tmax])-xmax)**2/(2*sg**2))*2*q/t[t<=tmax]**3
        y[t>tmax] = A/((ebin(t[t>tmax])-xmax)**2/(2*sl**2)+1)*2*q/t[t>tmax]**3
        return y
    
    
    def mGl(self, x, par):
        plist = list(par)
        mgl = 0
        sl =plist.pop()
        sg = plist.pop()
        while len(plist) > 0:
            A = plist.pop()
            xmax = plist.pop()
            mgl+=self.__gl(x, xmax, A, sg, sl)
        return mgl
    
    def mGlTrans(self, x, par):
        plist = list(par)
        mgl = 0
        sl =plist.pop()
        sg = plist.pop()
        while len(plist) > 0:
            A = plist.pop()
            xmax = plist.pop()
            mgl+=self.__glTrans(x, xmax, A, sg, sl)
        return mgl    
    
    
    def __err_mGl(self, par, x, y):
        return self.mGl(x, par)-y
    
    def __err_mGlTrans(self, par, x, y):
        return self.mGlTrans(x, par)-y    
    
    
    def __fitGl(self, p0, cutoff, subtractBg, gauged):
        if gauged:
            ebin_key = 'ebinGauged'
        else:
            ebin_key = 'ebin'
            
        if subtractBg:
            int_key = 'jacobyIntensitySub'
        else:
            int_key = 'jacobyIntensity'
            
        if type(cutoff) in [int,float]:
            xdata = self.xdata[ebin_key][self.xdata[ebin_key]<cutoff]
            ydata = self.ydata[int_key][:len(xdata)]
        elif cutoff == None:
            xdata = self.xdata[ebin_key]
            ydata = np.copy(self.ydata[int_key])
        else:
            raise ValueError('Cutoff must be int or float')
        
        fitValues = {'fitPar0': p0, 'fitCutoff': cutoff, 'fitGauged': gauged, 'fitSubtractBg': subtractBg}
        p, covar, info, mess, ierr = leastsq(self.__err_mGl, p0, args=(xdata,ydata), full_output=True)
        fitValues.update({'fitPar': p, 'fitCovar': covar, 'fitInfo': [info, mess, ierr]})
        
        return fitValues
 
 
    def __fitGlTrans(self, p0, cutoff, subtractBg, gauged):
        if gauged:
            tof_key = 'tofGauged'
        else:
            tof_key = 'tof'
            
        if subtractBg:
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
        
        fitValues = {'fitPar0Tof': p0, 'fitCutoffTof': cutoff, 'fitGaugedTof': gauged, 'fitSubtractBgTof': subtractBg}
        p, covar, info, mess, ierr = leastsq(self.__err_mGlTrans, p0, args=(xdata,ydata), full_output=True)
        fitValues.update({'fitParTof': p, 'fitCovarTof': covar, 'fitInfoTof': [info, mess, ierr]})
        
        return fitValues 
    
    
    def fit(self, specType, p0, cutoff=None, subtractBg=None, gauged=None):
        '''If subtractBg and/or gauged are None, try to find useful defaults.'''
        if subtractBg == None:
            if 'bgFile' in self.mdata.data().keys():
                subtractBg = True
            else:
                subtractBg = False
        if gauged == None:
            if 'gaugeRef' in self.mdata.data().keys():
                gauged = True
            else:
                gauged =False
        
        try:
            if specType == 'ebin':
                fitValues = self.__fitGl(p0, cutoff, subtractBg, gauged)
            elif specType == 'tof':
                fitValues = self.__fitGlTrans(p0, cutoff, subtractBg, gauged)
            else:
                raise ValueError('specType must be one of: "tof" or "ebin".')
        except:
            #self.mdata.update(fitValues)
            raise
        else:
            print 'Fit completed, Updating mdata...'
            self.mdata.update(fitValues)


#    def fitTof(self, p0, cutoff=None, subtractBg=None, gauged=None):
#        '''If subtractBg and/or gauged are None, try to find useful defaults.'''
#        if subtractBg == None:
#            if 'bgFile' in self.mdata.data().keys():
#                subtractBg = True
#            else:
#                subtractBg = False
#        if gauged == None:
#            if 'gaugeRef' in self.mdata.data().keys():
#                gauged = True
#            else:
#                gauged =False
#        
#        try:
#            fitValues = self.__fitGlTrans(p0, cutoff, subtractBg, gauged)
#        except:
#            #self.mdata.update(fitValues)
#            raise
#        else:
#            print 'Fit completed, Updating mdata...'
#            self.mdata.update(fitValues)



class mSpec(Spec):
    def calcSpec(self):
        self.__calcTof()
        
        

class pfSpec(Spec):
    def calcSpec(self):
        self.__calcTof()





