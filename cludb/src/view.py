from __future__ import unicode_literals
import matplotlib.pyplot as plt
import os.path
import load

class View(object):
    def __init__(self,spec):
        #print '__init__: Initializing View object.'
        self.spec = spec
        

    def _singleFig(self):
        if hasattr(self, 'fig'):        
            self.ax.lines = []
            self.ax.texts = []
        else:
            self.fig = plt.figure()
            #print 'Figure created.'
            self.ax = self.fig.add_subplot(1,1,1)    


    def addTextFileId(self, ax):
        ax.text(1.0, 1.01, '%s'%(os.path.basename(self.spec.mdata.data('datFile'))),
                transform = self.ax.transAxes, fontsize=8, horizontalalignment='right')  


    def plotIdx(self, ax):
        ax.set_xlabel('Index')
        ax.set_ylabel('Intensity (a.u.)')
        ax.set_xlim(0,self.spec.xdata['idx'][-1])
        ax.plot(self.spec.xdata['idx'], self.spec.ydata['intensity'], color='black')
        ax.relim()
        ax.autoscale(axis='y')       
            
            
    def showIdx(self):
        self._singleFig()
        self.plotIdx(self.ax)
        self.addTextFileId(self.ax)
        self.fig.show()
        
        
    def plotTof(self, ax, timeUnit=1e-6):
        'TODO: adapt for more time units'
        ax.set_xlabel(r'Flight Time ($\mu s$)')
        ax.set_ylabel('Intensity (a.u.)')
        ax.set_xlim(0,self.spec.xdata['tof'][-1]/timeUnit)
        ax.plot(self.spec.xdata['tof']/timeUnit, self.spec.ydata['intensity'], color='black')
        ax.relim()
        ax.autoscale(axis='y')


    def showTof(self):
        self._singleFig()
        self.plotTof(self.ax)        
        self.addTextFileId(self.ax)
        self.fig.show()
        
        
        
class ViewPes(View):
    def __init__(self, spec):
        View.__init__(self, spec)
        
        
    def addTextGaugeMarker(self, ax):
        ax.text(0, 1.01, 'gauged', transform = self.ax.transAxes, fontsize=8, horizontalalignment='left') 
        
        
    def addTextClusterId(self, ax, textPos='left', fontsize=28):
        if textPos == 'left':
            pos_x, pos_y = 0.05, 0.8
        elif textPos == 'right':
            pos_x, pos_y = 0.95, 0.8
        else:
            raise ValueError('textPos must be one of: left, right. Got "%s" instead.'%(str(textPos)))  
        formatStart = '$\mathrm{\mathsf{'
        formatEnd = '}}$'
        partCluster = '{%s'%self.spec.mdata.data('clusterBaseUnit')
        partClusterNumber = '_{%s}'%(str(self.spec.mdata.data('clusterBaseUnitNumber')))
        partCharge = '}^{%s}'%self.spec.mdata.data('ionType')
        partDopant = '{%s}'%self.spec.mdata.data('clusterDopant')
        partDopantNumber = '_{%s}'%(str(self.spec.mdata.data('clusterDopantNumber')))
        
        clusterId = formatStart + partCluster
        if self.spec.mdata.data('clusterBaseUnitNumber') > 1:
            clusterId += partClusterNumber
        if self.spec.mdata.data('clusterDopant'):
            clusterId += partDopant
            if self.spec.mdata.data('clusterDopantNumber') > 1:
                clusterId += partDopantNumber
        clusterId += partCharge
        clusterId += formatEnd
               
        ax.text(pos_x, pos_y, clusterId, transform = ax.transAxes, fontsize=fontsize, horizontalalignment=textPos)
        

    def showIdx(self):
        View.showIdx(self)
        self.addTextClusterId(self.ax)        
        self.fig.show()

        
    def showTof(self):
        View.showTof(self)
        self.addTextClusterId(self.ax)        
        self.fig.show()
        

    def plotEkin(self, ax):
        ax.set_xlabel(r'E$_{kin}$ (eV)')
        ax.set_ylabel('Intensity (a.u.)')
        ax.set_xlim(0,self.spec.photonEnergy(self.spec.mdata.data('waveLength')))
        ax.plot(self.spec.xdata['ekin'], self.spec.ydata['jacobyIntensity'], color='black')
        ax.relim()
        ax.autoscale(axis='y')


    def showEkin(self):  
        self._singleFig()
        self.plotEkin(self.ax)        
        self.addTextFileId(self.ax)
        self.addTextClusterId(self.ax, textPos='right')        
        self.fig.show()


    def plotEbin(self, ax, showGauged=False):
        ax.set_xlabel(r'E$_{bin}$ (eV)')
        ax.set_ylabel('Intensity (a.u.)')
        ax.set_xlim(0,self.spec.photonEnergy(self.spec.mdata.data('waveLength')))
        gauged = False
        if 'ebinGauged' in self.spec.xdata.keys():
            if showGauged:
                ebin = self.spec.xdata['ebinGauged']
                gauged = True
            else:
                ebin = self.spec.xdata['ebin']
        else:
            ebin = self.spec.xdata['ebin']
        ax.plot(ebin, self.spec.ydata['jacobyIntensity'], color='black')
        ax.relim()
        ax.autoscale(axis='y')
        
        return gauged


    def showEbin(self, showGauged=True):
        self._singleFig()
        gauged = self.plotEbin(self.ax, showGauged)
        if gauged:
            self.addTextGaugeMarker(self.ax)        
        self.addTextFileId(self.ax)
        self.addTextClusterId(self.ax)             
        self.fig.show()
        
        
    def showGaugeRef(self):
        gaugeRef = self.spec.mdata.data('gaugeRef')
        gaugeSpec = load.loadPickle(self.spec.cfg, gaugeRef)
        gaugeSpec.view.showEbinFit()
        


class ViewPt(ViewPes):
    def __init__(self,spec):
        ViewPes.__init__(self, spec)
        
    
    def addTextGaugePar(self, ax):
        textOffset = ax.text(0.05, 0.6, 'Offset: %s meV'%(round(self.spec.mdata.data('fitPar')[-1]*1e3, 2)),
                                  transform = self.spec.view.ax.transAxes, fontsize=12)
        textScale = ax.text(0.05, 0.55, 'Scale: %s'%(round(self.spec.mdata.data('fitPar')[-2], 2)),
                                 transform = self.spec.view.ax.transAxes, fontsize=12)        
        
    def plotEbinFit(self, ax, fitPar='fitPar'):
        if fitPar in self.spec.mdata.data().keys():        
            self.ax.plot(self.spec.xdata['ebin'],
                         self.spec.mGauss(self.spec.xdata['ebin'],self.spec.mdata.data('fitPeakPos'),self.spec.mdata.data(fitPar)),
                         color='blue')    
            self.ax.relim()
            self.ax.autoscale(axis='y')  
        else:
            raise ValueError('Spectrum not gauged. Gauge first by running <Spec instance>.gauge(offset=0).')
    
    
    def showEbinFit(self, fitPar='fitPar'):
        self._singleFig()
        self.plotEbin(self.ax)
        self.plotEbinFit(self.ax, fitPar=fitPar)       
        self.addTextFileId(self.ax)
        self.addTextClusterId(self.ax)
        self.addTextGaugePar(self.ax)             
        self.fig.show()

        
        
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






        