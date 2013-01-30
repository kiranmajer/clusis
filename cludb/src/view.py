import matplotlib.pyplot as plt
import os.path
import load

class View(object):
    def __init__(self,spec):
        #print '__init__: Initializing View object.'
        'TODO: allow multiple specs'
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
                transform = ax.transAxes, fontsize=8, horizontalalignment='right')  


    def plotIdx(self, ax, subtractBg=False):
        ax.set_xlabel('Index')
        ax.set_ylabel('Intensity (a.u.)')
        ax.set_xlim(0,self.spec.xdata['idx'][-1])
        if subtractBg:
            intensityKey = 'intensitySub'
        else:
            intensityKey = 'intensity'
        ax.plot(self.spec.xdata['idx'], self.spec.ydata[intensityKey], color='black')
        ax.relim()
        ax.autoscale(axis='y')       
            
            
    def showIdx(self, subtractBg=False):
        self._singleFig()
        self.plotIdx(self.ax, subtractBg=subtractBg)
        self.addTextFileId(self.ax)
        self.fig.show()
        
        
    def plotTof(self, ax, showGauged=False, subtractBg=False, timeUnit=1e-6, xlim=['auto', 'auto']):
        'TODO: adapt for more time units'
        if xlim[0] == 'auto':
            xlim[0] = self.spec.xdata['tof'][0]/timeUnit
        if xlim[1] == 'auto':
            xlim[1] = self.spec.xdata['tof'][-1]/timeUnit
        ax.set_xlabel(r'Flight Time ($\mu s$)')
        ax.set_ylabel('Intensity (a.u.)')
        ax.set_xlim(xlim[0],xlim[1])
        if subtractBg:
            intensityKey = 'intensitySub'
        else:
            intensityKey = 'intensity'        
        ax.plot(self.spec.xdata['tof']/timeUnit, self.spec.ydata[intensityKey], color='black')
        ax.relim()
        ax.autoscale(axis='y')


    def showTof(self, subtractBg=False, timeUnit=1e-6, xlim=['auto', 'auto']):
        self._singleFig()
        self.plotTof(self.ax, subtractBg=subtractBg, timeUnit=timeUnit, xlim=xlim)        
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
        

    def showIdx(self, subtractBg=False):
        View.showIdx(self, subtractBg=subtractBg)
        self.addTextClusterId(self.ax)        
        self.fig.show()

        
    def showTof(self, subtractBg=False, timeUnit=1e-6, xlim=[0, 'auto']):
        View.showTof(self, subtractBg=subtractBg, timeUnit=timeUnit, xlim=xlim)
        self.addTextClusterId(self.ax, textPos='right')        
        self.fig.show()
        

    def plotEkin(self, ax, subtractBg=False):
        ax.set_xlabel(r'E$_{kin}$ (eV)')
        ax.set_ylabel('Intensity (a.u.)')
        ax.set_xlim(0,self.spec.photonEnergy(self.spec.mdata.data('waveLength')))
        if subtractBg:
            intensityKey = 'jacobyIntensitySub'
        else:
            intensityKey = 'jacobyIntensity'          
        ax.plot(self.spec.xdata['ekin'], self.spec.ydata[intensityKey], color='black')
        ax.relim()
        ax.autoscale(axis='y')


    def showEkin(self, subtractBg=False):  
        self._singleFig()
        self.plotEkin(self.ax, subtractBg=subtractBg)        
        self.addTextFileId(self.ax)
        self.addTextClusterId(self.ax, textPos='right')        
        self.fig.show()


    def plotEbin(self, ax, showGauged=False, subtractBg=False):
        ax.set_xlabel(r'E$_{bin}$ (eV)')
        ax.set_ylabel('Intensity (a.u.)')
        ax.set_xlim(0,self.spec.photonEnergy(self.spec.mdata.data('waveLength')))
        gauged = False
        if 'ebinGauged' in list(self.spec.xdata.keys()):
            if showGauged:
                ebinKey = 'ebinGauged'
                gauged = True
            else:
                ebinKey = 'ebin'
        elif showGauged and self.spec.mdata.data('clusterBaseUnit') not in ['Pt']:
            print('Spec is not gauged! Plotting normal spectrum instead.')
            ebinKey = 'ebin'
        else:
            ebinKey = 'ebin'
        if subtractBg:
            intensityKey = 'jacobyIntensitySub'
        else:
            intensityKey = 'jacobyIntensity'   
        ax.plot(self.spec.xdata[ebinKey], self.spec.ydata[intensityKey], color='black')
        ax.relim()
        ax.autoscale(axis='y')
        
        return gauged


    def showEbin(self, showGauged=True, subtractBg=False):
        self._singleFig()
        gauged = self.plotEbin(self.ax, showGauged=showGauged, subtractBg=subtractBg)
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
        
    
    def addTextGaugePar(self, ax, textPos='left', fitPar='fitParTof'):
        if textPos == 'left':
            pos_x, pos_y = 0.05, 0.6
        elif textPos == 'right':
            pos_x, pos_y = 0.95, 0.6
        else:
            raise ValueError('textPos must be one of: left, right. Got "%s" instead.'%(str(textPos)))        
        ax.text(pos_x, pos_y, 'E$_{offset}$: %.2f meV'%(self.spec.mdata.data(fitPar)[-3]*1e3),
                transform = self.spec.view.ax.transAxes, fontsize=12, horizontalalignment=textPos)
        ax.text(pos_x, pos_y-0.05, 't$_{offset}$: %.3f ns'%(self.spec.mdata.data(fitPar)[-2]*1e9),
                transform = self.spec.view.ax.transAxes, fontsize=12, horizontalalignment=textPos)
        ax.text(pos_x, pos_y-0.1, 't$_{scale}$: %.3f'%(self.spec.mdata.data(fitPar)[-1]),
                transform = self.spec.view.ax.transAxes, fontsize=12, horizontalalignment=textPos)
               
    def plotEbinFit(self, ax, fitPar):
        if fitPar in list(self.spec.mdata.data().keys()):
            if fitPar in ['fitPar', 'fitPar0']:        
                ax.plot(self.spec.xdata['ebin'],
                        self.spec.mGauss(self.spec.xdata['ebin'],
                                         self.spec.mdata.data('fitPeakPos'),
                                         self.spec.mdata.data(fitPar)),
                        color='blue')
            else:
                ax.plot(self.spec.xdata['ebin'],
                        self.spec.jTrans(self.spec.mGaussTrans(self.spec.xdata['tof'],
                                                               self.spec.mdata.data('fitPeakPosTof'),
                                                               self.spec.mdata.data(fitPar)),
                                         self.spec.xdata['tof']),
                        color='blue')    
            ax.relim()
            ax.autoscale(axis='y')  
        else:
            raise ValueError('Spectrum not gauged. Gauge first by running <Spec instance>.gauge(specType, offset=0).')
    
    
    def showEbinFit(self, fitPar='fitPar'):
        self._singleFig()
        self.plotEbin(self.ax)
        self.plotEbinFit(self.ax, fitPar)       
        self.addTextFileId(self.ax)
        self.addTextClusterId(self.ax)
        self.addTextGaugePar(self.ax, fitPar=fitPar)             
        self.fig.show()
        
        
    def plotTofFit(self, ax, fitPar, timeUnit):
        if fitPar in list(self.spec.mdata.data().keys()):        
            ax.plot(self.spec.xdata['tof']/timeUnit,
                    self.spec.mGaussTrans(self.spec.xdata['tof'],self.spec.mdata.data('fitPeakPosTof'),self.spec.mdata.data(fitPar)),
                    color='blue')    
            ax.relim()
            ax.autoscale(axis='y')  
        else:
            raise ValueError('Spectrum not gauged. Gauge first by running <Spec instance>.gauge(specType, offset=0).')
    
    
    def showTofFit(self, fitPar='fitParTof', timeUnit=1e-6):
        self._singleFig()
        self.plotTof(self.ax, timeUnit=timeUnit)
        self.plotTofFit(self.ax, fitPar, timeUnit)       
        self.addTextFileId(self.ax)
        self.addTextClusterId(self.ax, textPos='right')
        self.addTextGaugePar(self.ax, textPos='right', fitPar=fitPar)             
        self.fig.show()        

        
        
class ViewWater(ViewPes):
    def __init__(self,spec):
        ViewPes.__init__(self, spec)
        

    def addTextFitValues(self, ax, fitParKey, specType, timeUnit=1, textPos='left'):
        'TODO: adapt units to match timeUnit'
        if specType=='ebin' and fitParKey in ['fitParTof', 'fitPar0Tof']:
            peak_values = list(self.spec.ebin(self.spec.mdata.data(fitParKey)[:-2:2]))
            peakPos_unit = 'eV'
        else:
            peak_values = list(self.spec.mdata.data(fitParKey)[:-2:2])
            peakPos_unit = '$\mu s$'
        if specType == 'tof':
            peakPos_unit = '$\mu s$'
        else:
            peakPos_unit = 'eV'
        if textPos == 'left':
            pos_x, pos_y = 0.05, 0.6
        elif textPos == 'right':
            pos_x, pos_y = 0.95, 0.6
        else:
            raise ValueError('textPos must be one of: left, right. Got "%s" instead.'%(str(textPos)))
        peak_number = 1
        for peak in peak_values:
            ax.text(pos_x, pos_y, '%i. Peak: %.3f %s'%(peak_number, round(peak/timeUnit, 3), peakPos_unit),
                    transform = self.spec.view.ax.transAxes, fontsize=12, horizontalalignment=textPos)
            peak_number+=1
            pos_y-=0.05
        
        #textScale = ax.text(0.05, 0.55, 'Scale: %s'%(round(self.spec.mdata.data('fitPar')[-2], 2)),
        #                        transform = self.spec.view.ax.transAxes, fontsize=12) 
    'TODO: implement gauging!'
    def plotEbinFit(self, ax, fitPar):
        if fitPar in ['fitPar', 'fitPar0']:
            ax.plot(self.spec.xdata['ebin'],
                    self.spec.mGl(self.spec.xdata['ebin'], self.spec.mdata.data(fitPar)),
                    color='blue')
            ax.relim()
            # plot single peaks, if there are more than one
            if len(self.spec.mdata.data(fitPar)) > 4:
                plist = list(self.spec.mdata.data(fitPar))
                sl = plist.pop()
                sg = plist.pop()
                while len(plist) >= 2:
                    A = plist.pop()
                    xmax = plist.pop()
                    ax.plot(self.spec.xdata['ebin'],
                            self.spec.mGl(self.spec.xdata['ebin'], [xmax,A,sg,sl]),
                            color='DimGray')
        else:
            ax.plot(self.spec.xdata['ebin'],
                    self.spec.jTrans(self.spec.mGlTrans(self.spec.xdata['tof'],
                                                   self.spec.mdata.data(fitPar)),
                                     self.spec.xdata['tof']),
                    color='blue')
            ax.relim()
            # plot single peaks, if there are more than one
            if len(self.spec.mdata.data(fitPar)) > 4:
                plist = list(self.spec.mdata.data(fitPar))
                sl = plist.pop()
                sg = plist.pop()
                while len(plist) >= 2:
                    A = plist.pop()
                    xmax = plist.pop()
                    ax.plot(self.spec.xdata['ebin'],
                            self.spec.jTrans(self.spec.mGlTrans(self.spec.xdata['tof'],
                                                                [xmax,A,sg,sl]),
                                             self.spec.xdata['tof']),
                            color='DimGray')             

            
    
    def showEbinFit(self, fitPar='fitPar'):
        if fitPar in list(self.spec.mdata.data().keys()):
            self._singleFig()
            if fitPar in ['fitPar', 'fitPar0']:
                gauged = self.plotEbin(self.ax, showGauged=self.spec.mdata.data('fitGauged'),
                                       subtractBg=self.spec.mdata.data('fitSubtractBg'))
            else:
                gauged = self.plotEbin(self.ax, showGauged=self.spec.mdata.data('fitGaugedTof'),
                                       subtractBg=self.spec.mdata.data('fitSubtractBgTof'))
            self.plotEbinFit(self.ax, fitPar)
            self.addTextFileId(self.ax)
            self.addTextClusterId(self.ax)
            self.addTextFitValues(self.ax, fitParKey=fitPar, specType='ebin')
            if gauged:        
                self.addTextGaugeMarker(self.ax)
            self.fig.show()
        else:
            raise ValueError('Spectrum not yet fitted. Fit first.')            


    def plotTofFit(self, ax, fitPar, timeUnit):
        xdata = self.spec.xdata['tof']/timeUnit
        ax.plot(xdata,
                self.spec.mGlTrans(self.spec.xdata['tof'], self.spec.mdata.data(fitPar)),
                color='blue')
        ax.relim()
        # plot single peaks, if there are more than one
        if len(self.spec.mdata.data(fitPar)) > 4:        
            plist = list(self.spec.mdata.data(fitPar))
            sl = plist.pop()
            sg = plist.pop()
            while len(plist) >= 2:
                A = plist.pop()
                xmax = plist.pop()
                ax.plot(xdata,
                        self.spec.mGlTrans(self.spec.xdata['tof'], [xmax,A,sg,sl]),
                        color='DimGray') 



    def showTofFit(self, fitPar='fitParTof', timeUnit=1e-6):
        if fitPar in list(self.spec.mdata.data().keys()):
            self._singleFig()
            gauged = self.plotTof(self.ax, showGauged=self.spec.mdata.data('fitGaugedTof'),
                                   subtractBg=self.spec.mdata.data('fitSubtractBgTof'),
                                   timeUnit=timeUnit)
            self.plotTofFit(self.ax, fitPar, timeUnit=timeUnit)
            self.addTextFileId(self.ax)
            self.addTextClusterId(self.ax, textPos='right')
            self.addTextFitValues(self.ax, fitParKey=fitPar, specType='tof', timeUnit=timeUnit, textPos='right')
            if gauged:        
                self.addTextGaugeMarker(self.ax)
            self.fig.show()      
        else:
            raise ValueError('Spectrum not yet fitted. Fit first.')
        
        
        
class ViewMs(View):
    def __init__(self, spec):
        View.__init__(self, spec)   
        
        
    def plotMs(self, ax, massKey):
        if massKey == 'ms':
            ax.set_xlabel('Cluster Size (#%s)'%self.spec.mdata.data('clusterBaseUnit'))
        else:
            ax.set_xlabel('Cluster Mass (amu)')
        ax.set_ylabel('Intensity (a.u.)')
        ax.plot(self.spec.xdata[massKey], self.spec.ydata['intensity'], color='black')
        ax.relim()
        ax.autoscale()
        
        
    def showMs(self, massKey='ms'):
        self._singleFig()
        self.plotMs(ax=self.ax, massKey=massKey)
        self.addTextFileId(self.ax)
        self.fig.show()
        
        
        
