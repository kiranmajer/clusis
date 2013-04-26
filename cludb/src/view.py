import matplotlib.pyplot as plt
import os.path
from numpy import log10,sqrt

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
                
    
    def _addtext_cluster_id(self, ax, cluster_id, text_pos='left', fontsize=28):
        if text_pos == 'left':
            pos_x, pos_y = 0.05, 0.8
        elif text_pos == 'right':
            pos_x, pos_y = 0.95, 0.8
        else:
            raise ValueError('text_pos must be one of: left, right. Got "%s" instead.'%(str(text_pos)))
        ax.text(pos_x, pos_y, cluster_id, transform = ax.transAxes, fontsize=fontsize, horizontalalignment=text_pos)
        
    
    def _set_xlabel_time(self, ax, label, time_unit):
        if time_unit not in [1, 1e-3, 1e-6, 1e-9]:
            raise ValueError('time_unit must be one of: 1, 1e-3, 1e-6, 1e-9.')
        prefix_map = ['', 'm', '\mu ', 'n']
        prefix = prefix_map[int(abs(log10(time_unit)/3))]
        ax.set_xlabel(r'{0} (${1}s$)'.format(label, prefix))
        
        
#    def _pref_xdata_key(self, x_repr):
#        pref_map = {'idx': ['idx', 'idx'],
#                    'tof': ['tof', 'tofGauged'],
#                    'ekin': ['ekin', 'ekinGauged'],
#                    'ebin': ['ebin', 'ebinGauged']}
#        if 'gauged' in self.spec.mdata.data('systemTags'):
#            pxk = pref_map[x_repr][1]
#        else:
#            pxk = pref_map[x_repr][0]
#        return pxk
#        
#        
#    def _pref_ydata_key(self, xdata_key):
#        pref_map = {'idx': ['intensity', 'intensitySub'],
#                    'tof': ['intensity', 'intensitySub'],
#                    'tofGauged': ['intensity', 'intensitySub'],
#                    'ekin': ['jIntensity', 'jIntensitySub'],
#                    'ekinGauged': ['jIntensityGauged', 'jIntensityGaugedSub'],
#                    'ebin': ['jIntensity', 'jIntensitySub'],
#                    'ebinGauged': ['jIntensityGauged', 'jIntensityGaugedSub'],}
#        if 'subtracted' in self.spec.mdata.data('systemTags'):
#            pyk = pref_map[xdata_key][1]
#        else:
#            pyk = pref_map[xdata_key][0]
#        return pyk


    def _auto_key_selection(self, xdata_key, ydata_key, key_deps):
        def auto_xkey(key_deps):
            k_gauged = [i for i in key_deps.keys() if 'Gauged' in i]
            if 'gauged' in self.spec.mdata.data('systemTags') and len(k_gauged) > 0:
                auto_x = k_gauged[0]
            else:
                auto_x = [i for i in key_deps.keys() if 'Gauged' not in i][0]
            return auto_x
        
        def auto_ykey(key_deps, xdata_key):
            k_sub = [i for i in key_deps[xdata_key] if 'Sub' in i]
            if 'subtracted' in self.spec.mdata.data('systemTags') and len(k_sub) > 0:
                auto_y = k_sub[0]
            else:
                auto_y =  [i for i in key_deps[xdata_key] if 'Sub' not in i][0]
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
        

    def plot_idx(self, ax, xdata_key, ydata_key, xlim, color='black'):

#        xdata_key = 'idx'
#        if ydata_key in ['auto']:
#            ydata_key = self._pref_ydata_key(xdata_key)
#        elif ydata_key not in ['intensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw']:
#            raise ValueError("ydata_key must be one of: 'intensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw'")
        # plot 
        ax.plot(self.spec.xdata[xdata_key], self.spec.ydata[ydata_key], color=color)
        # set axes limits
        xlim_auto = [self.spec.xdata[xdata_key][0], self.spec.xdata[xdata_key][-1]]
        self._set_xlimit(ax, xlim, xlim_auto)
        self._set_ylimit(ax)
              
        
    def plot_tof(self, ax, xdata_key, ydata_key, time_unit, xlim, color='black'):
        print('plot_tof called with xlim =', xlim)
        
#        self._auto_key_selection(xdata_key=xdata_key, ydata_key=ydata_key,
#                                 xkeys=['tof', 'tofGauged'],
#                                 ykeys=['intensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw'])
#        # set data keys
#        if xdata_key in ['auto']:
#            xdata_key = self._pref_xdata_key('tof')
#        elif xdata_key not in ['tof', 'tofGauged']:
#            raise ValueError("xdata_key must be one of: 'tof', 'tofGauged'.")
#        if ydata_key in ['auto']:
#            ydata_key = self._pref_ydata_key(xdata_key)
#        elif ydata_key not in ['intensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw']:
#            raise ValueError("""ydata_key must be one of: 'intensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw'
#            Got'{}' instead.""".format(ydata_key))  
        # plot      
        ax.plot(self.spec.xdata[xdata_key]/time_unit, self.spec.ydata[ydata_key], color=color)
        #set axes limits
        xlim_auto = [self.spec.xdata[xdata_key][0]/time_unit, self.spec.xdata[xdata_key][-1]/time_unit] 
        self._set_xlimit(ax, xlim, xlim_auto)
        self._set_ylimit(ax)
            
            
    def show_idx(self, ydata_key='auto', xlim=['auto', 'auto']):
        self._single_fig_output()
        # set data keys
        key_deps = {'idx': ['intensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw']}
        xdata_key, ydata_key = self._auto_key_selection(xdata_key='idx', ydata_key=ydata_key, key_deps=key_deps)        
        self.plot_idx(self.ax, xdata_key=xdata_key, ydata_key=ydata_key, xlim=xlim)
        self.ax.set_xlabel('Index')
        self.ax.set_ylabel('Intensity (a.u.)')        
        self._addtext_file_id(self.ax)
        self._addtext_statusmarker(self.ax, xdata_key=xdata_key, ydata_key=ydata_key)
        self.fig.show()


    def show_tof(self, xdata_key='auto', ydata_key='auto', time_label='Time',
                 time_unit=1e-6, xlim=['auto', 'auto']):     
        self._single_fig_output()
        # set data keys
        key_deps = {'tof': ['intensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw'],
                    'tofGauged': ['intensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw']} 
        xdata_key, ydata_key = self._auto_key_selection(xdata_key=xdata_key, ydata_key=ydata_key, key_deps=key_deps)      
        self.plot_tof(self.ax, xdata_key=xdata_key, ydata_key=ydata_key,
                      time_unit=time_unit, xlim=xlim)
        self._set_xlabel_time(self.ax, label=time_label, time_unit=time_unit)
        self.ax.set_ylabel('Intensity (a.u.)')
        self._addtext_file_id(self.ax)
        self._addtext_statusmarker(self.ax, xdata_key=xdata_key, ydata_key=ydata_key)
        self.fig.show()
        
        
        
class ViewPes(View):
    def __init__(self, spec):
        View.__init__(self, spec)
        

    def plot_ekin(self, ax, xdata_key, ydata_key, xlim, color='black'):
#        # set data keys
#        if xdata_key in ['auto']:
#            xdata_key = self._pref_xdata_key('ekin')
#        elif xdata_key not in ['ekin', 'ekinGauged']:
#            raise ValueError("xdata_key must be one of: 'ekin', 'ekinGauged'")
#        if ydata_key in ['auto']:
#            ydata_key = self._pref_ydata_key(xdata_key)
#        elif xdata_key in ['ekin'] and ydata_key not in ['jIntensity', 'jIntensitySub']:
#            raise ValueError("ydata_key must be one of: 'jIntensity', 'jIntensitySub'")
#        elif xdata_key in ['ekinGauged'] and ydata_key not in ['jIntensityGauged', 'jIntensityGaugedSub']:
#            raise ValueError("ydata_key must be one of: 'jIntensityGauged', 'jIntensityGaugedSub'")
        # plot 
        ax.plot(self.spec.xdata[xdata_key], self.spec.ydata[ydata_key], color=color)
        #set axes limits  
        xlim_auto = [0, self.spec._hv]
        self._set_xlimit(ax, xlim, xlim_auto)
        self._set_ylimit(ax)


    def plot_ebin(self, ax, xdata_key, ydata_key, xlim, color='black'):
#        if xdata_key in ['auto']:
#            xdata_key = self._pref_xdata_key('ebin')
#        elif xdata_key not in ['ebin', 'ebinGauged']:
#            raise ValueError("xdata_key must be one of: 'ebin', 'ebinGauged'.")
#        if ydata_key in ['auto']:
#            ydata_key = self._pref_ydata_key(xdata_key)
#        elif xdata_key in ['ebin'] and ydata_key not in ['jIntensity', 'jIntensitySub']:
#            raise ValueError("ydata_key must be one of: 'jIntensity', 'jIntensitySub'")
#        elif xdata_key in ['ebinGauged'] and ydata_key not in ['jIntensityGauged', 'jIntensityGaugedSub']:
#            raise ValueError("{} invalid key. ydata_key must be one of: 'jIntensityGauged', 'jIntensityGaugedSub'".format(ydata_key))        
        # plot
        ax.plot(self.spec.xdata[xdata_key], self.spec.ydata[ydata_key], color=color)
        #set axes limits  
        xlim_auto = [0, self.spec._hv]
        self._set_xlimit(ax, xlim, xlim_auto)
        self._set_ylimit(ax)


    def show_idx(self, ydata_key='auto', xlim=['auto', 'auto']):
        View.show_idx(self, ydata_key=ydata_key, xlim=xlim)
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid(), text_pos='right')
        self.fig.show()

        
    def show_tof(self, xdata_key='auto', ydata_key='auto', time_label='Flight Time',
                 time_unit=1e-6, xlim=[0, 'auto']):
        View.show_tof(self, xdata_key=xdata_key, ydata_key=ydata_key, time_label=time_label, 
                      time_unit=time_unit, xlim=xlim)
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid(), text_pos='right')        
        self.fig.show()
        

    def show_ekin(self, xdata_key='auto', ydata_key='auto', xlim=['auto', 'auto']):
        self._single_fig_output()
        # set data keys
        key_deps = {'ekin': ['jIntensity', 'jIntensitySub'],
                    'ekinGauged': ['jIntensityGauged', 'jIntensityGaugedSub']} 
        xdata_key, ydata_key = self._auto_key_selection(xdata_key=xdata_key, ydata_key=ydata_key, key_deps=key_deps)        
        self.plot_ekin(self.ax, xdata_key=xdata_key, ydata_key=ydata_key, xlim=xlim)
        self.ax.set_xlabel(r'E$_{kin}$ (eV)')
        self.ax.set_ylabel('Intensity (a.u.)')     
        self._addtext_file_id(self.ax)
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid(), text_pos='right')
        self._addtext_statusmarker(self.ax, xdata_key=xdata_key, ydata_key=ydata_key)        
        self.fig.show()


    def show_ebin(self, xdata_key='auto', ydata_key='auto', xlim=['auto', 'auto']):
        self._single_fig_output()
        # set data keys
        key_deps = {'ebin': ['jIntensity', 'jIntensitySub'],
                    'ebinGauged': ['jIntensityGauged', 'jIntensityGaugedSub']} 
        xdata_key, ydata_key = self._auto_key_selection(xdata_key=xdata_key, ydata_key=ydata_key, key_deps=key_deps)         
        self.plot_ebin(self.ax, xdata_key=xdata_key, ydata_key=ydata_key, xlim=xlim)
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
        
    
    def _addtext_gauge_par(self, ax, text_pos='left', fit_par='fitParTof'):
        if text_pos == 'left':
            pos_x, pos_y = 0.05, 0.6
        elif text_pos == 'right':
            pos_x, pos_y = 0.95, 0.6
        else:
            raise ValueError('text_pos must be one of: left, right. Got "%s" instead.'%(str(text_pos)))        
        ax.text(pos_x, pos_y, 'E$_{offset}$: %.2f meV'%(self.spec.mdata.data(fit_par)[-3]*1e3),
                transform = self.spec.view.ax.transAxes, fontsize=12, horizontalalignment=text_pos)
        ax.text(pos_x, pos_y-0.05, 't$_{offset}$: %.3f ns'%(self.spec.mdata.data(fit_par)[-2]*1e9),
                transform = self.spec.view.ax.transAxes, fontsize=12, horizontalalignment=text_pos)
        ax.text(pos_x, pos_y-0.1, 'l$_{scale}$: %.3f'%(self.spec.mdata.data(fit_par)[-1]),
                transform = self.spec.view.ax.transAxes, fontsize=12, horizontalalignment=text_pos)
        ax.text(pos_x, pos_y-0.15, '$\Delta$l: %.1f mm'%(self.spec.mdata.data('flightLength')*1000*
                                                      (1/sqrt(self.spec.mdata.data(fit_par)[-1]) -1)),
                transform = self.spec.view.ax.transAxes, fontsize=12, horizontalalignment=text_pos)
               
    
    def plot_tof_fit(self, ax, fit_par, time_unit, color='blue'):        
        ax.plot(self.spec.xdata['tof']/time_unit,
                self.spec._multi_gauss_trans(self.spec.xdata['tof'],
                                             self.spec.mdata.data('fitPeakPos'),
                                             self.spec.mdata.data(fit_par)),
                color=color) 
    
               
    def plot_energy_fit(self, ax, fit_par, xdata_key, color='blue'):
        ax.plot(self.spec.xdata[xdata_key],
                self.spec.jtrans(self.spec._multi_gauss_trans(self.spec.xdata['tof'],
                                                              self.spec.mdata.data('fitPeakPos'),
                                                              self.spec.mdata.data(fit_par)),
                                 self.spec.xdata['tof']),
                color=color) 

    
    def show_tof_fit(self, fit_par='fitPar', time_unit=1e-6, time_label='Flight Time', xlim=[0, 'auto']):
        xdata_key = 'tof'
        ydata_key = self.spec.mdata.data('fitYdataKey')
        self._single_fig_output()
        self.plot_tof(self.ax, xdata_key=xdata_key, ydata_key=ydata_key,
                      time_unit=time_unit, xlim=xlim)
        self.plot_tof_fit(self.ax, fit_par=fit_par, time_unit=time_unit)   
        self._set_xlabel_time(self.ax, label=time_label, time_unit=time_unit)
        self.ax.set_ylabel('Intensity (a.u.)')
        self._addtext_file_id(self.ax)
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid(), text_pos='right') 
        self._addtext_gauge_par(self.ax, fit_par=fit_par, text_pos='right')
        self._addtext_statusmarker(self.ax, xdata_key=xdata_key, ydata_key=ydata_key)        
        self.fig.show()
        
        
    def _show_energy_fit(self, xdata_key, fit_par, xlim):
        plot_method = {'ekin': self.plot_ekin, 'ebin': self.plot_ebin}
        if xdata_key not in ['ekin', 'ebin']:
            raise ValueError("xdata_key must be one of: 'ekin', 'ebin'")
        if 'Sub' in self.spec.mdata.data('fitYdataKey'):
            ydata_key = 'jIntensitySub'
        else:
            ydata_key = 'jIntensity'
        self._single_fig_output()
        plot_method[xdata_key](self.ax, xdata_key=xdata_key, ydata_key=ydata_key, xlim=xlim)
        self.plot_energy_fit(self.ax, fit_par=fit_par, xdata_key=xdata_key)
        self.ax.set_ylabel('Intensity (a.u.)')        
        self._addtext_file_id(self.ax)
        self._addtext_statusmarker(self.ax, xdata_key=xdata_key, ydata_key=ydata_key)
        
        
    def show_ekin_fit(self, fit_par='fitPar', xlim=['auto', 'auto']):
        self._show_energy_fit(xdata_key='ekin', fit_par=fit_par, xlim=xlim)
        self.ax.set_xlabel(r'E$_{kin}$ (eV)')
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid(), text_pos='right') 
        self._addtext_gauge_par(self.ax, fit_par=fit_par, text_pos='right')            
        self.fig.show()    
        
        
    def show_ebin_fit(self, fit_par='fitPar', xlim=['auto', 'auto']):
        self._show_energy_fit(xdata_key='ebin', fit_par=fit_par, xlim=xlim)
        self.ax.set_xlabel(r'E$_{bin}$ (eV)')
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid()) 
        self._addtext_gauge_par(self.ax, fit_par=fit_par)            
        self.fig.show()    

        
        
class ViewWater(ViewPes):
    def __init__(self,spec):
        ViewPes.__init__(self, spec)
        

    def _addtext_fitvalues(self, ax, peakpos_unit, time_unit=1, text_pos='left'):
        def time_prefix(time_unit):
            if time_unit not in [1, 1e-3, 1e-6, 1e-9]:
                raise ValueError('time_unit must be one of: 1, 1e-3, 1e-6, 1e-9.')
            prefix_map = ['', 'm', '$\mu $', 'n']
            prefix = prefix_map[int(abs(log10(time_unit)/3))]
            return prefix
        
        if 'eV' == peakpos_unit and 'tof' in self.spec.mdata.data('fitXdataKey'):
            peak_values = list(self.spec.ebin(self.spec.mdata.data('fitPar')[:-2:2]))
        elif 's' == peakpos_unit and 'tof' in self.spec.mdata.data('fitXdataKey'):
            peak_values = list(self.spec.mdata.data('fitPar')[:-2:2])
            peakPos_unit = '{}s'.format(time_prefix(time_unit))
        else:
            peak_values = list(self.spec.mdata.data('fitPar')[:-2:2])
            
        if text_pos == 'left':
            pos_x, pos_y = 0.05, 0.6
        elif text_pos == 'right':
            pos_x, pos_y = 0.95, 0.6
        else:
            raise ValueError('text_pos must be one of: left, right. Got "%s" instead.'%(str(text_pos)))
        peak_number = 1
        for peak in peak_values:
            ax.text(pos_x, pos_y, '%i. Peak: %.3f %s'%(peak_number, round(peak/time_unit, 3), peakPos_unit),
                    transform = self.spec.view.ax.transAxes, fontsize=12, horizontalalignment=text_pos)
            peak_number+=1
            pos_y-=0.05
        
        #textScale = ax.text(0.05, 0.55, 'Scale: %s'%(round(self.spec.mdata.data('fitPar')[-2], 2)),
        #                        transform = self.spec.view.ax.transAxes, fontsize=12) 

   
   
    
    def plot_tof_fit(self, ax, xdata_key, ydata_key, fit_par, time_unit, color='blue', color_peaks='DimGray'):
        xdata = self.spec.xdata[xdata_key]/time_unit
        ax.plot(xdata,
                self.spec.multi_gl_trans(self.spec.xdata[xdata_key], self.spec.mdata.data(fit_par)),
                color='blue')
        ax.relim()
        # plot single peaks, if there are more than one
        if len(self.spec.mdata.data(fit_par)) > 4:        
            plist = list(self.spec.mdata.data(fit_par))
            sl = plist.pop()
            sg = plist.pop()
            while len(plist) >= 2:
                A = plist.pop()
                xmax = plist.pop()
                ax.plot(xdata,
                        self.spec.mGlTrans(self.spec.xdata[xdata_key], [xmax,A,sg,sl]),
                        color='DimGray')     
    
    
    'TODO: implement gauging!'
    def plot_ebin_fit(self, ax, xdata_key, ydata_key, fitPar, color='blue', color_peaks='DimGray'):
        if fitPar in ['fitPar', 'fitPar0']:
            ax.plot(self.spec.xdata['ebin'],
                    self.spec.mGl(self.spec.xdata['ebin'], self.spec.mdata.data(fitPar)),
                    color=color)
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
                            color=color_peaks)
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



    def show_tof_fit(self, fit_par='fitPar', time_unit=1e-6, time_label='Flight Time', xlim=[0, 'auto']):
        if 'fitted' not in self.spec.mdata.data('systemTags'):
            raise ValueError('Spectrum not yet fitted. Fit first.')            
        self._single_fig_output()
        # set data keys
        xdata_key = self.spec.mdata.data('fitXdataKey')
        ydata_key = self.spec.mdata.data('fitYdataKey')
        # plot
        self.plot_tof(self.ax, xdata_key=xdata_key, ydata_key=ydata_key, time_unit=time_unit, xlim=xlim, color='black')
        self.plot_tof_fit(self.ax, xdata_key=xdata_key, ydata_key=ydata_key, fit_par=fit_par, time_unit=time_unit)
        # setup axes
        self._set_xlabel_time(self.ax, label=time_label, time_unit=time_unit)
        self.ax.set_ylabel('Intensity (a.u.)')
        self._addtext_file_id(self.ax)
        self._addtext_statusmarker(self.ax, xdata_key=xdata_key, ydata_key=ydata_key)
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid(), text_pos='right')
        self._addtext_fitvalues(self.ax, peakpos_unit='s', time_unit=time_unit, text_pos='right')
        self.fig.show()      





            
    
    def show_ebin_fit(self, fitPar='fitPar'):
        if 'fitted' not in self.spec.mdata.data('systemTags'):
            raise ValueError('Spectrum not yet fitted. Fit first.') 
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
        self._addtext_fitvalues(self.ax, peakpos_unit='eV')
        if gauged:        
            self._addtext_statusmarker(self.ax, xdata_key=xdata_key, ydata_key=ydata_key)
        self.fig.show()
           





        
        
        
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
        
        
        
