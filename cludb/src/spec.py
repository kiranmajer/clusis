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





class Spec(object):
    def __init__(self, mdata, xdata, ydata, cfg):
        self.mdata = MdataUtils.Mdata(mdata)
        self.xdata = xdata
        self.ydata = ydata
        self.cfg = cfg
        
    
    
    def commitDb(self, mdata):
        with Db(self.mdata.data('machine'), self.cfg) as db:
            db.add(mdata)
        
        
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
            
            
    def commit(self):
        self.commitPickle()
        self.commitDb(self.mdata.data())
        
    '''TODO: make privat'''    
    def calcTof(self):
        self.xdata['tof'] = self.xdata['idx']*self.mdata.data('timePerPoint')-self.mdata.data('triggerOffset')-self.mdata.data('timeOffset')

    def photonEnergy(self, waveLength):
        """Calculates photon energy in eV for a given wave length.
        
        Returns: float."""
        photonEnergy = constants.h*constants.c/(constants.e*waveLength)
        
        return photonEnergy


        

class peSpec(Spec):
    def __init__(self, mdata, xdata, ydata, cfg):
        Spec.__init__(self, mdata, xdata, ydata, cfg)
        if len(self.xdata) == 1:
            self.calcSpec()
        self.view = view.ViewPes(self)
    
    def __calcEkin(self):
        self.xdata['ekin'] = constants.m_e/(2*constants.e)*(self.mdata.data('flightLength')/self.xdata['tof'])**2
    
    def __calcEbin(self):
        self.xdata['ebin'] = self.photonEnergy(self.mdata.data('waveLength')) - self.xdata['ekin']
        
    def __fixNegIntensities(self):
        """
        The Oscilloscope sets the value for bins without counts to the value of the frame of display.
        So it's safe to set them to 0. 
        """
        fixedIntensity = (self.ydata['rawIntensity'] + np.abs(self.ydata['rawIntensity']))/2
        self.ydata['intensity'] = fixedIntensity
        
    def __calcJacobyIntensity(self):
        self.ydata['jacobyIntensity'] = self.ydata['intensity']/(2*self.xdata['ekin']/self.xdata['tof'])
    
    def calcSpec(self):
        self.calcTof()
        self.__calcEkin()
        self.__calcEbin()
        self.__fixNegIntensities()
        self.__calcJacobyIntensity()
        
        
        
class ptSpec(peSpec):
    def __init__(self, mdata, xdata, ydata, cfg):
        peSpec.__init__(self, mdata, xdata, ydata, cfg)
        self.view = view.ViewPt(self)
             
        
    def __fitPeakPos(self):
        return [p[0] for p in self.cfg.ptPeakPar[self.mdata.data('waveLength')]]
    
    
    def __fitParInit(self, scale, a, b):
        l = [i for p in self.cfg.ptPeakPar[self.mdata.data('waveLength')] for i in [p[1]*scale,p[2]]]
        l.extend([a,b])
        return l
    
    
    def __getScale(self, xdata, ydata, xcenter, xinterval):
        xlb = np.abs(xdata-(xcenter-xinterval/2)).argmin()
        xub = np.abs(xdata-(xcenter+xinterval/2)).argmin()
        return ydata[xlb:xub].max()
    
    
    def mGauss(self, x, peak_pos, parList):
        plist = list(parList)
        xlist = list(peak_pos)
        gauss = lambda x, m,A,s,a,b: A*np.exp(-(x-(a*m+b))**2/(2*s**2))
        b = plist.pop()
        a = plist.pop()
        mgauss = 0
        while len(plist) > 0:
            s = plist.pop()
            A = plist.pop()
            m = xlist.pop()
            mgauss += gauss(x, m, A, s, a, b)
        return mgauss
    
    
    def __err_mGauss(self, p,x,y,peak_pos):
        return self.mGauss(x, peak_pos, p)-y
    
    
    def __fitMgauss(self, a, b):
        xdata = self.xdata['ebin']
        ydata = self.ydata['jacobyIntensity']
        fitValues = {'fitPeakPos': self.__fitPeakPos()}
        xcenter = fitValues['fitPeakPos'][0]
        scale = self.__getScale(xdata, ydata, xcenter, 0.2)
        fitValues['fitPar0'] = self.__fitParInit(scale, a, b)
        p, covar, info, mess, ierr = leastsq(self.__err_mGauss, fitValues['fitPar0'],args=(xdata,ydata,fitValues['fitPeakPos']), full_output=True)
        fitValues.update({'fitPar': p, 'fitCovar': covar, 'fitInfo': [info, mess, ierr]})
        
        return fitValues
        

    def gauge(self, a=1, b=0):
        try:
            fitValues = self.__fitMgauss( a, b)
        except:
            self.mdata.add(fitValues)
            raise
        else:
            self.mdata.add(fitValues)



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





