import matplotlib.pyplot as plt
import os.path
from numpy import log10

import load

class View(object):
    def __init__(self,spec):
        #print '__init__: Initializing View object.'
        'TODO: allow multiple specs'
        self.spec = spec
        

    def _single_fig_output(self):
        if hasattr(self, 'fig'):        
            self.ax.lines = []
            self.ax.texts = []
        else:
            self.fig = plt.figure()
            #print 'Figure created.'
            self.ax = self.fig.add_subplot(1,1,1)    


    def _addtext_file_id(self, ax):
        ax.text(1.0, 1.01, '%s'%(os.path.basename(self.spec.mdata.data('datFile'))),
                transform = ax.transAxes, fontsize=8, horizontalalignment='right')  

        
    def _addtext_statusmarker(self, ax, xdata_key, ydata_key):
        stats = []
        if 'Gauged' in xdata_key:
            stats.append('gauged')
        if 'Sub' in ydata_key:
            stats.append('subtracted')
        if len(stats) > 0:
            stat_text = ', '.join(stats)
            ax.text(0.5, 1.01, stat_text, transform = self.ax.transAxes, fontsize=8, horizontalalignment='center')
    
    
    def _pretty_format_clusterid(self, ms=False):
        formatStart = '$\mathrm{\mathsf{'
        formatEnd = '}}$'
        bu = self.spec.mdata.data('clusterBaseUnit')
        if sum([c.isupper() for c in bu]) > 1: # base unit is molecule
            'TODO: Better a general lookup table or a parser.'
            if bu in ['H2O', 'D2O']:
                mol_map = {'H2O': '(H_{2}O)',
                           'D2O': '(D_{2}O)'}
                partCluster = mol_map[bu]
            else:
                print('Warning: No map entry for this molecule.')
        else:
            partCluster = bu
        if not ms:
            partClusterNumber = '_{%s}'%(str(self.spec.mdata.data('clusterBaseUnitNumber')))
        partCharge = '}^{%s}'%self.spec.mdata.data('ionType')
        partDopant = '{%s}'%self.spec.mdata.data('clusterDopant')
        partDopantNumber = '_{%s}'%(str(self.spec.mdata.data('clusterDopantNumber')))
        
        cluster_id_str = formatStart + partCluster
        if not ms:
            if self.spec.mdata.data('clusterBaseUnitNumber') > 1:
                cluster_id_str += partClusterNumber
        if self.spec.mdata.data('clusterDopant'):
            cluster_id_str += partDopant
            if self.spec.mdata.data('clusterDopantNumber') > 1:
                cluster_id_str += partDopantNumber
        cluster_id_str += partCharge
        cluster_id_str += formatEnd
        return cluster_id_str
                
    
    def _addtext_cluster_id(self, ax, cluster_id, textPos='left', fontsize=28):
        if textPos == 'left':
            pos_x, pos_y = 0.05, 0.8
        elif textPos == 'right':
            pos_x, pos_y = 0.95, 0.8
        else:
            raise ValueError('textPos must be one of: left, right. Got "%s" instead.'%(str(textPos)))
        ax.text(pos_x, pos_y, cluster_id, transform = ax.transAxes, fontsize=fontsize, horizontalalignment=textPos)
        
    
    def _set_xlabel_time(self, ax, label, time_unit):
        if time_unit not in [1, 1e-3, 1e-6, 1e-9]:
            raise ValueError('time_unit must be one of: 1, 1e-3, 1e-6, 1e-9.')
        prefix_map = ['', 'm', '\mu ', 'n']
        prefix = prefix_map[int(abs(log10(time_unit)/3))]
        ax.set_xlabel(r'{0} (${1}s$)'.format(label, prefix))
        
        
    def _pref_xdata_key(self, x_repr):
        pref_map = {'idx': ['idx', 'idx'],
                    'tof': ['tof', 'tofGauged'],
                    'ekin': ['ekin', 'ekinGauged'],
                    'ebin': ['ebin', 'ebinGauged']}
        if 'gauged' in self.spec.mdata.data('systemTags'):
            pxk = pref_map[x_repr][1]
        else:
            pxk = pref_map[x_repr][0]
        return pxk
        
        
    def _pref_ydata_key(self, xdata_key):
        pref_map = {'idx': ['intensity', 'intensitySub'],
                    'tof': ['intensity', 'intensitySub'],
                    'tofGauged': ['intensity', 'intensitySub'],
                    'ekin': ['jIntensity', 'jIntensitySub'],
                    'ekinGauged': ['jIntensityGauged', 'jIntensityGaugedSub'],
                    'ebin': ['jIntensity', 'jIntensitySub'],
                    'ebinGauged': ['jIntensityGauged', 'jIntensityGaugedSub'],}
        if 'subtracted' in self.spec.mdata.data('systemTags'):
            pyk = pref_map[xdata_key][1]
        else:
            pyk = pref_map[xdata_key][0]
        return pyk
    
    
    def _set_xlimit(self, ax, xlim, xlim_auto):
        x_lim = [0,1]
        if xlim[0] == 'auto':
            x_lim[0] = xlim_auto[0]
        else:
            x_lim[0] = xlim[0]
        if xlim[1] == 'auto':
            x_lim[1] = xlim_auto[1]
        else:
            x_lim[1] = xlim[1]
        ax.set_xlim(x_lim[0], x_lim[1])
        
        
    def _set_ylimit(self, ax):
        ax.relim()  
        ax.autoscale(axis='y')        
        

    def plot_idx(self, ax, ydata_key, xlim, xlim_auto, color='black'):
        # set data keys
        xdata_key = 'idx'
        if ydata_key in ['auto']:
            ydata_key = self._pref_ydata_key(xdata_key)
        elif ydata_key not in ['instensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw']:
            raise ValueError("ydata_key must be one of: 'intensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw'")
        # plot 
        ax.plot(self.spec.xdata[xdata_key], self.spec.ydata[ydata_key], color=color)
        # set axes limits
        self._set_xlimit(ax, xlim, xlim_auto)
        self._set_ylimit(ax)

                
        
    def plot_tof(self, ax, xdata_key, ydata_key, time_unit, xlim, xlim_auto, color='black'):
        print('plot_tof called with xlim =', xlim)
        # set data keys
        if xdata_key in ['auto']:
            xdata_key = self._pref_xdata_key('tof')
        elif xdata_key not in ['tof', 'tofGauged']:
            raise ValueError("xdata_key must be one of: 'tof', 'tofGauged'.")
        if ydata_key in ['auto']:
            ydata_key = self._pref_ydata_key(xdata_key)
        elif ydata_key not in ['intensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw']:
            raise ValueError("ydata_key must be one of: 'intensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw'")  
        # plot      
        ax.plot(self.spec.xdata[xdata_key]/time_unit, self.spec.ydata[ydata_key], color=color)
        #set axes limits
        self._set_xlimit(ax, xlim, xlim_auto)
        self._set_ylimit(ax)
            
            
    def show_idx(self, xdata_key='idx', ydata_key='auto', xlim=['auto', 'auto']):
        xlim_auto = [self.spec.xdata[xdata_key][0], self.spec.xdata[xdata_key][-1]]
        self._single_fig_output()
        self.plot_idx(self.ax, ydata_key=ydata_key, xlim=xlim, xlim_auto=xlim_auto)
        self.ax.set_xlabel('Index')
        self.ax.set_ylabel('Intensity (a.u.)')        
        self._addtext_file_id(self.ax)
        self._addtext_statusmarker(self.ax, xdata_key=xdata_key, ydata_key=ydata_key)
        self.fig.show()


    def show_tof(self, xdata_key='auto', ydata_key='auto', time_label='Time',
                 time_unit=1e-6, xlim=['auto', 'auto']):
        xlim_auto = [self.spec.xdata[xdata_key][0]/time_unit, self.spec.xdata[xdata_key][-1]/time_unit]      
        self._single_fig_output()
        self.plot_tof(self.ax, xdata_key=xdata_key, ydata_key=ydata_key,
                      time_unit=time_unit, xlim=xlim, xlim_auto=xlim_auto)
        self._set_xlabel_time(self.ax, label=time_label, time_unit=time_unit)
        self.ax.set_ylabel('Intensity (a.u.)')
        self._addtext_file_id(self.ax)
        self._addtext_statusmarker(self.ax, xdata_key=xdata_key, ydata_key=ydata_key)
        self.fig.show()
        
        
        
class ViewPes(View):
    def __init__(self, spec):
        View.__init__(self, spec)
        

    def plot_ekin(self, ax, xdata_key, ydata_key, xlim, xlim_auto, color='black'):
        # set data keys
        #ax.set_xlim(0,self.spec._hv)
        if xdata_key in ['auto']:
            xdata_key = self._pref_xdata_key('ekin')
        elif xdata_key not in ['ekin', 'ekinGauged']:
            raise ValueError("xdata_key must be one of: 'ekin', 'ekinGauged'")
        if ydata_key in ['auto']:
            ydata_key = self._pref_ydata_key(xdata_key)
        elif xdata_key in ['ekin'] and ydata_key not in ['jIntensity', 'jIntensitySub']:
            raise ValueError("ydata_key must be one of: 'jIntensity', 'jIntensitySub'")
        elif ydata_key not in ['jIntensityGauged', 'jIntensityGaugedSub']:
            raise ValueError("ydata_key must be one of: 'jIntensityGauged', 'jIntensityGaugedSub'")
        # plot 
        ax.plot(self.spec.xdata[xdata_key], self.spec.ydata[ydata_key], color=color)
        #set axes limits
        self._set_xlimit(ax, xlim, xlim_auto)
        self._set_ylimit(ax)


    def plot_ebin(self, ax, xdata_key, ydata_key, xlim, xlim_auto, color='black'):
        if xdata_key in ['auto']:
            xdata_key = self._pref_xdata_key('ebin')
        elif xdata_key not in ['ebin', 'ekinGauged']:
            raise ValueError("xdata_key must be one of: 'ebin', 'ebinGauged'.")
        if ydata_key in ['auto']:
            ydata_key = self._pref_ydata_key(xdata_key)
        elif xdata_key in ['ebin'] and ydata_key not in ['jIntensity', 'jIntensitySub']:
            raise ValueError("ydata_key must be one of: 'jIntensity', 'jIntensitySub'")
        elif ydata_key not in ['jIntensityGauged', 'jIntensityGaugedSub']:
            raise ValueError("ydata_key must be one of: 'jIntensityGauged', 'jIntensityGaugedSub'")        
        # plot
        ax.plot(self.spec.xdata[xdata_key], self.spec.ydata[ydata_key], color=color)
        #set axes limits
        self._set_xlimit(ax, xlim, xlim_auto)
        self._set_ylimit(ax)


    def show_idx(self, ydata_key='auto', xlim=['auto', 'auto']):
        View.show_idx(self, ydata_key=ydata_key, xlim=xlim)
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid())
        self.fig.show()

        
    def show_tof(self, xdata_key='auto', ydata_key='auto', time_label='Flight Time',
                 timeUnit=1e-6, xlim=[0, 'auto']):
        View.show_tof(self, xdata_key=xdata_key, ydata_key=ydata_key, time_label=time_label, 
                      timeUnit=timeUnit, xlim=xlim)
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid(), textPos='right')        
        self.fig.show()
        

    def show_ekin(self, xdata_key='auto', ydata_key='auto', xlim=['auto', 'auto']):  
        xlim_auto = [0, self.spec._hv]
        self._single_fig_output()
        self.plot_ekin(self.ax, xdata_key=xdata_key, ydata_key=ydata_key, xlim=xlim, xlim_auto=xlim_auto)
        self.ax.set_xlabel(r'E$_{kin}$ (eV)')
        self.ax.set_ylabel('Intensity (a.u.)')     
        self._addtext_file_id(self.ax)
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid(), textPos='right')
        self._addtext_statusmarker(self.ax, xdata_key=xdata_key, ydata_key=ydata_key)        
        self.fig.show()


    def show_ebin(self, xdata_key='auto', ydata_key='auto', xlim=['auto', 'auto']):
        xlim_auto = [0, self.spec._hv]
        self._single_fig_output()
        self.plot_ebin(self.ax, xdata_key=xdata_key, ydata_key=ydata_key, xlim=xlim, xlim_auto=xlim_auto)
        self.ax.set_xlabel(r'E$_{bin}$ (eV)')
        self.ax.set_ylabel('Intensity (a.u.)')      
        self._addtext_file_id(self.ax)
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid())
        self._addtext_statusmarker(self.ax, xdata_key=xdata_key, ydata_key=ydata_key)             
        self.fig.show()
        
        
    def show_gaugeref(self):
        gaugeRef = self.spec.mdata.data('gaugeRef')
        gaugeSpec = load.load_pickle(self.spec.cfg, gaugeRef)
        gaugeSpec.view.show_ebin_fit()
        


class ViewPt(ViewPes):
    def __init__(self,spec):
        ViewPes.__init__(self, spec)
        
    
    def addtext_gauge_par(self, ax, textPos='left', fitPar='fitParTof'):
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
        ax.text(pos_x, pos_y-0.1, 'l$_{scale}$: %.3f'%(self.spec.mdata.data(fitPar)[-1]),
                transform = self.spec.view.ax.transAxes, fontsize=12, horizontalalignment=textPos)
               
    def plot_ebin_fit(self, ax, fitPar):
        if fitPar in list(self.spec.mdata.data().keys()):
#            if fitPar in ['fitPar', 'fitPar0']:        
#                ax.plot(self.spec.xdata['ebin'],
#                        self.spec.mGauss(self.spec.xdata['ebin'],
#                                         self.spec.mdata.data('fitPeakPos'),
#                                         self.spec.mdata.data(fitPar)),
#                        color='blue')
#            else:
            ax.plot(self.spec.xdata['ebin'],
                        self.spec.jtrans(self.spec._multi_gauss_trans(self.spec.xdata['tof'],
                                                                      self.spec.mdata.data('fitPeakPos'),
                                                                      self.spec.mdata.data(fitPar)),
                                         self.spec.xdata['tof']),
                        color='blue')    
            ax.relim()
            ax.autoscale(axis='y')  
        else:
            raise ValueError('Spectrum not gauged. Gauge first by running <Spec instance>.gauge(specType, offset=0).')
    
    
    def show_ebin_fit(self, fitPar='fitPar'):
        self._single_fig_output()
        self.plot_ebin(self.ax)
        self.plot_ebin_fit(self.ax, fitPar)       
        self._addtext_file_id(self.ax)
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid())
        self.addtext_gauge_par(self.ax, fitPar=fitPar)             
        self.fig.show()
        
        
    def plot_tof_fit(self, ax, fitPar, timeUnit):
        if fitPar in list(self.spec.mdata.data().keys()):        
            ax.plot(self.spec.xdata['tof']/timeUnit,
                    self.spec._multi_gauss_trans(self.spec.xdata['tof'],
                                                 self.spec.mdata.data('fitPeakPos'),
                                                 self.spec.mdata.data(fitPar)),
                    color='blue')    
            ax.relim()
            ax.autoscale(axis='y')  
        else:
            raise ValueError('Spectrum not gauged. Gauge first by running <Spec instance>.gauge().')
    
    
    def show_tof_fit(self, fitPar='fitPar', timeUnit=1e-6):
        self._single_fig_output()
        self.plot_tof(self.ax, timeUnit=timeUnit)
        self.plot_tof_fit(self.ax, fitPar, timeUnit)       
        self._addtext_file_id(self.ax)
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid(), textPos='right')
        self.addtext_gauge_par(self.ax, textPos='right', fitPar=fitPar)             
        self.fig.show()        

        
        
class ViewWater(ViewPes):
    def __init__(self,spec):
        ViewPes.__init__(self, spec)
        

    def addtext_fitvalues(self, ax, fitParKey, specType, timeUnit=1, textPos='left'):
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
    def plot_ebin_fit(self, ax, fitPar):
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
                    self.spec.jtrans(self.spec.mGlTrans(self.spec.xdata['tof'],
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
                            self.spec.jtrans(self.spec.mGlTrans(self.spec.xdata['tof'],
                                                                [xmax,A,sg,sl]),
                                             self.spec.xdata['tof']),
                            color='DimGray')             

            
    
    def show_ebin_fit(self, fitPar='fitPar'):
        if fitPar in list(self.spec.mdata.data().keys()):
            self._single_fig_output()
            if fitPar in ['fitPar', 'fitPar0']:
                gauged = self.plot_ebin(self.ax, show_gauged=self.spec.mdata.data('fitGauged'),
                                       subtractBg=self.spec.mdata.data('fitSubtractBg'))
            else:
                gauged = self.plot_ebin(self.ax, show_gauged=self.spec.mdata.data('fitGaugedTof'),
                                       subtractBg=self.spec.mdata.data('fitSubtractBgTof'))
            self.plot_ebin_fit(self.ax, fitPar)
            self._addtext_file_id(self.ax)
            self._addtext_cluster_id(self.ax, self._pretty_format_clusterid())
            self.addtext_fitvalues(self.ax, fitParKey=fitPar, specType='ebin')
            if gauged:        
                self._addtext_statusmarker(self.ax, xdata_key=xdata_key, ydata_key=ydata_key)
            self.fig.show()
        else:
            raise ValueError('Spectrum not yet fitted. Fit first.')            


    def plot_tof_fit(self, ax, fitPar, timeUnit):
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



    def show_tof_fit(self, fitPar='fitParTof', timeUnit=1e-6):
        if fitPar in list(self.spec.mdata.data().keys()):
            self._single_fig_output()
            gauged = self.plot_tof(self.ax, show_gauged=self.spec.mdata.data('fitGaugedTof'),
                                   subtractBg=self.spec.mdata.data('fitSubtractBgTof'),
                                   timeUnit=timeUnit)
            self.plot_tof_fit(self.ax, fitPar, timeUnit=timeUnit)
            self._addtext_file_id(self.ax)
            self._addtext_cluster_id(self.ax, self._pretty_format_clusterid(), textPos='right')
            self.addtext_fitvalues(self.ax, fitParKey=fitPar, specType='tof', timeUnit=timeUnit, textPos='right')
            if gauged:        
                self._addtext_statusmarker(self.ax, xdata_key=xdata_key, ydata_key=ydata_key)
            self.fig.show()      
        else:
            raise ValueError('Spectrum not yet fitted. Fit first.')
        
        
        
class ViewMs(View):
    def __init__(self, spec):
        View.__init__(self, spec)   
        
        
    def plot_ms(self, ax, massKey):
        if massKey == 'ms':
            ax.set_xlabel('Cluster Size (#%s)'%self.spec.mdata.data('clusterBaseUnit'))
        else:
            ax.set_xlabel('Cluster Mass (amu)')
        ax.set_ylabel('Intensity (a.u.)')
        ax.plot(self.spec.xdata[massKey], self.spec.ydata['intensity'], color='black')
        ax.relim()
        ax.autoscale()
        
        
    def show_ms(self, massKey='ms'):
        self._single_fig_output()
        self.plot_ms(ax=self.ax, massKey=massKey)
        self._addtext_file_id(self.ax)
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid(ms=True))
        self.fig.show()
        
        
        
