import matplotlib as mpl
import matplotlib.backends.backend_pdf as Pdf
import matplotlib.pyplot as plt
import scipy.constants as constants
import load
import os
import numpy as np




class ViewList(object):
    def __init__(self, speclist):
        self.speclist = speclist

    # auxiliary methods
    def _build_idx_list(self, layout):
        'Returns a list of subplot indices for a given layout [rows, columns].'
        rows = layout[0]
        col = layout[1]
        return np.arange(1,rows*col+1).reshape(rows,col).transpose().reshape(rows*col)
    
    def _format_overview_plot(self, ax):
          
        for tick in ax.xaxis.get_major_ticks():
            tick.tick2On=True
            tick.gridOn=True
            tick.label1On=True
            tick.label2On=False
            tick.tick1On=True
        for label in ax.xaxis.get_ticklabels():
            label.set_fontsize(7)
        ax.yaxis.set_major_locator(mpl.ticker.NullLocator())
        ax.legend_=None
        ax.lines[0].set_linewidth(.3)
        ax.grid(linewidth=.1, linestyle=':', color='black')
        
    def _show(self, show_fct, layout=[5,4], pdf=False, **keywords):
        if pdf:
            fname = os.path.join(os.path.expanduser('~'), 'export.pdf')
            pdf_file = Pdf.PdfPages(fname)        
        print('keywords:', keywords)
        subplt_idx = self._build_idx_list(layout)
        total_plots = len(self.speclist.pfile_list)
        plotcount = 0
        figidx = 1
        while plotcount < total_plots:
            # create page
            print('Plotting page', figidx)
            fig = plt.figure(figidx, figsize=(0.21/constants.inch, 0.297/constants.inch))
            plt.subplots_adjust(left  = 0.03, right = 0.97, bottom = 0.03, top = 0.97,
                                wspace = 0.1, hspace = 0.14)
            plotidx = 0
            while plotidx < layout[0]*layout[1] and plotcount < total_plots:
                #print('Creating plot', plotidx)
                cs = self.speclist.get_spec(plotcount)
                ax = fig.add_subplot(layout[0], layout[1], subplt_idx[plotidx])
                show_fct(cs, ax, **keywords)
                self._format_overview_plot(ax)
                del cs
                plotidx += 1
                plotcount += 1
            if pdf:
                fig.savefig(pdf_file, dpi=None, facecolor='w', edgecolor='w',
                            orientation='portrait', papertype='a4', format='pdf')
            figidx += 1
        if pdf:    
            pdf_file.close()
               
    def _show_idx(self, spec, axes, ydata_key='auto', xlim=['auto', 'auto'], xlim_scale=None):
        key_deps = {'idx': ['intensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw']}
        x_key, y_key = spec._auto_key_selection(xdata_key='idx', ydata_key=ydata_key, key_deps=key_deps) 
        spec.view.plot_idx(axes, x_key, y_key, xlim, xlim_scale=None, color='black')
        spec.view._addtext_file_id(axes) 
        
    def _show_tof(self, spec, axes, xdata_key='auto', ydata_key='auto', time_unit=1e-6,
                  xlim=['auto', 'auto'], xlim_scale=None):
        key_deps = {'tof': ['intensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw'],
                    'tofGauged': ['intensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw']} 
        xdata_key, ydata_key = spec._auto_key_selection(xdata_key=xdata_key, ydata_key=ydata_key, key_deps=key_deps)      
        spec.view.plot_tof(axes, xdata_key=xdata_key, ydata_key=ydata_key,
                      time_unit=time_unit, xlim=xlim, xlim_scale=xlim_scale)
        spec.view._addtext_file_id(axes)
        spec.view._addtext_statusmarker(axes, xdata_key=xdata_key, ydata_key=ydata_key, text_pos='left')          
    
    
    def show_idx(self, layout=[5,4], ydata_key='auto', xlim=['auto', 'auto'], xlim_scale=None, pdf=False):
        self._show(self._show_idx, layout=layout, pdf=pdf, ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale)

    def show_tof(self, layout=[5,4], xdata_key='auto', ydata_key='auto', time_unit=1e-6,
                 xlim=['auto', 'auto'], xlim_scale=None, pdf=False):
        self._show(self._show_tof, layout=layout, pdf=pdf, xdata_key=xdata_key, ydata_key=ydata_key,
                   time_unit=time_unit, xlim=xlim, xlim_scale=xlim_scale)



class ViewPesList(ViewList):
    def __init__(self, speclist):
        self.speclist = speclist


    def _show_idx(self, spec, ax, ydata_key='auto', xlim=['auto', 'auto'], xlim_scale=None):
        ViewList._show_idx(self, spec, ax, ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(), fontsize=10)
        spec.view._addtext_statusmarker(ax, xdata_key='idx', ydata_key=ydata_key, text_pos='left')
        
    def _show_tof(self, spec, ax, xdata_key='auto', ydata_key='auto', time_unit=1e-6,
                  xlim=['auto', 'auto'], xlim_scale=None):
        ViewList._show_tof(self, spec, ax, xdata_key=xdata_key, ydata_key=ydata_key,
                   time_unit=time_unit, xlim=xlim, xlim_scale=xlim_scale)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(), fontsize=10)
        spec.view._addtext_statusmarker(ax, xdata_key=xdata_key, ydata_key=ydata_key, text_pos='left')          
        
    def _show_ekin(self, spec, ax, xdata_key='auto', ydata_key='auto', xlim=['auto', 'auto'], xlim_scale=None):
        key_deps = {'ekin': ['jIntensity', 'jIntensitySub'],
                    'ekinGauged': ['jIntensityGauged', 'jIntensityGaugedSub']} 
        xdata_key, ydata_key = spec._auto_key_selection(xdata_key=xdata_key, ydata_key=ydata_key, key_deps=key_deps)        
        spec.view.plot_ekin(ax, xdata_key=xdata_key, ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale)
        spec.view._addtext_file_id(ax)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(), text_pos='right', fontsize=10)
        spec.view._addtext_statusmarker(ax, xdata_key=xdata_key, ydata_key=ydata_key, text_pos='left') 
        
    def _show_ebin(self, spec, ax, xdata_key='auto', ydata_key='auto', xlim=['auto', 'auto'], xlim_scale=None):
        key_deps = {'ebin': ['jIntensity', 'jIntensitySub'],
                    'ebinGauged': ['jIntensityGauged', 'jIntensityGaugedSub']} 
        xdata_key, ydata_key = spec._auto_key_selection(xdata_key=xdata_key, ydata_key=ydata_key, key_deps=key_deps)         
        spec.view.plot_ebin(ax, xdata_key=xdata_key, ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale)     
        spec.view._addtext_file_id(ax)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(), fontsize=10)
        spec.view._addtext_statusmarker(ax, xdata_key=xdata_key, ydata_key=ydata_key, text_pos='left')
        
              
        
    def show_ekin(self, layout=[5,4], xdata_key='auto', ydata_key='auto',
                  xlim=['auto', 'auto'], xlim_scale=None, pdf=False):
        self._show(self._show_ekin, layout=layout, pdf=pdf, xdata_key=xdata_key,
                   ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale)
        
    def show_ebin(self, layout=[5,4], xdata_key='auto', ydata_key='auto',
                  xlim=['auto', 'auto'], xlim_scale=None, pdf=False):
        self._show(self._show_ebin, layout=layout, pdf=pdf, xdata_key=xdata_key,
                   ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale)        
        
        



class ViewPtFitList(ViewPesList):
    def __init__(self, speclist):
        self.speclist = speclist


    def _show_tof_fit(self, spec, ax, fit_par='fitPar', time_unit=1e-6, xlim=['auto', 'auto'], xlim_scale=None):
        xdata_key = 'tof'
        ydata_key = spec.mdata.data('fitYdataKey')
        self._show_tof(spec, ax, xdata_key, ydata_key, time_unit, xlim, xlim_scale)
        spec.view.plot_tof_fit(ax, fit_par=fit_par, time_unit=time_unit)
        spec.view._addtext_gauge_par(ax, fit_par=fit_par, text_pos='right', fontsize=6)
        
    def _show_energy_fit(self, spec, ax, xdata_key, fit_par, xlim, xlim_scale):
        'TODO: use method from View instead (after minimal modification).'
        plot_method = {'ekin': spec.view.plot_ekin, 'ebin': spec.view.plot_ebin}
        if xdata_key not in ['ekin', 'ebin']:
            raise ValueError("xdata_key must be one of: 'ekin', 'ebin'")
        if 'Sub' in spec.mdata.data('fitYdataKey'):
            ydata_key = 'jIntensitySub'
        else:
            ydata_key = 'jIntensity'        
        plot_method[xdata_key](ax, xdata_key=xdata_key, ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale)
        spec.view.plot_energy_fit(ax, fit_par=fit_par, xdata_key=xdata_key)      
        spec.view._addtext_file_id(ax)
        spec.view._addtext_statusmarker(ax, xdata_key=xdata_key, ydata_key=ydata_key, text_pos='left')
        
    def _show_ekin_fit(self, spec, ax, fit_par='fitPar', xlim=['auto', 'auto'], xlim_scale=None):
        self._show_energy_fit(spec, ax, xdata_key='ekin', fit_par=fit_par, xlim=xlim, xlim_scale=xlim_scale)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(), text_pos='right', fontsize=10) 
        spec.view._addtext_gauge_par(ax, fit_par=fit_par, text_pos='right', fontsize=6)
        
    def _show_ebin_fit(self, spec, ax, fit_par='fitPar', xlim=['auto', 'auto'], xlim_scale=None):
        self._show_energy_fit(spec, ax, xdata_key='ebin', fit_par=fit_par, xlim=xlim, xlim_scale=xlim_scale)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(), fontsize=10) 
        spec.view._addtext_gauge_par(ax, fit_par=fit_par, fontsize=6)
                
        
    def show_tof_fit(self, layout=[5,4], fit_par='fitPar', time_unit=1e-6,
                     xlim=[0, 'auto'], xlim_scale=None, pdf=False):
        self._show(self._show_tof_fit, layout=layout, fit_par=fit_par, time_unit=time_unit,
                   xlim=xlim, xlim_scale=xlim_scale)
            
    def show_ekin_fit(self, layout=[5,4], fit_par='fitPar', xlim=['auto', 'auto'],
                      xlim_scale=None, pdf=False):
        self._show(self._show_ekin_fit, layout=layout, pdf=pdf, fit_par=fit_par, xlim=xlim, xlim_scale=xlim_scale)
        
    def show_ebin_fit(self, layout=[5,4], fit_par='fitPar', xlim=['auto', 'auto'],
                      xlim_scale=None, pdf=False):
        self._show(self._show_ebin_fit, layout=layout, pdf=pdf, fit_par=fit_par, xlim=xlim, xlim_scale=xlim_scale)    



class ViewWaterFitList(ViewPesList):
    def __init__(self, speclist):
        self.speclist = speclist


    def _show_tof_fit(self, spec, ax, fit_par='fitPar', time_unit=1e-6, time_label='Flight Time',
                      xlim=[0, 'auto'], xlim_scale=None):
        xdata_key = spec.mdata.data('fitXdataKey')
        ydata_key = spec.mdata.data('fitYdataKey')
        spec.view.plot_tof(ax, xdata_key=xdata_key, ydata_key=ydata_key, time_unit=time_unit,
                      xlim=xlim, xlim_scale=xlim_scale, color='black')
        spec.view.plot_tof_fit(ax, xdata_key=xdata_key, ydata_key=ydata_key, fit_par=fit_par,
                          time_unit=time_unit)
        spec.view._addtext_file_id(ax)
        spec.view._addtext_statusmarker(ax, xdata_key=xdata_key, ydata_key=ydata_key, text_pos='left')
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(), text_pos='right', fontsize=10)
        spec.view._addtext_fitvalues(ax, plot_type='tof', fit_par=fit_par, time_unit=time_unit, text_pos='right', fontsize=6)

    def _show_energy_fit(self, spec, ax, plot_type, fit_par, xlim, xlim_scale):
        'TODO: use method from View instead (after minimal modification).'
        plot_key_map = {'ekin': {'tof_intensity': [spec.view.plot_ekin, 'ekin', 'jIntensity'],
                                 'tof_intensitySub': [spec.view.plot_ekin, 'ekin', 'jIntensitySub'],
                                 'tofGauged_intensity': [spec.view.plot_ekin, 'ekinGauged', 'jIntensityGauged'],
                                 'tofGauged_intensitySub': [spec.view.plot_ekin, 'ekinGauged', 'jIntensityGaugedSub'],
                                 },
                        'ebin': {'tof_intensity': [spec.view.plot_ebin, 'ebin', 'jIntensity'],
                                 'tof_intensitySub': [spec.view.plot_ebin, 'ebin', 'jIntensitySub'],
                                 'tofGauged_intensity': [spec.view.plot_ebin, 'ebinGauged', 'jIntensityGauged'],
                                 'tofGauged_intensitySub': [spec.view.plot_ebin, 'ebinGauged', 'jIntensityGaugedSub'],
                                 }
                        }
        plot_method, xdata_key, ydata_key = plot_key_map[plot_type]['{}_{}'.format(spec.view.spec.mdata.data('fitXdataKey'),
                                                                                   spec.view.spec.mdata.data('fitYdataKey'))]
        plot_method(ax, xdata_key=xdata_key, ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale)
        spec.view.plot_energy_fit(ax, fit_par=fit_par, xdata_key=xdata_key,
                             fit_xdata_key=spec.view.spec.mdata.data('fitXdataKey'))       
        spec.view._addtext_file_id(ax)
        spec.view._addtext_statusmarker(ax, xdata_key=xdata_key, ydata_key=ydata_key, text_pos='left')


    def _show_ekin_fit(self, spec, ax, fit_par='fitPar', xlim=[0, 'auto'], xlim_scale=None):
        self._show_energy_fit(spec, ax, plot_type='ekin', fit_par=fit_par, xlim=xlim, xlim_scale=xlim_scale)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(), text_pos='right', fontsize=10) 
        spec.view._addtext_fitvalues(ax, plot_type='ekin', fit_par=fit_par, text_pos='right', fontsize=6)


    def _show_ebin_fit(self, spec, ax, fit_par='fitPar', xlim=[0, 'auto'], xlim_scale=None):
        self._show_energy_fit(spec, ax, plot_type='ebin', fit_par=fit_par, xlim=xlim, xlim_scale=xlim_scale)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(), fontsize=10) 
        spec.view._addtext_fitvalues(ax, plot_type='ebin', fit_par=fit_par, fontsize=6)


    def show_tof_fit(self, layout=[5,4], fit_par='fitPar', time_unit=1e-6,
                     xlim=[0, 'auto'], xlim_scale=None, pdf=False):
        self._show(self._show_tof_fit, layout=layout, pdf=pdf, fit_par=fit_par, time_unit=time_unit,
                   xlim=xlim, xlim_scale=xlim_scale)

    def show_ekin_fit(self, layout=[5,4], fit_par='fitPar', xlim=[0, 'auto'], xlim_scale=None, pdf=False):
        self._show(self._show_ekin_fit, layout=layout, pdf=pdf, fit_par=fit_par, xlim=xlim, xlim_scale=xlim_scale)
        
    def show_ebin_fit(self, layout=[5,4], fit_par='fitPar', xlim=[0, 'auto'], xlim_scale=None, pdf=False):
        self._show(self._show_ebin_fit, layout=layout, pdf=pdf, fit_par=fit_par, xlim=xlim, xlim_scale=xlim_scale) 






class OverView(object):
    def __init__(self,specList, cfg):
        self.cfg = cfg
        'specList is a list of sqlite3.Row objects'
        #print '__init__: Initializing View object.'
        if type(specList) is list:
            self.specList = specList
        else:
            raise ValueError('Argument must be list of sqlite3.Row objects')
        #self.fig = plt.figure()
        #print 'Figure created.'
        #self.ax = self.fig.add_subplot(1,1,1)



    def show(self, xdata_key, ydata_key, fit_par=None, xlim=['auto', 'auto'], xlim_scale=None, size=[5, 4], pdf=False):
        '''
        Takes a list of picklefile paths, and creates a overview plot.
        '''
        # auxiliary methods
        def build_idx_list(size):
            return np.arange(1,size[0]*size[1]+1).reshape(size[0],size[1]).transpose().reshape(size[0]*size[1])
        
        def plot_water_ebin_fit(spec, ax, fit_par):
            if fit_par is None:
                spec.view.plot_ebin(ax, xdata_key=xdata_key,
                                           ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale)
            else:
                spec.view.plot_ebin(ax, xdata_key=xdata_key,
                                           ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale)
                spec.view.plot_energy_fit(ax, fit_par=fit_par, xdata_key=xdata_key,
                                                 fit_xdata_key=spec.mdata.data('fitXdataKey'))
                spec.view._addtext_fitvalues(ax, plot_type='ebin', fit_par=fit_par, fontsize=9)
    
        def plot_pt_ebin_fit(spec, ax, fit_par):
            if fit_par is None:
                spec.view.plot_ebin(ax, xdata_key=xdata_key,
                                    ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale)
            else:
                spec.view.plot_ebin(ax, xdata_key=xdata_key,
                                    ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale)
                spec.view.plot_energy_fit(ax, fit_par=fit_par, xdata_key=xdata_key)
                spec.view._addtext_gauge_par(ax, fit_par=fit_par, fontsize=7)            
            
             
             
             
        def format_overview_plot(ax):
              
            for tick in ax.xaxis.get_major_ticks():
                tick.tick2On=True
                tick.gridOn=True
                tick.label1On=True
                tick.label2On=False
                tick.tick1On=True
            for label in ax.xaxis.get_ticklabels():
                label.set_fontsize(7)
            ax.yaxis.set_major_locator(mpl.ticker.NullLocator())
            ax.legend_=None
            ax.lines[0].set_linewidth(.3)
            ax.grid(linewidth=.1, linestyle=':', color='black')


        # main method
        if pdf:
            fname = os.path.join(os.path.expanduser('~'), 'export.pdf')
            pdf_file = Pdf.PdfPages(fname)
        
        idx_list = build_idx_list(size)
        plot_list = list(self.specList)
        plot_list.reverse()
        figidx = 1
        'TODO: clear or del remains from previous plots'
        while len(plot_list) > 0:
            # create page
            print('Creating page', figidx)
            fig = plt.figure(figidx, figsize=(0.21/constants.inch, 0.297/constants.inch))
            plt.subplots_adjust(left  = 0.03, right = 0.97, bottom = 0.03, top = 0.97,
                                wspace = 0.1, hspace = 0.14)
            plotidx = 0
            while plotidx < size[0]*size[1] and len(plot_list) > 0:
                #print 'Creating plot', plotidx
                row = plot_list.pop()
                #print 'type row is:', type(row)
                pf = row['pickleFile']
                currentspec = load.load_pickle(self.cfg, pf)
                currentax = fig.add_subplot(size[0],size[1],idx_list[plotidx])
                if currentspec.mdata.data('specTypeClass') == 'specPeWater':
                    plot_water_ebin_fit(currentspec, currentax, fit_par)
                elif currentspec.mdata.data('specTypeClass') == 'specPePt':
                    plot_pt_ebin_fit(currentspec, currentax, fit_par)
                else:
                    raise ValueError('Unsupported spec type: {}'.format(currentspec.mdata.data('datFile')))
                currentspec.view._addtext_file_id(currentax)
                currentspec.view._addtext_cluster_id(currentax, 
                                                     currentspec.view._pretty_format_clusterid(),
                                                     fontsize=10)
                currentspec.view._addtext_statusmarker(currentax, xdata_key=xdata_key,
                                                       ydata_key=ydata_key, text_pos='left')
                format_overview_plot(currentax)
                plotidx += 1
            if pdf:
                fig.savefig(pdf_file, dpi=None, facecolor='w', edgecolor='w',
                            orientation='portrait', papertype='a4', format='pdf')
            figidx += 1
        if pdf:    
            pdf_file.close()
        
 
        
        


