import matplotlib.pyplot as plt
import os.path


class View(object):
    def __init__(self,spec):
        self.spec = spec
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(1,1,1)
        
        
    def _clearPlot(self):
        self.ax.lines = []
        self.ax.texts = []
            
            
    def showIdx(self):
        self._clearPlot()
        self.ax.set_xlabel('Index')
        self.ax.set_ylabel('Intensity (a.u.)')
        self.ax.set_xlim(0,self.spec.xdata['idx'][-1])
        self.ax.plot(self.spec.xdata['idx'], self.spec.ydata['intensity'], color='black')
        self.ax.relim()
        self.ax.autoscale(axis='y')
        textId = self.ax.text(1.0, 1.01, '%s'%(os.path.basename(self.spec.mdata.data('datFile'))),
                                  transform = self.ax.transAxes, fontsize=8, horizontalalignment='right')
        self.fig.show()
        
        
    def showTof(self, timeUnit=1e-6):
        '''TODO: adapt for more time units'''
        self._clearPlot()
        self.ax.set_xlabel(r'Flight Time ($\mu s$)')
        self.ax.set_ylabel('Intensity (a.u.)')
        self.ax.set_xlim(0,self.spec.xdata['tof'][-1]*timeUnit)
        self.ax.plot(self.spec.xdata['tof']*timeUnit, self.spec.ydata['intensity'], color='black')
        self.ax.relim()
        self.ax.autoscale(axis='y')
        textId = self.ax.text(1.0, 1.01, '%s'%(os.path.basename(self.spec.mdata.data('datFile'))),
                                  transform = self.ax.transAxes, fontsize=8, horizontalalignment='right')
        self.fig.show()
        
        
        
class ViewPes(View):
    def __init__(self, spec):
        View.__init__(self, spec)


    def showEkin(self):
        self._clearPlot()
        self.ax.set_xlabel(r'E$_{kin}$ (eV)')
        self.ax.set_ylabel('Intensity (a.u.)')
        self.ax.set_xlim(0,self.spec.photonEnergy(self.spec.mdata.data('waveLength')))
        self.ax.plot(self.spec.xdata['ekin'], self.spec.ydata['jacobyIntensity'], color='black')
        self.ax.relim()
        self.ax.autoscale(axis='y')
        textId = self.ax.text(1.0, 1.01, '%s'%(os.path.basename(self.spec.mdata.data('datFile'))),
                                  transform = self.ax.transAxes, fontsize=8, horizontalalignment='right')
        self.fig.show()


    def showEbin(self):
        self._clearPlot()
        self.ax.set_xlabel(r'E$_{bin}$ (eV)')
        self.ax.set_ylabel('Intensity (a.u.)')
        self.ax.set_xlim(0,self.spec.photonEnergy(self.spec.mdata.data('waveLength')))
        self.ax.plot(self.spec.xdata['ebin'], self.spec.ydata['jacobyIntensity'], color='black')
        self.ax.relim()
        self.ax.autoscale(axis='y')
        textId = self.ax.text(1.0, 1.01, '%s'%(os.path.basename(self.spec.mdata.data('datFile'))),
                                  transform = self.ax.transAxes, fontsize=8, horizontalalignment='right')
        self.fig.show()



class ViewPt(ViewPes):
    def __init__(self,spec):
        ViewPes.__init__(self, spec)
        
        
    def showEbinFit(self, fitPar='fitPar'):
        self._clearPlot()
        if fitPar in self.spec.mdata.data().keys():
            self.showEbin()
            self.ax.plot(self.spec.xdata['ebin'],
                         self.spec.mGauss(self.spec.xdata['ebin'],self.spec.mdata.data('fitPeakPos'),self.spec.mdata.data(fitPar)),
                         color='blue')
            self.ax.relim()
            self.ax.autoscale(axis='y')
            textOffset = self.ax.text(0.05, 0.9, 'Offset: %s meV'%(round(self.spec.mdata.data('fitPar')[-1]*1e3, 2)),
                                      transform = self.spec.view.ax.transAxes, fontsize=12)
            textScale = self.ax.text(0.05, 0.85, 'Scale: %s'%(round(self.spec.mdata.data('fitPar')[-2], 2)),
                                     transform = self.spec.view.ax.transAxes, fontsize=12)
            self.fig.show()
        else:
            raise ValueError('Spectrum not gauged. Gauge first.')
        
        
class ViewWater(ViewPes):
    def __init__(self,spec):
        ViewPes.__init__(self, spec)
        
        
    def showEbinFit(self, fitPar='fitPar'):
        self._clearPlot()
        if fitPar in self.spec.mdata.data().keys():
            self.showEbin()
            self.ax.plot(self.spec.xdata['ebin'],
                         self.spec.mGl(self.spec.xdata['ebin'], self.spec.mdata.data(fitPar)),
                         color='blue')
            self.ax.relim()
            plist = list(self.spec.mdata.data(fitPar))
            sl = plist.pop()
            sg = plist.pop()
            while len(plist) >= 2:
                A = plist.pop()
                xmax = plist.pop()
                self.ax.plot(self.spec.xdata['ebin'],
                         self.spec.mGl(self.spec.xdata['ebin'], [xmax,A,sg,sl]),
                         color='DimGray')
            self.fig.show()
        else:
            raise ValueError('Spectrum not yet fitted. Fit first.')






        