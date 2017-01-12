import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import os.path
#from numpy import log10,sqrt, abs, argmin, arange, sort
import numpy as np

import load_3f
from matplotlib.pyplot import xlim
from smooth import moving_avg_gaussian

class View(object):
    def __init__(self, spec):
        self.spec = spec
        self.xdata_key = None
        self.ydata_key = None
        self.timeunit = None
        self.xlim_scale = None
        self.ymax = None
        self.comp_spec_data = {}
        

    def _single_fig_output(self, size):
# this does not work (?)
#         if hasattr(self, 'fig'):
#             try:
#                 print('Testing if plot window still exists ...')
#                 self.fig.show()
#             except Exception:
#                 del self.fig
#         if size:
#             'TODO: presets are mere personal. For a general approach probably not suitable.'
#             presets = {'p1': [14, 14*3/7],
#                        'p2': [7, 7*5/7],
#                        'p3': [4.8, 4.8*5/6]}
#             if isinstance(size, str) and size in presets.keys():
#                 size = presets[size]
#             else:
#                 raise ValueError('size must be either a list [width, height] or one of the following presets: '.format(list(presets.keys())))
#             w = size[0]/2.54
#             h = size[1]/2.54
#             size = (w,h)
                
        if hasattr(self, 'fig'):      
            self.ax.lines = []
            self.ax.texts = []
#             if w and h:
#                 self.fig.set_size_inches(w,h)
        else:
            self.fig = plt.figure() #figsize=size)
            #print 'Figure created.'
            self.ax = self.fig.add_subplot(1,1,1)
        # actually show figure
        self.fig.show()
        'TODO: is this still needed since It is now in init?'
        self.comp_spec_data = {}
    
    
    def _close_fig(self):
        plt.close(self.fig)
        
        
    def __scale_text_vpos(self, ax, offset, scale_to_width=False):
        bbox = ax.get_window_extent()
        w, h = bbox.width, bbox.height
        if scale_to_width:
            yoffset = offset*w/h
        else:
            yoffset = offset/h
            
        return yoffset


    def _addtext_file_id(self, ax, fontsize=6):
        ypos_offset = self.__scale_text_vpos(ax, offset=1.3)        
        ypos = 1 + ypos_offset
        #print('Adding file_id at relative height: {}'.format(ypos))
        self.txt_fileid = ax.text(1.0, ypos, '%s'%(os.path.basename(self.spec.mdata.data('datFile'))),
                                  transform = ax.transAxes, fontsize=fontsize, horizontalalignment='right',
                                  verticalalignment='bottom')  

        
    def _addtext_statusmarker(self, ax, xdata_key, ydata_key, text_pos='left', fontsize=6):
        xpos = {'left': 0.0,
                'center': 0.5,
                'right': 1.0}
        ypos_offset = self.__scale_text_vpos(ax, offset=1.3) 
        ypos = 1 + ypos_offset
        stats = []
        if 'waveLength' in self.spec.mdata.data().keys():
            human_wl = '{} nm'.format(round(self.spec.mdata.data('waveLength')*1e9))
            stats.append(human_wl)
        if 'Gauged' not in xdata_key and self.spec.mdata.data('specType') not in ['generic']:
            stats.append('not gauged')
        if 'Sub' in ydata_key:
            stats.append('subtracted')
        if 'background' in self.spec.mdata.data('systemTags'):
            stats.append('background')
        if len(stats) > 0:
            stat_text = ', '.join(stats)
            #print(self.spec.mdata.data('datFile'), 'Adding status marker(s): ', stat_text)
            self.txt_statusmarker = ax.text(xpos[text_pos], ypos, stat_text, transform = ax.transAxes,
                                            fontsize=fontsize, horizontalalignment=text_pos,
                                            verticalalignment='bottom')
    
    
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
        if 'clusterDopant' in self.spec.mdata.data().keys():
            partDopant = '{%s}'%self.spec.mdata.data('clusterDopant')
            partDopantNumber = '_{%s}'%(str(self.spec.mdata.data('clusterDopantNumber')))
        
        cluster_id_str = formatStart + partCluster
        if not ms:
            if self.spec.mdata.data('clusterBaseUnitNumber') > 1:
                cluster_id_str += partClusterNumber
        if 'clusterDopant' in self.spec.mdata.data().keys():
            cluster_id_str += partDopant
            if self.spec.mdata.data('clusterDopantNumber') > 1:
                cluster_id_str += partDopantNumber
        cluster_id_str += partCharge
        cluster_id_str += formatEnd
        return cluster_id_str
                
    
    def _addtext_cluster_id(self, ax, cluster_id, text_pos='left', fontsize=28, color='black', voffset=0):
#         fig = ax.get_figure()
#         w, h = fig.get_size_inches()
#         bbox = ax.get_window_extent()
#         w, h = bbox.width, bbox.height
#         print('Got size: {}, {}'.format(w,h))
        ypos_offset = self.__scale_text_vpos(ax, offset=0.05, scale_to_width=True)
        if text_pos == 'left':
            pos_x, pos_y = 0.05, 1 - ypos_offset #+ voffset
        elif text_pos == 'right':
            pos_x, pos_y = 0.95, 1 - ypos_offset #+ voffset
        else:
            raise ValueError('text_pos must be one of: left, right. Got "%s" instead.'%(str(text_pos)))
        #print('Placing at: {}, {}'.format(pos_x,pos_y))
        id_str = cluster_id
        if voffset < 0:
            id_str = '\n'*abs(voffset) + id_str
        elif voffset > 0:
            id_str = id_str + '\n'*voffset
        self.txt_clusterid = ax.text(pos_x, pos_y, id_str, transform = ax.transAxes, fontsize=fontsize,
                                     horizontalalignment=text_pos, verticalalignment='top', color=color)
        
        
    def _addtext_info(self, ax, info_text, text_pos='left', text_vpos='center', fontsize=12):
        txt_pos = {'left': 0.05, 'right': 0.95,
                   'top': 0.9, 'center': 0.6, 'bottom': 0.1}
             
        ax.text(txt_pos[text_pos], txt_pos[text_vpos], info_text, transform = ax.transAxes, fontsize=fontsize,
                horizontalalignment=text_pos, verticalalignment=text_vpos)        


    def _pretty_print_info(self, mdata_key):
        if mdata_key in self.spec.mdata.data().keys():
            if mdata_key == 'trapTemp':
                if self.spec.mdata.data(mdata_key) is not None:
                    info_str = 'T$_{trap}$: ' + '{:.0f} K'.format(self.spec.mdata.data(mdata_key))
                else:
                    info_str = 'T$_{trap}$: not set'
            elif 'tags' in mdata_key:
                info_str = '\n'.join(self.spec.mdata.data('userTags'))
            else:
                info_str = str(self.spec.mdata.data(mdata_key))
        else:
            info_str = ''
        
        return info_str
    
    
    def _set_xlabel_time(self, ax, label, time_unit, fontsize):
        if time_unit not in [1, 1e-3, 1e-6, 1e-9]:
            raise ValueError('time_unit must be one of: 1, 1e-3, 1e-6, 1e-9.')
        prefix_map = ['', 'm', '\mu ', 'n']
        prefix = prefix_map[int(abs(np.log10(time_unit)/3))]
        ax.set_xlabel(r'{0} (${1}s$)'.format(label, prefix), fontsize=fontsize)
        

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
        
    
    def _set_xlimit(self, ax, xlim, xlim_auto, n_xticks=None):
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
        if n_xticks:
            #xticks = ax.get_xticks()
            ax.xaxis.set_major_locator(ticker.MaxNLocator(n_xticks))
        else:
            ax.xaxis.set_major_locator(ticker.AutoLocator())
        return x_lim
        
        
    def _set_ylimit(self, ax):
        ax.relim()  
        ax.autoscale(axis='y')
        
    def _yminmax_in_xrange(self, xdata, ydata, xlim_scale):
        xlb = np.argmin(abs(xdata-xlim_scale[0]))
        xub = np.argmin(abs(xdata-xlim_scale[1]))
        ydata_sorted = np.sort(ydata[xlb:xub])
        # exclude infinite values
        if len(ydata_sorted) > 0:
            ymin = ydata_sorted[np.isfinite(ydata_sorted)][0]
            ymax = ydata_sorted[np.isfinite(ydata_sorted)][-1]
        else: # no data in selected xrange, so we scale to -1, 1, to prevent index errors.
            ymin, ymax = -1, 1
        return ymin, ymax
               
    
    def _auto_ylim(self, ax, xdata, ydata, xlim_scale, lower_padding=0.04, upper_padding=0.3):
        'TODO: Is scaling of ymin always wanted?'
        self.xlim_scale = xlim_scale
        ymin, self.ymax = self._yminmax_in_xrange(xdata, ydata, xlim_scale)
        dy = abs(self.ymax - ymin)
        ax.set_ylim([ymin - lower_padding*dy, self.ymax + upper_padding*dy])

     
        

    def plot_idx(self, ax, xdata_key, ydata_key, xlim, xlim_scale=None, n_xticks=None,
                 color='black'):
        self.xdata_key = xdata_key
        self.ydata_key = ydata_key
        # plot 
        ax.plot(self.spec.xdata[xdata_key], self.spec.ydata[ydata_key], color=color)
        # set axes limits
        xlim_auto = [self.spec.xdata[xdata_key][0], self.spec.xdata[xdata_key][-1]]
        xlim_plot = self._set_xlimit(ax, xlim, xlim_auto, n_xticks=n_xticks)
#         print(xlim_plot)
        if xlim_scale is None:
            self._auto_ylim(ax, self.spec.xdata[xdata_key], self.spec.ydata[ydata_key],
                            xlim_plot)
        else:
            self._auto_ylim(ax, self.spec.xdata[xdata_key], self.spec.ydata[ydata_key],
                            xlim_scale)
              
        
    def plot_time(self, ax, xdata_key, ydata_key, time_unit, xlim, xlim_scale=None,
                 n_xticks=None, color='black', smooth=False):
        self.xdata_key = xdata_key
        self.ydata_key = ydata_key
        self.timeunit = time_unit
        #self.xlim_scale = xlim_scale
        if smooth:
            ydata = moving_avg_gaussian(self.spec.ydata[ydata_key])
        else:
            ydata = self.spec.ydata[ydata_key]
        # plot      
        ax.plot(self.spec.xdata[xdata_key]/time_unit, ydata, color=color)
        #set axes limits
        xlim_auto = [self.spec.xdata[xdata_key][0]/time_unit, self.spec.xdata[xdata_key][-1]/time_unit] 
        xlim_plot = self._set_xlimit(ax, xlim, xlim_auto, n_xticks=n_xticks)
        if xlim_scale is None:
            self._auto_ylim(ax, self.spec.xdata[xdata_key]/time_unit, ydata, xlim_plot)
        else:
            self._auto_ylim(ax, self.spec.xdata[xdata_key]/time_unit, ydata, xlim_scale)
            
            
    def show_idx(self, ydata_key='auto', xlim=['auto', 'auto'], xlim_scale=None, n_xticks=None,
                 show_mdata=False, show_ytics=False, fontsize_label=12, fontsize_ref=6,
                 export=False, show_xlabel=True, show_ylabel=True, size=None,
                 key_deps={'idx': ['rawVoltageSpec', 'rawVoltageRamp', 'rawVoltagePulse']}):
        self._single_fig_output(size=size)
        # set data keys
        xdata_key, ydata_key = self._auto_key_selection(xdata_key='idx', ydata_key=ydata_key, key_deps=key_deps)        
        self.plot_idx(self.ax, xdata_key=xdata_key, ydata_key=ydata_key, xlim=xlim,
                      xlim_scale=xlim_scale, n_xticks=n_xticks)
        if show_xlabel:
            self.ax.set_xlabel('Index', fontsize=fontsize_label)
        if show_ylabel:
            self.ax.set_ylabel('Intensity (a.u.)', fontsize=fontsize_label)
        self.ax.tick_params(labelsize=fontsize_label)      
        self._addtext_file_id(self.ax, fontsize=fontsize_ref)
        self._addtext_statusmarker(self.ax, xdata_key=xdata_key, ydata_key=ydata_key, fontsize=fontsize_ref)
        if show_mdata:
            self._addtext_info(self.ax, self._pretty_print_info(show_mdata), text_pos='right',
                               fontsize=fontsize_label)
        if show_ytics:
            self.ax.yaxis.set_major_locator(plt.AutoLocator())
        else:
            self.ax.yaxis.set_major_locator(plt.NullLocator())
        self.ax.xaxis.grid(linewidth=.1, linestyle=':', color='black')
        if not export:          
            self.fig.canvas.draw()


    def show_time(self, xdata_key='auto', ydata_key='auto', time_label='Time',
                  time_unit=1e-6, xlim=['auto', 'auto'], xlim_scale=None, n_xticks=None, show_mdata=False,
                  show_ytics=False, fontsize_label=12, fontsize_ref=6, export=False, show_xlabel=True,
                  show_ylabel=True, size=None, smooth=True,
                  key_deps={'time': ['rawVoltageSpec', 'rawVoltageRamp', 'rawVoltagePulse'],}):     
        self._single_fig_output(size=size)
        # set data keys
        xdata_key, ydata_key = self._auto_key_selection(xdata_key=xdata_key, ydata_key=ydata_key,
                                                        key_deps=key_deps)      
        self.plot_time(self.ax, xdata_key=xdata_key, ydata_key=ydata_key, time_unit=time_unit,
                       xlim=xlim, xlim_scale=xlim_scale, n_xticks=n_xticks, smooth=smooth)
        if show_xlabel:
            self._set_xlabel_time(self.ax, label=time_label, time_unit=time_unit, fontsize=fontsize_label)
        if show_ylabel:
            self.ax.set_ylabel('Intensity (a.u.)', fontsize=fontsize_label)
        self.ax.tick_params(labelsize=fontsize_label)
        self._addtext_file_id(self.ax, fontsize=fontsize_ref)
        self._addtext_statusmarker(self.ax, xdata_key=xdata_key, ydata_key=ydata_key,
                                   fontsize=fontsize_ref)
        if show_mdata:
            self._addtext_info(self.ax, self._pretty_print_info(show_mdata), text_pos='right',
                               text_vpos='top', fontsize=fontsize_label)
        if show_ytics:
            self.ax.yaxis.set_major_locator(plt.AutoLocator())
        else:
            self.ax.yaxis.set_major_locator(plt.NullLocator())
        self.ax.xaxis.grid(linewidth=.1, linestyle=':', color='black')
        if not export:          
            self.fig.canvas.draw()
        
        
    def add_plot(self, ax, xdata, ydata, color='blue', linestyle='-', linewidth=.5, file_id=None, unit_scale=1,
                 rescale=True, batch_mode=False, smooth=False):
        if file_id is not None:
            self.txt_fileid.set_text('{}, {}'.format(os.path.basename(self.spec.mdata.data('datFile')), file_id))
        if smooth:
            ydata = moving_avg_gaussian(ydata)
        if rescale:
            if self._yminmax_in_xrange(xdata, ydata, np.array(self.xlim_scale)*unit_scale)[1] > self.ymax:
                self._auto_ylim(ax, xdata, ydata, np.array(self.xlim_scale)*unit_scale)
        
        added_line = ax.plot(xdata/unit_scale, ydata, color=color, linestyle=linestyle, linewidth=linewidth)[0]
        if linestyle in ['--', ':']:
            added_line.set_dashes((1,1))
        if not batch_mode:
            self.fig.canvas.draw()
        
        
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


    def export(self, fname='export.pdf', export_dir='~/test', size=[20,14], overwrite=False,
               linewidth=.8):
        'validate export dir'
        'TODO: put this in helper library for reuse.'
        if export_dir.startswith('~'):
            export_dir = os.path.expanduser(export_dir)
        os.makedirs(export_dir, exist_ok=overwrite)
        f = os.path.join(export_dir, fname)
        'TODO: presets are mere personal. For a general approach probably not suitable.'
        presets = {'p1': [14, 14*3/7],
                   'p2': [7, 7*5/7],
                   'p3': [4.8, 4.8*5/6]}
        if isinstance(size, str) and size in presets.keys():
            size = presets[size]
        w = size[0]/2.54
        h = size[1]/2.54
        #orig_size = self.fig.get_size_inches()
#         if figure is None:
#             figure = self.fig
        self.fig.set_size_inches(w,h)
        'TODO: some of these margins are font size related, so they need to be adapted accordingly'
        t = 0.2/size[1]
        r = 0.3/size[0]
        if self.ax.get_xlabel():
            b = 0.9/size[1] # 0.9 fits for font size 8
        else:
            b = 0.4/size[1]
        if self.ax.get_ylabel():
            l = 0.4/size[0] # 0.4 dito
        else:
            l = 0.15/size[0]
            r = 0.15/size[0]
        self.fig.subplots_adjust(left=l, bottom=b, right=1-r, top=1-t)

        self.ax.yaxis.labelpad = 3
        if isinstance(linewidth, (int, float)):
            for l in self.ax.lines:
                l.set_linewidth(linewidth)
        else:
            raise ValueError('"linewidth" must be an integer or a float.')
        'adapt voffset for text'
        '''TODO: don't use hard coded positions and offsets. This is really hard to maintain.'''
        if hasattr(self, 'txt_clusterid'):
            (x,y) = self.txt_clusterid.get_position()
            ypos_offset = self.__scale_text_vpos(self.ax, offset=0.05, scale_to_width=True)
            y = 1 - ypos_offset
            self.txt_clusterid.set_position((x,y))
            
        if hasattr(self, 'txt_fileid'):
            (x,y) = self.txt_fileid.get_position()
            ypos_offset = self.__scale_text_vpos(self.ax, offset=1.3)        
            y = 1 + ypos_offset
            self.txt_fileid.set_position((x,y))
            
        if hasattr(self, 'txt_statusmarker'):
            (x,y) = self.txt_statusmarker.get_position()
            ypos_offset = self.__scale_text_vpos(self.ax, offset=1.3)        
            y = 1 + ypos_offset
            self.txt_statusmarker.set_position((x,y))
            
        #self.txt_clusterid.set_y(1 - 0.05*size[0]/size[1])
        #'TODO: Set up margins so we dont have to use bbox_inches'
        #self.fig.canvas.draw()
        self.fig.savefig(f) #, bbox_inches='tight', pad_inches=0.01)
        #self.fig.set_size_inches(orig_size)
        
        
class ViewTof(View):
    def __init__(self, spec):
        View.__init__(self, spec)
        

    def show_idx(self, ydata_key='auto', xlim=['auto', 'auto'], xlim_scale=None, n_xticks=None,
                 show_mdata=False, show_ytics=True, fontsize_clusterid=28, fontsize_label=12,
                 fontsize_ref=6, export=False, show_xlabel=True, show_ylabel=True, size=None,
                  show_pulse=True):
        key_deps={'idx': ['rawVoltageSpec', 'rawVoltagePulse'],}
        View.show_idx(self, ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale, n_xticks=n_xticks,
                      show_mdata=show_mdata, show_ytics=show_ytics, fontsize_label=fontsize_label,
                      fontsize_ref=fontsize_ref, export=export, show_xlabel=show_xlabel,
                      show_ylabel=show_ylabel, size=size,key_deps=key_deps)
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid(ms=True), text_pos='right',
                                 fontsize=fontsize_clusterid)
        if show_pulse:
            self.add_plot(self.ax, self.spec.xdata[self.xdata_key], self.spec.ydata['rawVoltagePulse'])
        if not export:          
            self.fig.canvas.draw()

        
    def show_time(self, xdata_key='auto', ydata_key='auto', time_label='Time',
                  time_unit=1e-3, xlim=[0, 'auto'], xlim_scale=None, n_xticks=None,
                  show_mdata=False, show_ytics=True, fontsize_clusterid=28, fontsize_label=12,
                  fontsize_ref=6, export=False, show_xlabel=True, show_ylabel=True, size=None,
                  show_pulse=True, smooth=True):
        key_deps={'time': ['rawVoltageSpec', 'rawVoltagePulse'],}
        View.show_time(self, xdata_key=xdata_key, ydata_key=ydata_key, time_label=time_label, 
                       time_unit=time_unit, xlim=xlim, xlim_scale=xlim_scale, n_xticks=n_xticks,
                       show_mdata=show_mdata, show_ytics=show_ytics, fontsize_label=fontsize_label,
                       fontsize_ref=fontsize_ref, export=export, show_xlabel=show_xlabel,
                       show_ylabel=show_ylabel, size=size, key_deps=key_deps, smooth=smooth)
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid(ms=True), text_pos='right',
                                 fontsize=fontsize_clusterid)    
        if show_pulse:
            self.add_plot(self.ax, self.spec.xdata[self.xdata_key], self.spec.ydata['rawVoltagePulse'],
                          unit_scale=self.timeunit)
        if not export:          
            self.fig.canvas.draw()
            
       
#     def show_gaugeref(self):
#         gaugeRef = self.spec.mdata.data('gaugeRef')
#         gaugeSpec = load.load_pickle_3f(self.spec.cfg, gaugeRef)
#         gaugeSpec.view.show_ebin_fit()
        
        
    def _add_spec(self, specfile, xscale=1, yscale=1, yscale_type=None, xoffset=0, yoffset=0,
                  color='blue', linestyle='-' , linewidth=.5, fontsize_clusterid=28, ax=None):
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
        #addspec = load.load_pickle_3f(self.spec.cfg, specfile)
        addspec = load_3f.spec_from_specdatadir(self.spec.cfg, specfile)
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
            #print('New scale factor:', yscale)    
        
        ydata = addspec.ydata[self.ydata_key]*yscale + yoffset
        if self.txt_clusterid.get_position()[0] == 0.05:
            text_pos = 'left'
        else:
            text_pos = 'right'
        self._addtext_cluster_id(ax, addspec.view._pretty_format_clusterid(), text_pos=text_pos, 
                                 fontsize=fontsize_clusterid, color=color, voffset=-1)
        #cluster_ids = '{}\n{}'.format(self._pretty_format_clusterid(), addspec.view._pretty_format_clusterid())
        #self.txt_clusterid.set_text(cluster_ids)
        self.add_plot(ax, xdata, ydata, color=color, linestyle=linestyle, linewidth=linewidth,
                      file_id=os.path.basename(addspec.mdata.data('datFile')))
        
        
    def add_spec(self, specfile, xscale=1, yscale=1, yscale_type=None, xoffset=0, yoffset=0, color='blue',
                 linestyle='-' , linewidth=.5, fontsize_clusterid=28, ax=None):
        self._add_spec(specfile, xscale=xscale, yscale=yscale, yscale_type=yscale_type, xoffset=xoffset,
                       yoffset=yoffset, color=color, linestyle=linestyle, linewidth=linewidth,
                       fontsize_clusterid=fontsize_clusterid, ax=ax)
        self.fig.canvas.draw()
        
        


    def add_che_spec(self, point, shifted_point, yscale, linewidth=1.5):
        '''Shortcut for shifting the same spectrum by the difference of point_shifted - point.
        Method to determin charging energy by manual shift'''
        xoffset = shifted_point[0] - point[0]
        yoffset = shifted_point[1] - point[1]
        self.add_spec(self.spec.mdata.data('dataStorageLocation'), linewidth=linewidth,
                      xoffset=xoffset, yoffset=yoffset, yscale=yscale)

       
        

       
        
class ViewMs(View):
    def __init__(self, spec):
        View.__init__(self, spec)   
        
        
    def _xlabel_str(self, mass_key, mass_unit=None):
        diam_mass_unit_map = {1: 'm',
                              1e-3: 'mm',
                              1e-6: 'um',
                              1e-9: 'nm',
                              1e-10: 'angstrom'}
        if mass_key == 'cluster':
            # TODO: better a generic str parser and formatter
            id_str = self._pretty_format_clusterid(ms=True)
            ref_str = self.spec.mdata.data('clusterBaseUnit')
            id_str = id_str[id_str.index(ref_str[0]):id_str.index(ref_str[-1])+1]
            if '_' in id_str:
                id_str = '$\mathrm{\mathsf{' + id_str + '}}$'
            xlabel = 'Cluster Size (number of {})'.format(id_str)
        elif mass_key == 's_u':
            xlabel = 'Cluster Mass (simplified u)'
        elif mass_key == 'u':
            xlabel = 'Cluster Mass (u)'
        else:
            xlabel = 'Cluster Diameter ({})'.format(diam_mass_unit_map[mass_unit])
            
        return xlabel        

    
    def plot_ms(self, ax, mass_key, mass_unit, xlim, xlim_scale=None, n_xticks=None, color='black',
                spec_key='voltageSpec', smooth=False):
        if smooth:
            ydata = moving_avg_gaussian(self.spec.ydata[spec_key])
        else:
            ydata = self.spec.ydata[spec_key]
        ax.plot(self.spec.xdata[mass_key]/mass_unit, ydata, color=color)
        # set axes limits
        xlim_auto = [self.spec.xdata[mass_key][0]/mass_unit, self.spec.xdata[mass_key][-1]/mass_unit]
        xlim_plot = self._set_xlimit(ax, xlim, xlim_auto, n_xticks=n_xticks)
        if xlim_scale is None:
            self._auto_ylim(ax, self.spec.xdata[mass_key]/mass_unit, ydata, xlim_plot)
        else:
            self._auto_ylim(ax, self.spec.xdata[mass_key]/mass_unit, ydata, xlim_scale)
#         ax.relim()
#         ax.autoscale()
     
     
    def show_idx(self, ydata_key='auto', xlim=['auto', 'auto'], xlim_scale=None, n_xticks=None,
                 show_mdata=False, show_ytics=True, fontsize_clusterid=28, fontsize_label=12,
                 fontsize_ref=6, export=False, show_xlabel=True, show_ylabel=True, size=None,
                 show_ramp=True):
        key_deps = {'idx': ['voltageSpec', 'rawVoltageSpec', 'rawVoltageRamp', 'rawVoltagePulse'],}
        View.show_idx(self, ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale, n_xticks=n_xticks,
                      show_mdata=show_mdata, show_ytics=show_ytics, fontsize_label=fontsize_label,
                      fontsize_ref=fontsize_ref, export=export, show_xlabel=show_xlabel,
                      show_ylabel=show_ylabel, size=size, key_deps=key_deps)
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid(ms=True), text_pos='right',
                                 fontsize=fontsize_clusterid)
        if show_ramp:
            self.add_plot(self.ax, self.spec.xdata[self.xdata_key], self.spec.ydata['rawVoltageRamp'])
        if not export:          
            self.fig.canvas.draw()
            
        
    def show_time(self, xdata_key='auto', ydata_key='auto', time_label='Time',
                 time_unit=1e-3, xlim=[0, 'auto'], xlim_scale=None, n_xticks=None,
                 show_mdata=False, show_ytics=True, fontsize_clusterid=28, fontsize_label=12,
                 fontsize_ref=6, export=False, show_xlabel=True, show_ylabel=True, size=None,
                 show_ramp=True, smooth=True):
        key_deps = {'time': ['voltageSpec', 'rawVoltageSpec', 'rawVoltageRamp', 'rawVoltagePulse'],}
        View.show_time(self, xdata_key=xdata_key, ydata_key=ydata_key, time_label=time_label, 
                      time_unit=time_unit, xlim=xlim, xlim_scale=xlim_scale, n_xticks=n_xticks,
                      show_mdata=show_mdata, show_ytics=show_ytics, fontsize_label=fontsize_label,
                      fontsize_ref=fontsize_ref, export=export, show_xlabel=show_xlabel,
                      show_ylabel=show_ylabel, size=size, key_deps=key_deps, smooth=smooth)
        self._addtext_cluster_id(self.ax, self._pretty_format_clusterid(ms=True), text_pos='right',
                                 fontsize=fontsize_clusterid)        
        if show_ramp:
            self.add_plot(self.ax, self.spec.xdata[self.xdata_key], self.spec.ydata['rawVoltageRamp'],
                          unit_scale=self.timeunit)
        if not export:          
            self.fig.canvas.draw()
    
    
    def plot_ramp(self, ax, xdata_key, ydata_key, xlim, xlim_scale=None,
                 n_xticks=None, color='black', smooth=True):
        self.xdata_key = xdata_key
        self.ydata_key = ydata_key
        #self.timeunit = time_unit
        #self.xlim_scale = xlim_scale
        if smooth:
            ydata = moving_avg_gaussian(self.spec.ydata[ydata_key])
        else:
            ydata = self.spec.ydata[ydata_key]
        # plot      
        ax.plot(self.spec.ydata[xdata_key], ydata, color=color)
        #set axes limits
        xlim_auto = [self.spec.ydata[xdata_key][0], self.spec.ydata[xdata_key][-1]] 
        xlim_plot = self._set_xlimit(ax, xlim, xlim_auto, n_xticks=n_xticks)
        if xlim_scale is None:
            self._auto_ylim(ax, self.spec.ydata[xdata_key], ydata, xlim_plot)
        else:
            self._auto_ylim(ax, self.spec.ydata[xdata_key], ydata, xlim_scale)
            
    
    def show_ramp(self, ramp_data_key='voltageRampFitted', ydata_key='auto', xlim=['auto', 'auto'],
                  xlim_scale=None, n_xticks=None, show_mdata=False, show_ytics=True, fontsize_clusterid=28,
                  fontsize_label=12, fontsize_ref=6, export=False, show_xlabel=True, show_ylabel=True,
                  size=None, smooth=True):
        self._single_fig_output(size=size)
        # set data keys
        xdata_key, ydata_key = ramp_data_key, 'voltageSpec' #self._auto_key_selection(xdata_key='idx', ydata_key=ydata_key, key_deps=key_deps)        
        self.plot_ramp(self.ax, xdata_key=xdata_key, ydata_key=ydata_key, xlim=xlim,
                       xlim_scale=xlim_scale, n_xticks=n_xticks, smooth=smooth)
        if show_xlabel:
            self.ax.set_xlabel('Ramp Voltage (V)', fontsize=fontsize_label)
        if show_ylabel:
            self.ax.set_ylabel('Intensity (a.u.)', fontsize=fontsize_label)
        self.ax.tick_params(labelsize=fontsize_label)      
        self._addtext_file_id(self.ax, fontsize=fontsize_ref)
        self._addtext_statusmarker(self.ax, xdata_key=xdata_key, ydata_key=ydata_key, fontsize=fontsize_ref)
        if fontsize_clusterid:
            self._addtext_cluster_id(self.ax, self._pretty_format_clusterid(ms=True), text_pos='right',
                                     fontsize=fontsize_clusterid)
        if show_mdata:
            self._addtext_info(self.ax, self._pretty_print_info(show_mdata), text_pos='right',
                               fontsize=fontsize_label)
        if show_ytics:
            self.ax.yaxis.set_major_locator(plt.AutoLocator())
        else:
            self.ax.yaxis.set_major_locator(plt.NullLocator())
        self.ax.xaxis.grid(linewidth=.1, linestyle=':', color='black')
        if not export:          
            self.fig.canvas.draw()
                
        
    def show_ms(self, mass_key='diam', mass_unit=None, xlim=['auto', 'auto'], xlim_scale=None, n_xticks=None,
                color='black', show_ytics=True, fontsize_clusterid=28, fontsize_label=12,
                fontsize_ref=6, export=False, show_mdata=None, size=None, smooth=True):
        self._single_fig_output(size=size)
        if not mass_unit:
            if mass_key=='diam':
                mass_unit = 1e-9
            else:
                mass_unit = 1
        self.plot_ms(ax=self.ax, mass_key=mass_key, mass_unit=mass_unit, xlim=xlim, xlim_scale=xlim_scale,
                     n_xticks=n_xticks, color=color, smooth=smooth)
        self.ax.set_xlabel(self._xlabel_str(mass_key, mass_unit=mass_unit), fontsize=fontsize_label)
        self.ax.set_ylabel('Intensity (a.u.)', fontsize=fontsize_label)
        self.ax.tick_params(labelsize=fontsize_label)
        self._addtext_file_id(self.ax, fontsize=fontsize_ref)
        if fontsize_clusterid:
            self._addtext_cluster_id(self.ax, self._pretty_format_clusterid(ms=True),
                                     fontsize=fontsize_clusterid)
        if show_mdata:
            self._addtext_info(self.ax, self._pretty_print_info(show_mdata), fontsize=fontsize_label,
                               text_pos='right', text_vpos='top')
        if show_ytics:
            self.ax.yaxis.set_major_locator(plt.AutoLocator())
        else:
            self.ax.yaxis.set_major_locator(plt.NullLocator())
        self.ax.xaxis.grid(linewidth=.1, linestyle=':', color='black')
        if not export:          
            self.fig.canvas.draw()
        
        
        
