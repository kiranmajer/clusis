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
        
    
    
    def commitDb(self, update=False):
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
            
            
    def commit(self, update=False):
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
        if len(self.xdata) == 1:
            self.calcSpec()
        #print 'Assigning view.ViewPes'
        self.view = view.ViewPes(self)
    
    def __calcEkin(self):
        self.xdata['ekin'] = constants.m_e/(2*constants.e)*(self.mdata.data('flightLength')/self.xdata['tof'])**2
    
    def __calcEbin(self):
        self.xdata['ebin'] = self.photonEnergy(self.mdata.data('waveLength')) - self.xdata['ekin']
        
    def __calcJacobyIntensity(self, ydataKey='intensity', newKey='jacobyIntensity'):
        self.ydata[newKey] = self.ydata[ydataKey]/(2*self.xdata['ekin']/self.xdata['tof'])
        
    def __calcEbinGauged(self):
        self.xdata['ebinGauged'] = (self.xdata['ebin'] - self.mdata.data('gaugePar')['offset'])/self.mdata.data('gaugePar')['scale']
        
    
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
        self.__calcEbinGauged()
        self.commitPickle()
        del gaugeSpec
        
    def subtractBg(self, bgFile, isUpDown=True):
        Spec.subtractBg(self, bgFile, isUpDown=isUpDown)
        self.__calcJacobyIntensity(ydataKey='intensitySub', newKey='jacobyIntensitySub')
        self.commitPickle()
        
        
class ptSpec(peSpec):
    def __init__(self, mdata, xdata, ydata, cfg):
        peSpec.__init__(self, mdata, xdata, ydata, cfg)
        self.view = view.ViewPt(self)
             
        
    def __fitPeakPos(self, peakPar):
        return [p[0] for p in peakPar]
    
    
    def __fitParInit(self, peakPar, yscale, scale, offset):
        l = [i for p in peakPar if p[0] for i in [p[1]*yscale,p[2]]]
        l.extend([scale,offset])
        return l
    
    
    def __getScale(self, xdata, ydata, xcenter, xinterval):
        xlb = np.abs(xdata-(xcenter-xinterval/2)).argmin()
        xub = np.abs(xdata-(xcenter+xinterval/2)).argmin()
        return ydata[xlb:xub].max()
    
    
    def mGauss(self, x, peak_pos, parList):
        plist = list(parList)
        xlist = list(peak_pos)
        gauss = lambda x, m,A,s,scale,offset: A*np.exp(-(x-(scale*m+offset))**2/(2*s**2))
        offset = plist.pop()
        scale = plist.pop()
        mgauss = 0
        while len(plist) > 0:
            s = plist.pop()
            A = plist.pop()
            m = xlist.pop()
            mgauss += gauss(x, m, A, s, scale, offset)
        return mgauss
    
    
    def __err_mGauss(self, p,x,y,peak_pos):
        return self.mGauss(x, peak_pos, p)-y
    
    
    def __fitMgauss(self, peakParRef, scale, offset, rel_y_min):
        xdata = self.xdata['ebin']
        ydata = self.ydata['jacobyIntensity']
        ebin_max = self.xdata['ebin'].max()
        peakPar = [p for p in peakParRef if p[0]<ebin_max and p[1]>rel_y_min]
        fitValues = {'fitPeakPos': self.__fitPeakPos(peakPar)}
        xcenter = fitValues['fitPeakPos'][0]
        yscale = self.__getScale(xdata, ydata, xcenter, 0.2)
        fitValues['fitPar0'] = self.__fitParInit(peakPar, yscale, scale, offset)
        p, covar, info, mess, ierr = leastsq(self.__err_mGauss, fitValues['fitPar0'],args=(xdata,ydata,fitValues['fitPeakPos']), full_output=True)
        fitValues.update({'fitPar': p, 'fitCovar': covar, 'fitInfo': [info, mess, ierr]})
        
        return fitValues
        

    def gauge(self, offset=0, rel_y_min=0, scale=1):
        '''
        Fits a multiple gauss to the pes.
        offset, scale: fit parameter
        rel_y_min: minimum peak height of reference peaks (cfg.ptPeakPar) to be included in the fit.
        '''
        peakParRef = self.cfg.ptPeakPar[self.mdata.data('waveLength')]
        try:
            fitValues = self.__fitMgauss(peakParRef, scale, offset, rel_y_min)
        except:
            self.mdata.update(fitValues)
            raise
        else:
            self.mdata.update(fitValues)



class waterSpec(peSpec):
    def __init__(self, mdata, xdata, ydata, cfg):
        peSpec.__init__(self, mdata, xdata, ydata, cfg)
        self.view = view.ViewWater(self)


    def __gl(self, x, xmax, A, sg, sl):
        y = np.zeros(x.shape)
        y[x<=xmax] = A*np.exp(-(x[x<=xmax]-xmax)**2/(2*sg**2))
        y[x>xmax] = A/((x[x>xmax]-xmax)**2/(2*sl**2)+1)
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
    
    def __err_mGl(self, par, x, y):
        return self.mGl(x, par)-y
    
    
    def __fitGl(self, p0, cutoff):
        xdata = self.xdata['ebin']
        ydata = np.copy(self.ydata['jacobyIntensity'])
        fitValues = {'fitPar0': p0, 'fitCutoff': cutoff}
        if type(cutoff) in [int,float]:
            ydata[xdata>cutoff] = xdata[xdata>cutoff]*0
        p, covar, info, mess, ierr = leastsq(self.__err_mGl, p0, args=(xdata,ydata), full_output=True)
        fitValues.update({'fitPar': p, 'fitCovar': covar, 'fitInfo': [info, mess, ierr]})
        
        return fitValues
    
    
    def fit(self, p0, cutoff=None):
        
        try:
            fitValues = self.__fitGl( p0, cutoff)
        except:
            self.mdata.add(fitValues)
            raise
        else:
            self.mdata.add(fitValues)




class mSpec(Spec):
    def calcSpec(self):
        self.__calcTof()
        
        

class pfSpec(Spec):
    def calcSpec(self):
        self.__calcTof()





