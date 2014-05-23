import matplotlib.pyplot as plt
import os.path
from numpy import log10,sqrt, abs, argmin

import load

class View(object):
    def __init__(self, spec):
        #print '__init__: Initializing View object.'
        'TODO: allow multiple specs'
        self.spec = spec
        self.xdata_key = None
        self.ydata_key = None
        self.timeunit = None
        self.xlim_scale = None
        self.ymax = None
        self.comp_spec_data = {}
        

    def _single_fig_output(self):
# this does not work (?)
#         if hasattr(self, 'fig'):
#             try:
#                 print('Testing if plot window still exists ...')
#                 self.fig.show()
#             except Exception:
#                 del self.fig
                
        if hasattr(self, 'fig'):      
            self.ax.lines = []
            self.ax.texts = []
        else:
            self.fig = plt.figure()
            #print 'Figure created.'
            self.ax = self.fig.add_subplot(1,1,1)
        self.comp_spec_data = {}


    def _addtext_file_id(self, ax, fontsize=6, layout_y=3):
        ypos = 1 + layout_y*0.01/3
        self.txt_fileid = ax.text(1.0, ypos, '%s'%(os.path.basename(self.spec.mdata.data('datFile'))),
                                  transform = ax.transAxes, fontsize=fontsize, horizontalalignment='right')  

        
    def _addtext_statusmarker(self, ax, xdata_key, ydata_key, text_pos='center', fontsize=6, layout_y=3):
        xpos = {'left': 0.0,
                'center': 0.5,
                'right': 1.0}
        ypos = 1 + layout_y*0.01/3
        stats = []
        if 'waveLength' in self.spec.mdata.data().keys():
            human_wl = '{} nm'.format(round(self.spec.mdata.data('waveLength')*1e9))
            stats.append(human_wl)
        if 'Gauged' in xdata_key:
            stats.append('gauged')
        if 'Sub' in ydata_key:
            stats.append('subtracted')
        if 'background' in self.spec.mdata.data('systemTags'):
            stats.append('background')
        if len(stats) > 0:
            stat_text = ', '.join(stats)
            #print(self.spec.mdata.data('datFile'), 'Adding status marker(s): ', stat_text)
            ax.text(xpos[text_pos], ypos, stat_text, transform = ax.transAxes,
                    fontsize=fontsize, horizontalalignment=text_pos)
    
    
    def _pretty_format_clusterid(self, ms=False):
        formatStart = '$\mathrm{\mathsf{'
        formatEnd = '}}$'
        bu = self.spec.mdata.data('clusterBaseUnit')
        if sum([c.isupper() for c in bu]) > 1: # base unit is molecule
            'TODO: Better a general lookup table or a parser.'
            if bu in ['H2O', 'D2O', 'CH4O']:
                mol_map = {'H2O': '(H_{2}O)',
                           'D2O': '(D_{2}O)',
                           'CH4O': '(CH_{4}O)'}
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
                
    
    def _addtext_cluster_id(self, ax, cluster_id, text_pos='left', fontsize=28, color='black', valign='bottom',
                            voffset=0):
        if text_pos == 'left':
            pos_x, pos_y = 0.05, 0.8 + voffset
        elif text_pos == 'right':
            pos_x, pos_y = 0.95, 0.8 + voffset
        else:
            raise ValueError('text_pos must be one of: left, right. Got "%s" instead.'%(str(text_pos)))
        self.txt_clusterid = ax.text(pos_x, pos_y, cluster_id, transform = ax.transAxes, fontsize=fontsize,
                horizontalalignment=text_pos, verticalalignment=valign, color=color)
        
        
    def _addtext_info(self, ax, info_text, text_pos='left', text_vpos='center', fontsize=12):
#         if text_pos == 'left':
#             pos_x = 0.05
#         elif text_pos == 'right':
#             pos_x= 0.95
#         else:
#             raise ValueError('text_pos must be one of: left, right. Got "%s" instead.'%(str(text_pos)))
        txt_pos = {'left': 0.05, 'right': 0.95,
                   'top': 0.9, 'center': 0.5, 'bottom': 0.1}
             
        ax.text(txt_pos[text_pos], txt_pos[text_vpos], info_text, transform = ax.transAxes, fontsize=fontsize,
                horizontalalignment=text_pos, verticalalignment=text_vpos)        

    def _pretty_print_info(self, mdata_key):
        if mdata_key in self.spec.mdata.data().keys():
            if mdata_key == 'trapTemp':
                if self.spec.mdata.data(mdata_key) is not None:
                    info_str = 'T$_{trap}$: ' + '{:.0f} K'.format(self.spec.mdata.data(mdata_key))
                else:
                    info_str = 'T$_{trap}$: not set' 
            else:
                info_str = str(self.spec.mdata.data(mdata_key))
        else:
            info_str = ''
        
        
        return info_str
    
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
        'TODO: Use self.spec._auto_key_selection instead.'
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
        return x_lim
        
        
    def _set_ylimit(self, ax):
        ax.relim()  
        ax.autoscale(axis='y')
        
    def _yminmax_in_xrange(self, xdata, ydata, xlim_scale):
        xlb = argmin(abs(xdata-xlim_scale[0]))
        xub = argmin(abs(xdata-xlim_scale[1]))
        return ydata[xlb:xub].min(), ydata[xlb:xub].max()
               
    
    def _auto_ylim(self, ax, xdata, ydata, xlim_scale, lower_padding=0.04, upper_padding=0.2):
        'TODO: Is scaling of ymin always wanted?'
        self.xlim_scale = xlim_scale
        ymin, self.ymax = self._yminmax_in_xrange(xdata, ydata, xlim_scale)
        dy = abs(self.ymax - ymin)
        ax.set_ylim([ymin - lower_padding*dy, self.ymax + upper_padding*dy])

     
        

    def plot_idx(self, ax, xdata_key, ydata_key, xlim, xlim_scale=None, color='black'):

#        xdata_key = 'idx'
#        if ydata_key in ['auto']:
#            ydata_key = self._pref_ydata_key(xdata_key)
#        elif ydata_key not in ['intensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw']:
#            raise ValueError("ydata_key must be one of: 'intensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw'")
        self.xdata_key = xdata_key
        self.ydata_key = ydata_key
        #self.xlim_scale = xlim_scale
        # plot 
        ax.plot(self.spec.xdata[xdata_key], self.spec.ydata[ydata_key], color=color)
        # set axes limits
        xlim_auto = [self.spec.xdata[xdata_key][0], self.spec.xdata[xdata_key][-1]]
        xlim_plot = self._set_xlimit(ax, xlim, xlim_auto)
        if xlim_scale is None:
            self._auto_ylim(ax, self.spec.xdata[xdata_key], self.spec.ydata[ydata_key],
                            xlim_plot)
        else:
            self._auto_ylim(ax, self.spec.xdata[xdata_key], self.spec.ydata[ydata_key],
                            xlim_scale)
              
        
    def plot_tof(self, ax, xdata_key, ydata_key, time_unit, xlim, xlim_scale=None, color='black'):
        #print('plot_tof called with xlim =', xlim)
        
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
        self.xdata_key = xdata_key
        self.ydata_key = ydata_key
        self.timeunit = time_unit
        #self.xlim_scale = xlim_scale
        # plot      
        ax.plot(self.spec.xdata[xdata_key]/time_unit, self.spec.ydata[ydata_key], color=color)
        #set axes limits
        xlim_auto = [self.spec.xdata[xdata_key][0]/time_unit, self.spec.xdata[xdata_key][-1]/time_unit] 
        xlim_plot = self._set_xlimit(ax, xlim, xlim_auto)
        if xlim_scale is None:
            self._auto_ylim(ax, self.spec.xdata[xdata_key]/time_unit, self.spec.ydata[ydata_key],
                            xlim_plot)
        else:
            self._auto_ylim(ax, self.spec.xdata[xdata_key]/time_unit, self.spec.ydata[ydata_key],
                            xlim_scale)
            
            
    def show_idx(self, ydata_key='auto', xlim=['auto', 'auto'], xlim_scale=None, show_info=False):
        self._single_fig_output()
        # set data keys
        key_deps = {'idx': ['intensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw']}
        xdata_key, ydata_key = self._auto_key_selection(xdata_key='idx', ydata_key=ydata_key, key_deps=key_deps)        
        self.plot_idx(self.ax, xdata_key=xdata_key, ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale)
        self.ax.set_xlabel('Index')
        self.ax.set_ylabel('Intensity (a.u.)')        
        self._addtext_file_id(self.ax)
        self._addtext_statusmarker(self.ax, xdata_key=xdata_key, ydata_key=ydata_key)
        if show_info:
            self._addtext_info(self.ax, self.spec.mdata.data('info'), text_pos='right')
        self.fig.show()


    def show_tof(self, xdata_key='auto', ydata_key='auto', time_label='Time',
                 time_unit=1e-6, xlim=['auto', 'auto'], xlim_scale=None, show_info=False):     
        self._single_fig_output()
        # set data keys
        key_deps = {'tof': ['intensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw'],
                    'tofGauged': ['intensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw']} 
        xdata_key, ydata_key = self._auto_key_selection(xdata_key=xdata_key, ydata_key=ydata_key, key_deps=key_deps)      
        self.plot_tof(self.ax, xdata_key=xdata_key, ydata_key=ydata_key,
                      time_unit=time_unit, xlim=xlim, xlim_scale=xlim_scale)
        self._set_xlabel_time(self.ax, label=time_label, time_unit=time_unit)
        self.ax.set_ylabel('Intensity (a.u.)')
        self._addtext_file_id(self.ax)
        self._addtext_statusmarker(self.ax, xdata_key=xdata_key, ydata_key=ydata_key)
        if show_info:
            self._addtext_info(self.ax, self.spec.mdata.data('info'), text_pos='right')
        self.fig.show()
        
        
    def add_plot(self, ax, xdata, ydata, color='blue', file_id=None):
#         if not hasattr(self, 'fig'):
#             raise ValueError('No active plot. Create one first via show_XXX.')
        if file_id is not None:
            self.txt_fileid.set_text('{}, {}'.format(os.path.basename(self.spec.mdata.data('datFile')), file_id))
#         if self.xlim_scale is None:
#             xlim_scale = self.ax.get_xlim()
#         else:
#             xlim_scale = self.xlim_scale
        if self._yminmax_in_xrange(xdata, ydata, self.xlim_scale)[1] > self.ymax:
            self._auto_ylim(ax, xdata, ydata, self.xlim_scale)
        ax.plot(xdata, ydata, color=color)[0]
        #self.fig.canvas.draw()
        
        
    def _scalefactor_equal_area(self, xdata_ref, ydata_ref, xdata, ydata, yoffset):
        A_ref, i = 0, 0
        for y in ydata_ref[:-1]:
            if y - yoffset > 0:
                A_ref += (y - yoffset)*(xdata_ref[i+1] - xdata_ref[i])
            else:
                A_ref += 0
            i+=1
        A_comp, i = 0, 0
        for y in ydata[:-1]:
            A_comp += y*(xdata[i+1] - xdata[i])
            i+=1
        return A_ref/A_comp
    
    def _scalefactor_equal_max(self, ydata_ref, ydata):
        max_ref = ydata_ref.max()
        max_comp = ydata.max()
        return  max_ref/max_comp
        
        
        
class ViewPes(View):
    def __init__(self, spec):
        View.__init__(self, spec)
        

    def plot_ekin(self, ax, xdata_key, ydata_key, xlim, xlim_scale=None, color='black'):
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
        self.xdata_key = xdata_key
        self.ydata_key = ydata_key
        #self.xlim_scale = xlim_scale
        # plot 
        ax.plot(self.spec.xdata[xdata_key], self.spec.ydata[ydata_key], color=color)
        #set axes limits  
        xlim_auto = [0, self.spec._hv]
        xlim_plot = self._set_xlimit(ax, xlim, xlim_auto)
        if xlim_scale is None:
            self._auto_ylim(ax, self.spec.xdata[xdata_key], self.spec.ydata[ydata_key],
                            [xlim_plot[1], xlim_plot[0]])
        else:
            self._auto_ylim(ax, self.spec.xdata[xdata_key], self.spec.ydata[ydata_key],
                            [xlim_scale[1], xlim_scale[0]])


    def plot_ebin(self, ax, xdata_key, ydata_key, xlim, xlim_scale=None, color='black'):
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
        self.xdata_key = xdata_key
        self.ydata_key = ydata_key
        #self.xlim_scale = xlim_scale
        # plot
        ax.plot(self.spec.xdata[xdata_key], self.spec.ydata[ydata_key], color=color)
        #set axes limits  
        xlim_auto = [0, self.spec._hv]
        xlim_plot = self._set_xlimit(ax, xlim, xlim_auto)
        if xlim_scale is None:
            self._auto_ylim(ax, self.spec.xdata[xdata_key], self.spec.ydata[ydata_key],
                            xlim_plot)
        else:
            self._auto_ylim(ax, self.spec.xdata[xdata_key], self.spec.ydata[ydata_key],
                            xlim_scale)


    def show_idx(self, ydata_key='auto', xlim=['auto', 'auto'], xlim_scale=None, show_info=False):
        View.show_idx(self, ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale, show_info=show_info)
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid(), text_pos='right')
        self.fig.show()

        
    def show_tof(self, xdata_key='auto', ydata_key='auto', time_label='Flight Time',
                 time_unit=1e-6, xlim=[0, 'auto'], xlim_scale=None, show_info=False):
        View.show_tof(self, xdata_key=xdata_key, ydata_key=ydata_key, time_label=time_label, 
                      time_unit=time_unit, xlim=xlim, xlim_scale=xlim_scale, show_info=show_info)
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid(), text_pos='right')        
        self.fig.show()
        

    def show_ekin(self, xdata_key='auto', ydata_key='auto', xlim=['auto', 'auto'], xlim_scale=None, show_info=False):
        self._single_fig_output()
        # set data keys
        key_deps = {'ekin': ['jIntensity', 'jIntensitySub'],
                    'ekinGauged': ['jIntensityGauged', 'jIntensityGaugedSub']} 
        xdata_key, ydata_key = self._auto_key_selection(xdata_key=xdata_key, ydata_key=ydata_key, key_deps=key_deps)        
        self.plot_ekin(self.ax, xdata_key=xdata_key, ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale)
        self.ax.set_xlabel(r'E$_{kin}$ (eV)')
        self.ax.set_ylabel('Intensity (a.u.)')     
        self._addtext_file_id(self.ax)
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid(), text_pos='right')
        self._addtext_statusmarker(self.ax, xdata_key=xdata_key, ydata_key=ydata_key)
        if show_info:
            self._addtext_info(self.ax, self.spec.mdata.data('info'), text_pos='right')        
        self.fig.show()


    def show_ebin(self, xdata_key='auto', ydata_key='auto', xlim=['auto', 'auto'], xlim_scale=None, show_info=False):
        self._single_fig_output()
        # set data keys
        key_deps = {'ebin': ['jIntensity', 'jIntensitySub'],
                    'ebinGauged': ['jIntensityGauged', 'jIntensityGaugedSub']} 
        xdata_key, ydata_key = self._auto_key_selection(xdata_key=xdata_key, ydata_key=ydata_key, key_deps=key_deps)         
        self.plot_ebin(self.ax, xdata_key=xdata_key, ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale)
        self.ax.set_xlabel(r'E$_{bin}$ (eV)')
        self.ax.set_ylabel('Intensity (a.u.)')      
        self._addtext_file_id(self.ax)
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid())
        self._addtext_statusmarker(self.ax, xdata_key=xdata_key, ydata_key=ydata_key)
        if show_info:
            self._addtext_info(self.ax, self.spec.mdata.data('info'))             
        self.fig.show()
        
        
    def show_gaugeref(self):
        gaugeRef = self.spec.mdata.data('gaugeRef')
        gaugeSpec = load.load_pickle(self.spec.cfg, gaugeRef)
        gaugeSpec.view.show_ebin_fit()
        
        
    def _add_spec(self, specfile, xscale=1, yscale=1, yscale_type=None, xoffset=0, yoffset=0, color='blue', clusterid_fontsize=28, ax=None):
        '''
        Adds another spectrum to the plot using the same data keys as the original plot.
        The spectrum can be modified by:
        xscale: scalar to scale the xdata
        yscale: scalar to scale the ydata OR
                list specifying a xdata interval, yscale is then chosen that both spectra have the same area
                on that interval or the same max intensity
        yscale_type: 'area' or 'max', specifies how yscale is calculated on an interval
        x/yoffset: scalar shift the spectrum in x-/y-direction
        
        TODO: fallback for missing data keys (e.g. one may want to compare 'ebinGauged' to 'ebin') 
        '''
        if ax is None:
            ax = self.ax
        self.comp_spec_data.update({'specfile': specfile,
                                    'xscale': xscale,
                                    'yscale': yscale,
                                    'yscale_type': yscale_type,
                                    'xoffset': xoffset,
                                    'yoffset': yoffset,
                                    'color': color,
                                    'xdata_key': self.xdata_key})
        addspec = load.load_pickle(self.spec.cfg, specfile)
        time_unit = 1
        if 'tof' in self.xdata_key:
            time_unit = self.timeunit
        xdata = addspec.xdata[self.xdata_key]/time_unit*xscale + xoffset
        # autoscale intensity if necessary
        if type(yscale) is list:
            lb, ub = yscale[0], yscale[1]
            ilb = abs(xdata - lb).argmin()
            iub = abs(xdata - ub).argmin()
            if ilb > iub: # needed for 'reversed' spectra, e.g. E_kin
                ilb_tmp = ilb
                ilb = iub
                iub = ilb_tmp
            ilb_ref = abs(self.spec.xdata[self.xdata_key]/time_unit - lb).argmin()
            iub_ref = abs(self.spec.xdata[self.xdata_key]/time_unit - ub).argmin()
            if ilb_ref > iub_ref: # needed for 'reversed' spectra, e.g. E_kin
                ilb_ref_tmp = ilb_ref
                ilb_ref = iub_ref
                iub_ref = ilb_ref_tmp            
            print('boundaries:', ilb, iub, ilb_ref, iub_ref)
            if yscale_type is None or yscale_type == 'area':
                yscale = self._scalefactor_equal_area(self.spec.xdata[self.xdata_key][ilb_ref:iub_ref]/time_unit,
                                                      self.spec.ydata[self.ydata_key][ilb_ref:iub_ref],
                                                      xdata[ilb:iub], 
                                                      addspec.ydata[self.ydata_key][ilb:iub],
                                                      yoffset)
            elif yscale_type == 'max':
                yscale = self._scalefactor_equal_max(self.spec.ydata[self.ydata_key][ilb_ref:iub_ref] - yoffset,
                                                     addspec.ydata[self.ydata_key][ilb:iub])
            else:
                raise ValueError('yscale_type must be "area" or "max"')
            print('New scale factor:', yscale)    
        
        ydata = addspec.ydata[self.ydata_key]*yscale + yoffset
        if self.txt_clusterid.get_position()[0] == 0.05:
            text_pos = 'left'
        else:
            text_pos = 'right'
        self._addtext_cluster_id(ax, addspec.view._pretty_format_clusterid(), text_pos=text_pos, 
                                 fontsize=clusterid_fontsize, color=color, valign='top', voffset=-0.02)
        #cluster_ids = '{}\n{}'.format(self._pretty_format_clusterid(), addspec.view._pretty_format_clusterid())
        #self.txt_clusterid.set_text(cluster_ids)
        self.add_plot(ax, xdata, ydata, color=color, file_id=os.path.basename(addspec.mdata.data('datFile')))
        
        
    def add_spec(self, specfile, xscale=1, yscale=1, yscale_type=None, xoffset=0, yoffset=0, color='blue', clusterid_fontsize=28, ax=None):
        self._add_spec(specfile, xscale, yscale, yscale_type, xoffset, yoffset, color, clusterid_fontsize, ax)
        self.fig.canvas.draw()
        
        
    def _add_fermiscaled_spec(self, specfile, xscale='fermi_energy', yscale=1, yscale_type='area', color='blue', clusterid_fontsize=28, ax=None):
        '''
        Right now a alkali specific shortcut for _add_spec, which automatically sets some values.
        Might be moved to a special class (?).
        '''
        if ax is None:
            ax = self.ax
        addspec = load.load_pickle(self.spec.cfg, specfile)
        try:
            ea = addspec.mdata.data('electronAffinity')
            ea_ref = self.spec.mdata.data('electronAffinity')
        except:
            raise ValueError('Missing electron affinity value.')
        if xscale == 'fermi_energy':
            self.comp_spec_data['xscale_type'] = xscale
            xscale = self.spec.cfg.bulk_fermi_energy[self.spec.mdata.data('clusterBaseUnit')]/self.spec.cfg.bulk_fermi_energy[addspec.mdata.data('clusterBaseUnit')]
        elif type(xscale) not in [int, float]:
            raise ValueError('xscale must be numeric or "fermy_energy"')
        if 'ebin' in self.xdata_key:
            xoffset = ea_ref - ea*xscale
        elif 'ekin' in self.xdata_key:
            xoffset = (self.spec._hv - ea_ref) - (self.spec._hv - ea)*xscale
        elif 'tof' in self.xdata_key:
            xoffset = sqrt(self.spec._pFactor/(self.spec._hv - ea_ref))/self.timeunit - sqrt(self.spec._pFactor/(self.spec._hv - ea))/self.timeunit*xscale
        print('xoffset calculated from eas:', xoffset)
        self._add_spec(specfile=specfile, xscale=xscale, yscale=yscale, yscale_type=yscale_type, xoffset=xoffset,
                      color=color, clusterid_fontsize=clusterid_fontsize, ax=ax)
        
        
    def add_fermiscaled_spec(self, specfile, xscale='fermi_energy', yscale=1, yscale_type='area', color='blue', clusterid_fontsize=28, ax=None):
        self._add_fermiscaled_spec(specfile, xscale, yscale, yscale_type, color, clusterid_fontsize, ax)
        self.fig.canvas.draw()


    def show_comp_spec(self, comp_spec_id, **keywords):
        base_plot_map = {'tof': self.show_tof,
                         'ekin': self.show_ekin,
                         'ebin': self.show_ebin}
        if type(comp_spec_id) is not list:
            comp_spec_id = [comp_spec_id]
        base_plot_mode = None
        for csid in comp_spec_id:
            if csid not in self.spec.mdata.data('compSpecs').keys():
                raise ValueError('No comparison spec with id "{}" is attached to this spec.')
            # set mode for base plot and plot
            if base_plot_mode is None:
                for k in base_plot_map.keys():
                    if k in self.spec.mdata.data('compSpecs')[csid]['xdata_key']:
                        base_plot_map[k](**keywords)
                        base_plot_mode = k
                        break
            elif base_plot_mode not in self.spec.mdata.data('compSpecs')[csid]['xdata_key']:
                raise ValueError('Comparison spectrum type ({}) does not fit to chosen view ({}).'.format(self.spec.mdata.data('compSpecs')[csid]['xdata_key'],
                                                                                                          base_plot_mode))
            if 'xscale_type' in self.spec.mdata.data('compSpecs')[csid].keys() and self.spec.mdata.data('compSpecs')[csid]['xscale_type'] is 'fermi_energy':
                self._add_fermiscaled_spec(self.spec.mdata.data('compSpecs')[csid]['specfile'],
                                          self.spec.mdata.data('compSpecs')[csid]['xscale_type'],
                                          self.spec.mdata.data('compSpecs')[csid]['yscale'],
                                          self.spec.mdata.data('compSpecs')[csid]['yscale_type'],
                                          self.spec.mdata.data('compSpecs')[csid]['color'])
            else:
                self._add_spec(self.spec.mdata.data('compSpecs')[csid]['specfile'],
                              self.spec.mdata.data('compSpecs')[csid]['xscale'],
                              self.spec.mdata.data('compSpecs')[csid]['yscale'],
                              self.spec.mdata.data('compSpecs')[csid]['yscale_type'],
                              self.spec.mdata.data('compSpecs')[csid]['xoffset'],
                              self.spec.mdata.data('compSpecs')[csid]['yoffset'],
                              self.spec.mdata.data('compSpecs')[csid]['color'])
            
        


class ViewPt(ViewPes):
    def __init__(self,spec):
        ViewPes.__init__(self, spec)
        
    
    def _addtext_gauge_par(self, ax, text_pos='left', fit_par='fitPar', fontsize=12):
        if text_pos == 'left':
            pos_x, pos_y = 0.05, 0.4
        elif text_pos == 'right':
            pos_x, pos_y = 0.95, 0.4
        else:
            raise ValueError('text_pos must be one of: left, right. Got "%s" instead.'%(str(text_pos)))        
        ax.text(pos_x, pos_y,
                'E$_{offset}$: %.2f meV\nt$_{offset}$: %.3f ns\nl$_{scale}$: %.3f\n$\Delta$l: %.1f mm'%(self.spec.mdata.data(fit_par)[-3]*1e3,
                                        self.spec.mdata.data(fit_par)[-2]*1e9,
                                        self.spec.mdata.data(fit_par)[-1],
                                        self.spec.mdata.data('flightLength')*1000*
                                        (1/sqrt(self.spec.mdata.data(fit_par)[-1]) -1)),
                transform = ax.transAxes, fontsize=fontsize, horizontalalignment=text_pos)
               
    
    def plot_tof_fit(self, ax, fit_par, time_unit, color='blue', color_peaks='DimGray', single_peaks=False):        
        if self.spec.mdata.data('fitCutoff') is None:
            ax.plot(self.spec.xdata['tof']/time_unit,
                    self.spec._multi_gauss_trans(self.spec.xdata['tof'],
                                                 self.spec.mdata.data('fitPeakPos'),
                                                 self.spec.mdata.data(fit_par)),
                    color=color)
            cutoff_idx = len(self.spec.xdata['tof'])
        else:
            cutoff_idx = (abs(self.spec.xdata['tof'] - self.spec.mdata.data('fitCutoff'))).argmin()
            
            ax.plot(self.spec.xdata['tof'][:cutoff_idx]/time_unit,
                    self.spec._multi_gauss_trans(self.spec.xdata['tof'][:cutoff_idx],
                                                 self.spec.mdata.data('fitPeakPos'),
                                                 self.spec.mdata.data(fit_par)),
                    color=color)
            ax.plot(self.spec.xdata['tof'][cutoff_idx:]/time_unit,
                    self.spec._multi_gauss_trans(self.spec.xdata['tof'][cutoff_idx:],
                                                 self.spec.mdata.data('fitPeakPos'),
                                                 self.spec.mdata.data(fit_par)),
                    color=color, ls='--')
         
        # plot single peaks, if there are more than one
        if single_peaks and len(self.spec.mdata.data(fit_par)) > 4:        
            plist = list(self.spec.mdata.data(fit_par))
            xlist = list(self.spec.mdata.data('fitPeakPos'))
            lscale = plist.pop()
            toff = plist.pop()
            Eoff = plist.pop()
            while len(plist) >= 2:
                sigma = plist.pop()
                A = plist.pop()
                m = xlist.pop()
                
                ax.plot(self.spec.xdata['tof'][:cutoff_idx]/time_unit,
                        self.spec._multi_gauss_trans(self.spec.xdata['tof'][:cutoff_idx],
                                                     [m],
                                                     [A, sigma, Eoff, toff, lscale]),
                        color=color_peaks)
    
               
    def plot_energy_fit(self, ax, fit_par, xdata_key, color='blue', color_peaks='DimGray', single_peaks=False):
        if self.spec.mdata.data('fitCutoff') is None:
            ax.plot(self.spec.xdata[xdata_key],
                    self.spec.jtrans(self.spec._multi_gauss_trans(self.spec.xdata['tof'],
                                                                  self.spec.mdata.data('fitPeakPos'),
                                                                  self.spec.mdata.data(fit_par)),
                                     self.spec.xdata['tof']),
                    color=color)
            cutoff_idx = len(self.spec.xdata[xdata_key])
        else:
            cutoff_idx = (abs(self.spec.xdata['tof'] - self.spec.mdata.data('fitCutoff'))).argmin()
            ax.plot(self.spec.xdata[xdata_key][:cutoff_idx],
                    self.spec.jtrans(self.spec._multi_gauss_trans(self.spec.xdata['tof'][:cutoff_idx],
                                                                  self.spec.mdata.data('fitPeakPos'),
                                                                  self.spec.mdata.data(fit_par)),
                                     self.spec.xdata['tof'][:cutoff_idx]),
                    color=color)
            ax.plot(self.spec.xdata[xdata_key][cutoff_idx:],
                    self.spec.jtrans(self.spec._multi_gauss_trans(self.spec.xdata['tof'][cutoff_idx:],
                                                                  self.spec.mdata.data('fitPeakPos'),
                                                                  self.spec.mdata.data(fit_par)),
                                     self.spec.xdata['tof'][cutoff_idx:]),
                    color=color, ls='--')            
         
        # plot single peaks, if there are more than one
        if single_peaks and len(self.spec.mdata.data(fit_par)) > 4:        
            plist = list(self.spec.mdata.data(fit_par))
            xlist = list(self.spec.mdata.data('fitPeakPos'))
            lscale = plist.pop()
            toff = plist.pop()
            Eoff = plist.pop()
            while len(plist) >= 2:
                sigma = plist.pop()
                A = plist.pop()
                m = xlist.pop()
                
#                 ax.plot(self.spec.xdata['tof'][:cutoff_idx]/time_unit,
#                         self.spec._multi_gauss_trans(self.spec.xdata['tof'][:cutoff_idx],
#                                                      [m],
#                                                      [A, sigma, Eoff, toff, lscale]),
#                         color=color_peaks)            
                
                ax.plot(self.spec.xdata[xdata_key][:cutoff_idx],
                    self.spec.jtrans(self.spec._multi_gauss_trans(self.spec.xdata['tof'][:cutoff_idx],
                                                                  [m],
                                                                  [A, sigma, Eoff, toff, lscale]),
                                     self.spec.xdata['tof'][:cutoff_idx]),
                    color=color_peaks)
               

    
    def show_tof_fit(self, fit_par='fitPar', time_unit=1e-6, time_label='Flight Time', xlim=[0, 'auto'], xlim_scale=None, single_peaks=True):
        xdata_key = 'tof'
        ydata_key = self.spec.mdata.data('fitYdataKey')
        self._single_fig_output()
        self.plot_tof(self.ax, xdata_key=xdata_key, ydata_key=ydata_key,
                      time_unit=time_unit, xlim=xlim, xlim_scale=xlim_scale)
        self.plot_tof_fit(self.ax, fit_par=fit_par, time_unit=time_unit, single_peaks=single_peaks)   
        self._set_xlabel_time(self.ax, label=time_label, time_unit=time_unit)
        self.ax.set_ylabel('Intensity (a.u.)')
        self._addtext_file_id(self.ax)
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid(), text_pos='right') 
        self._addtext_gauge_par(self.ax, fit_par=fit_par, text_pos='right')
        self._addtext_statusmarker(self.ax, xdata_key=xdata_key, ydata_key=ydata_key)        
        self.fig.show()
        
        
    def _show_energy_fit(self, xdata_key, fit_par, xlim, xlim_scale, single_peaks):
        plot_method = {'ekin': self.plot_ekin, 'ebin': self.plot_ebin}
        if xdata_key not in ['ekin', 'ebin']:
            raise ValueError("xdata_key must be one of: 'ekin', 'ebin'")
        if 'Sub' in self.spec.mdata.data('fitYdataKey'):
            ydata_key = 'jIntensitySub'
        else:
            ydata_key = 'jIntensity'
        self._single_fig_output()
        plot_method[xdata_key](self.ax, xdata_key=xdata_key, ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale)
        self.plot_energy_fit(self.ax, fit_par=fit_par, xdata_key=xdata_key, single_peaks=single_peaks)
        self.ax.set_ylabel('Intensity (a.u.)')        
        self._addtext_file_id(self.ax)
        self._addtext_statusmarker(self.ax, xdata_key=xdata_key, ydata_key=ydata_key)
        
        
    def show_ekin_fit(self, fit_par='fitPar', xlim=['auto', 'auto'], xlim_scale=None, single_peaks=False):
        self._show_energy_fit(xdata_key='ekin', fit_par=fit_par, xlim=xlim, xlim_scale=xlim_scale, single_peaks=single_peaks)
        self.ax.set_xlabel(r'E$_{kin}$ (eV)')
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid(), text_pos='right') 
        self._addtext_gauge_par(self.ax, fit_par=fit_par, text_pos='right')            
        self.fig.show()    
        
        
    def show_ebin_fit(self, fit_par='fitPar', xlim=['auto', 'auto'], xlim_scale=None, single_peaks=False):
        self._show_energy_fit(xdata_key='ebin', fit_par=fit_par, xlim=xlim, xlim_scale=xlim_scale, single_peaks=single_peaks)
        self.ax.set_xlabel(r'E$_{bin}$ (eV)')
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid()) 
        self._addtext_gauge_par(self.ax, fit_par=fit_par)            
        self.fig.show()    

        
        
class ViewWater(ViewPes):
    def __init__(self,spec):
        ViewPes.__init__(self, spec)
        

    def _addtext_fitvalues(self, ax, plot_type, fit_par, time_unit=1, text_pos='left', fontsize=12):
        def time_prefix(time_unit):
            if time_unit not in [1, 1e-3, 1e-6, 1e-9]:
                raise ValueError('time_unit must be one of: 1, 1e-3, 1e-6, 1e-9.')
            prefix_map = ['', 'm', '$\mu $', 'n']
            prefix = prefix_map[int(abs(log10(time_unit)/3))]
            return prefix
        
        #peak_width = round(self.spec._get_peak_width(), 3)
        
        if plot_type == 'ebin' and 'tof' in self.spec.mdata.data('fitXdataKey'):
            peak_values = list(self.spec.ebin(self.spec.mdata.data(fit_par)[:-2:2]))
            peakPos_unit = 'eV'
        elif plot_type == 'ekin' and 'tof' in self.spec.mdata.data('fitXdataKey'):
            peak_values = list(self.spec.ekin(self.spec.mdata.data(fit_par)[:-2:2]))
            peakPos_unit = 'eV'
        elif plot_type == 'tof' and 'tof' in self.spec.mdata.data('fitXdataKey'):
            peak_values = list(self.spec.mdata.data(fit_par)[:-2:2])
            peakPos_unit = '{}s'.format(time_prefix(time_unit))
        else:
            raise ValueError("Can't add values for this plot combination.")
            
        if text_pos == 'left':
            pos_x, pos_y = 0.05, 0.5
        elif text_pos == 'right':
            pos_x, pos_y = 0.95, 0.5
        else:
            raise ValueError('text_pos must be one of: left, right. Got "%s" instead.'%(str(text_pos)))
#         peak_number = 1
#         for peak in peak_values:
#             ax.text(pos_x, pos_y, '%i. Peak: %.2f %s'%(peak_number, round(peak/time_unit, 3), peakPos_unit),
#                     transform = ax.transAxes, fontsize=fontsize, horizontalalignment=text_pos)
#             peak_number+=1
#             pos_y-=0.05
#         ax.text(pos_x, pos_y-0.025, 'fwhm: %.3f eV'%(peak_width),
#                 transform = ax.transAxes, fontsize=fontsize, horizontalalignment=text_pos)
        fit_values_str = '\n'.join(['{:.2f} {}'.format(p/time_unit, peakPos_unit) for p in peak_values])
        fit_values_str += '\n\nfwhm: {:.3f} eV'.format(self.spec._get_peak_width())
        ax.text(pos_x, pos_y, fit_values_str,transform = ax.transAxes, fontsize=fontsize, 
                horizontalalignment=text_pos, verticalalignment='center')
   
   
    
    def plot_tof_fit(self, ax, xdata_key, ydata_key, fit_par, time_unit, color='blue', color_peaks='DimGray'):
        if self.spec.mdata.data('fitCutoff') is None:
            ax.plot(self.spec.xdata[xdata_key]/time_unit,
                    self.spec.multi_gl_trans(self.spec.xdata[xdata_key], self.spec.mdata.data(fit_par)),
                    color=color)
            cutoff_idx = len(self.spec.xdata[xdata_key])
        else:
            cutoff_idx = (abs(self.spec.xdata[xdata_key] - self.spec.mdata.data('fitCutoff'))).argmin()            
            ax.plot(self.spec.xdata[xdata_key][:cutoff_idx]/time_unit,
                    self.spec.multi_gl_trans(self.spec.xdata[xdata_key][:cutoff_idx], self.spec.mdata.data(fit_par)),
                    color=color)
            ax.plot(self.spec.xdata[xdata_key][cutoff_idx:]/time_unit,
                    self.spec.multi_gl_trans(self.spec.xdata[xdata_key][cutoff_idx:], self.spec.mdata.data(fit_par)),
                    color=color, ls='--')
        ax.relim()
        # plot single peaks, if there are more than one
        if len(self.spec.mdata.data(fit_par)) > 4:        
            plist = list(self.spec.mdata.data(fit_par))
            sl = plist.pop()
            sg = plist.pop()
            while len(plist) >= 2:
                A = plist.pop()
                xmax = plist.pop()
                if self.spec.mdata.data('fitCutoff') is None:
                    ax.plot(self.spec.xdata[xdata_key]/time_unit,
                            self.spec.multi_gl_trans(self.spec.xdata[xdata_key], [xmax,A,sg,sl]),
                            color=color_peaks)
                else:
                    ax.plot(self.spec.xdata[xdata_key][:cutoff_idx]/time_unit,
                            self.spec.multi_gl_trans(self.spec.xdata[xdata_key][:cutoff_idx], [xmax,A,sg,sl]),
                            color=color_peaks) 
                    ax.plot(self.spec.xdata[xdata_key][cutoff_idx:]/time_unit,
                            self.spec.multi_gl_trans(self.spec.xdata[xdata_key][cutoff_idx:], [xmax,A,sg,sl]),
                            color=color_peaks, ls='--')
                    
                    
    
    def plot_energy_fit(self, ax, fit_par, xdata_key, fit_xdata_key, color='blue', color_peaks='DimGray'):
        if self.spec.mdata.data('fitCutoff') is None:
            ax.plot(self.spec.xdata[xdata_key],
                    self.spec.jtrans(self.spec.multi_gl_trans(self.spec.xdata[fit_xdata_key],
                                                                  self.spec.mdata.data(fit_par)),
                                     self.spec.xdata[fit_xdata_key]),
                    color=color)
            cutoff_idx = len(self.spec.xdata[xdata_key])
        else:
            cutoff_idx = (abs(self.spec.xdata[fit_xdata_key] - self.spec.mdata.data('fitCutoff'))).argmin()
            ax.plot(self.spec.xdata[xdata_key][:cutoff_idx],
                    self.spec.jtrans(self.spec.multi_gl_trans(self.spec.xdata[fit_xdata_key][:cutoff_idx],
                                                                  self.spec.mdata.data(fit_par)),
                                     self.spec.xdata[fit_xdata_key][:cutoff_idx]),
                    color=color)
            ax.plot(self.spec.xdata[xdata_key][cutoff_idx:],
                    self.spec.jtrans(self.spec.multi_gl_trans(self.spec.xdata[fit_xdata_key][cutoff_idx:],
                                                                  self.spec.mdata.data(fit_par)),
                                     self.spec.xdata[fit_xdata_key][cutoff_idx:]),
                    color=color, ls='--')
                    
        ax.relim()
        # plot single peaks, if there are more than one
        if len(self.spec.mdata.data(fit_par)) > 4:
            plist = list(self.spec.mdata.data(fit_par))
            sl = plist.pop()
            sg = plist.pop()
            while len(plist) >= 2:
                A = plist.pop()
                xmax = plist.pop()
                if self.spec.mdata.data('fitCutoff') is None:
                    ax.plot(self.spec.xdata[xdata_key],
                            self.spec.jtrans(self.spec.multi_gl_trans(self.spec.xdata[fit_xdata_key],
                                                                [xmax,A,sg,sl]),
                                             self.spec.xdata[fit_xdata_key]),
                            color=color_peaks)
                else:
                    ax.plot(self.spec.xdata[xdata_key][:cutoff_idx],
                            self.spec.jtrans(self.spec.multi_gl_trans(self.spec.xdata[fit_xdata_key][:cutoff_idx],
                                                                [xmax,A,sg,sl]),
                                             self.spec.xdata[fit_xdata_key][:cutoff_idx]),
                            color=color_peaks)
                    ax.plot(self.spec.xdata[xdata_key][cutoff_idx:],
                            self.spec.jtrans(self.spec.multi_gl_trans(self.spec.xdata[fit_xdata_key][cutoff_idx:],
                                                                [xmax,A,sg,sl]),
                                             self.spec.xdata[fit_xdata_key][cutoff_idx:]),
                            color=color_peaks, ls='--')
    
    
#    'TODO: implement gauging!'
#    def plot_ebin_fit(self, ax, xdata_key, ydata_key, fitPar, color='blue', color_peaks='DimGray'):
#        if fitPar in ['fitPar', 'fitPar0']:
#            ax.plot(self.spec.xdata['ebin'],
#                    self.spec.mGl(self.spec.xdata['ebin'], self.spec.mdata.data(fitPar)),
#                    color=color)
#            ax.relim()
#            # plot single peaks, if there are more than one
#            if len(self.spec.mdata.data(fitPar)) > 4:
#                plist = list(self.spec.mdata.data(fitPar))
#                sl = plist.pop()
#                sg = plist.pop()
#                while len(plist) >= 2:
#                    A = plist.pop()
#                    xmax = plist.pop()
#                    ax.plot(self.spec.xdata['ebin'],
#                            self.spec.mGl(self.spec.xdata['ebin'], [xmax,A,sg,sl]),
#                            color=color_peaks)
#        else:
#            ax.plot(self.spec.xdata['ebin'],
#                    self.spec.jtrans(self.spec.mGlTrans(self.spec.xdata['tof'],
#                                                        self.spec.mdata.data(fitPar)),
#                                     self.spec.xdata['tof']),
#                    color='blue')
#            ax.relim()
#            # plot single peaks, if there are more than one
#            if len(self.spec.mdata.data(fitPar)) > 4:
#                plist = list(self.spec.mdata.data(fitPar))
#                sl = plist.pop()
#                sg = plist.pop()
#                while len(plist) >= 2:
#                    A = plist.pop()
#                    xmax = plist.pop()
#                    ax.plot(self.spec.xdata['ebin'],
#                            self.spec.jtrans(self.spec.mGlTrans(self.spec.xdata['tof'],
#                                                                [xmax,A,sg,sl]),
#                                             self.spec.xdata['tof']),
#                            color='DimGray')             


    def show_tof_fit(self, fit_par='fitPar', time_unit=1e-6, time_label='Flight Time',
                     xlim=[0, 'auto'], xlim_scale=None):
        if 'fitted' not in self.spec.mdata.data('systemTags'):
            raise ValueError('Spectrum not yet fitted. Fit first.')            
        self._single_fig_output()
        # set data keys
        xdata_key = self.spec.mdata.data('fitXdataKey')
        ydata_key = self.spec.mdata.data('fitYdataKey')
        # plot
        self.plot_tof(self.ax, xdata_key=xdata_key, ydata_key=ydata_key, time_unit=time_unit,
                      xlim=xlim, xlim_scale=xlim_scale, color='black')
        self.plot_tof_fit(self.ax, xdata_key=xdata_key, ydata_key=ydata_key, fit_par=fit_par,
                          time_unit=time_unit)
        # setup axes
        self._set_xlabel_time(self.ax, label=time_label, time_unit=time_unit)
        self.ax.set_ylabel('Intensity (a.u.)')
        self._addtext_file_id(self.ax)
        self._addtext_statusmarker(self.ax, xdata_key=xdata_key, ydata_key=ydata_key)
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid(), text_pos='right')
        self._addtext_fitvalues(self.ax, plot_type='tof', fit_par=fit_par, time_unit=time_unit, text_pos='right')
        self.fig.show()      


    def _show_energy_fit(self, plot_type, fit_par, xlim, xlim_scale):
        plot_key_map = {'ekin': {'tof_intensity': [self.plot_ekin, 'ekin', 'jIntensity'],
                                 'tof_intensitySub': [self.plot_ekin, 'ekin', 'jIntensitySub'],
                                 'tofGauged_intensity': [self.plot_ekin, 'ekinGauged', 'jIntensityGauged'],
                                 'tofGauged_intensitySub': [self.plot_ekin, 'ekinGauged', 'jIntensityGaugedSub'],
                                 },
                        'ebin': {'tof_intensity': [self.plot_ebin, 'ebin', 'jIntensity'],
                                 'tof_intensitySub': [self.plot_ebin, 'ebin', 'jIntensitySub'],
                                 'tofGauged_intensity': [self.plot_ebin, 'ebinGauged', 'jIntensityGauged'],
                                 'tofGauged_intensitySub': [self.plot_ebin, 'ebinGauged', 'jIntensityGaugedSub'],
                                 }
                        }
        plot_method, xdata_key, ydata_key = plot_key_map[plot_type]['{}_{}'.format(self.spec.mdata.data('fitXdataKey'),
                                                                                   self.spec.mdata.data('fitYdataKey'))]
        self._single_fig_output()
        plot_method(self.ax, xdata_key=xdata_key, ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale)
        self.plot_energy_fit(self.ax, fit_par=fit_par, xdata_key=xdata_key,
                             fit_xdata_key=self.spec.mdata.data('fitXdataKey'))
        self.ax.set_ylabel('Intensity (a.u.)')        
        self._addtext_file_id(self.ax)
        self._addtext_statusmarker(self.ax, xdata_key=xdata_key, ydata_key=ydata_key)


    def show_ekin_fit(self, fit_par='fitPar', xlim=[0, 'auto'], xlim_scale=None):
        self._show_energy_fit(plot_type='ekin', fit_par=fit_par, xlim=xlim, xlim_scale=xlim_scale)
        self.ax.set_xlabel(r'E$_{kin}$ (eV)')
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid(), text_pos='right') 
        self._addtext_fitvalues(self.ax, plot_type='ekin', fit_par=fit_par, text_pos='right')            
        self.fig.show()  


    def show_ebin_fit(self, fit_par='fitPar', xlim=[0, 'auto'], xlim_scale=None):
        self._show_energy_fit(plot_type='ebin', fit_par=fit_par, xlim=xlim, xlim_scale=xlim_scale)
        self.ax.set_xlabel(r'E$_{bin}$ (eV)')
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid()) 
        self._addtext_fitvalues(self.ax, plot_type='ebin', fit_par=fit_par)            
        self.fig.show()  

            
    
#    def show_ebin_fit(self, fitPar='fitPar', xlim=[0, 'auto']):
#        if 'fitted' not in self.spec.mdata.data('systemTags'):
#            raise ValueError('Spectrum not yet fitted. Fit first.') 
#        self._single_fig_output()
#        
#        if fitPar in ['fitPar', 'fitPar0']:
#            gauged = self.plot_ebin(self.ax, show_gauged=self.spec.mdata.data('fitGauged'),
#                                   subtractBg=self.spec.mdata.data('fitSubtractBg'))
#        else:
#            gauged = self.plot_ebin(self.ax, show_gauged=self.spec.mdata.data('fitGaugedTof'),
#                                   subtractBg=self.spec.mdata.data('fitSubtractBgTof'))
#        self.plot_ebin_fit(self.ax, fitPar)
#        self._addtext_file_id(self.ax)
#        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid())
#        self._addtext_fitvalues(self.ax, peakpos_unit='eV')
#        if gauged:        
#            self._addtext_statusmarker(self.ax, xdata_key=xdata_key, ydata_key=ydata_key)
#        self.fig.show()
           





        
        
        
class ViewMs(View):
    def __init__(self, spec):
        View.__init__(self, spec)   
        
        
    def _xlabel_str(self, mass_key):
        if mass_key == 'cluster':
            xlabel = 'Cluster Size (#%s)'%self.spec.mdata.data('clusterBaseUnit')
        elif mass_key == 's_u':
            xlabel = 'Cluster Mass (simplified u)'
        else:
            xlabel = 'Cluster Mass (u)'
            
        return xlabel        

    
    def plot_ms(self, ax, mass_key, xlim, xlim_scale=None, color='black'):
        ax.plot(self.spec.xdata[mass_key], self.spec.ydata['intensity'], color=color)
        # set axes limits
        xlim_auto = [self.spec.xdata[mass_key][0], self.spec.xdata[mass_key][-1]]
        xlim_plot = self._set_xlimit(ax, xlim, xlim_auto)
        if xlim_scale is None:
            self._auto_ylim(ax, self.spec.xdata[mass_key], self.spec.ydata['intensity'],
                            xlim_plot)
        else:
            self._auto_ylim(ax, self.spec.xdata[mass_key], self.spec.ydata['intensity'],
                            xlim_scale)
#         ax.relim()
#         ax.autoscale()
        
        
    def show_ms(self, mass_key='cluster', xlim=['auto', 'auto'], xlim_scale=None, color='black'):
        self._single_fig_output()
        self.plot_ms(ax=self.ax, mass_key=mass_key, xlim=xlim, xlim_scale=xlim_scale, color=color)
        self.ax.set_xlabel(self._xlabel_str(mass_key))
        self.ax.set_ylabel('Intensity (a.u.)')
        self._addtext_file_id(self.ax)
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid(ms=True))
        self.fig.show()
        
        
        
