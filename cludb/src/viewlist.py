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
    
    def _format_overview_plot(self, ax, show_yticks=False):
          
        for tick in ax.xaxis.get_major_ticks():
            tick.tick2On=True
            tick.gridOn=True
            tick.label1On=True
            tick.label2On=False
            tick.tick1On=True
        for label in ax.xaxis.get_ticklabels():
            label.set_fontsize(7)
        if show_yticks:
            for label in ax.yaxis.get_ticklabels():
                label.set_fontsize(5)
        else:            
            ax.yaxis.set_major_locator(mpl.ticker.NullLocator())
        ax.legend_=None
        ax.lines[0].set_linewidth(.3)
        ax.xaxis.grid(linewidth=.1, linestyle=':', color='black')
        
    def _format_time_label(self, label, time_unit):
        if time_unit not in [1, 1e-3, 1e-6, 1e-9]:
            raise ValueError('time_unit must be one of: 1, 1e-3, 1e-6, 1e-9.')
        prefix_map = ['', 'm', '\mu ', 'n']
        prefix = prefix_map[int(abs(np.log10(time_unit)/3))]
        return r'{0} (${1}s$)'.format(label, prefix)
         
        
    def _show(self, show_fct, xlabel_str, layout=[7,3], pdf=False, show_yticks=False, **keywords):
        if pdf:
            fname = os.path.join(os.path.expanduser('~'), 'export.pdf')
            pdf_file = Pdf.PdfPages(fname)        
        print('keywords:', keywords)
        # calc margins and padding
        hspace = 0.028*layout[0]
        if show_yticks:
            margin = 0.045
            wspace = 0.045*layout[1]
        else:
            margin = 0.03
            wspace = 0.03*layout[1]
        subplt_idx = self._build_idx_list(layout)
        total_plots = len(self.speclist.pfile_list)
        plotcount = 0
        figidx = 1
        while plotcount < total_plots:
            # create page
            print('Plotting page', figidx)
            fig = plt.figure(figidx, figsize=(0.21/constants.inch, 0.297/constants.inch))
            plt.subplots_adjust(left  = margin, right = 1-margin, bottom = margin+0.01, top = 1-margin,
                                wspace = wspace, hspace = hspace)
            plotidx = 0
            while plotidx < layout[0]*layout[1] and plotcount < total_plots:
                #print('Creating plot', plotidx)
                cs = self.speclist.get_spec(plotcount)
                ax = fig.add_subplot(layout[0], layout[1], subplt_idx[plotidx])
                show_fct(cs, ax, layout[0], **keywords)
                self._format_overview_plot(ax, show_yticks=show_yticks)
                if (plotidx + 1) % layout[0] == 0 or plotcount + 1 == total_plots:
                    ax.set_xlabel(xlabel_str, fontsize=8)
                del cs
                plotidx += 1
                plotcount += 1
            if pdf:
                fig.savefig(pdf_file, dpi=None, facecolor='w', edgecolor='w',
                            orientation='portrait', papertype='a4', format='pdf')
                plt.close(fig) # may produce some console noise (which can be ignored)
            figidx += 1
        if pdf:    
            pdf_file.close()
               
    def _show_idx(self, spec, ax, layout_y, ydata_key='auto', xlim=['auto', 'auto'], xlim_scale=None, show_mdata=None):
        key_deps = {'idx': ['intensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw']}
        x_key, y_key = spec._auto_key_selection(xdata_key='idx', ydata_key=ydata_key, key_deps=key_deps) 
        spec.view.plot_idx(ax, x_key, y_key, xlim, xlim_scale=None, color='black')
        spec.view._addtext_file_id(ax, layout_y=layout_y) 
        if show_mdata is not None:
            spec.view._addtext_info(ax, spec.view._pretty_print_info(show_mdata), fontsize=6, text_pos='right')  
        
    def _show_tof(self, spec, ax, layout_y, xdata_key='auto', ydata_key='auto', time_unit=1e-6,
                  xlim=['auto', 'auto'], xlim_scale=None, show_mdata=None):
        key_deps = {'tof': ['intensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw'],
                    'tofGauged': ['intensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw']} 
        xdata_key, ydata_key = spec._auto_key_selection(xdata_key=xdata_key, ydata_key=ydata_key, key_deps=key_deps)      
        spec.view.plot_tof(ax, xdata_key=xdata_key, ydata_key=ydata_key, time_unit=time_unit, 
                           xlim=xlim, xlim_scale=xlim_scale)
        spec.view._addtext_file_id(ax, layout_y=layout_y)
        spec.view._addtext_statusmarker(ax, xdata_key=xdata_key, ydata_key=ydata_key, text_pos='left', layout_y=layout_y)
        if show_mdata is not None:
            spec.view._addtext_info(ax, spec.view._pretty_print_info(show_mdata), fontsize=6, text_pos='right')           
    
    
    def show_idx(self, layout=[7,3], ydata_key='auto', xlim=['auto', 'auto'], xlim_scale=None,
                 pdf=False, show_mdata=None, show_yticks=False):
        self._show(self._show_idx, xlabel_str='Index', layout=layout, pdf=pdf, ydata_key=ydata_key, xlim=xlim,
                   xlim_scale=xlim_scale, show_mdata=show_mdata, show_yticks=show_yticks)

    def show_tof(self, layout=[7,3], xdata_key='auto', ydata_key='auto', time_unit=1e-6,
                 xlim=['auto', 'auto'], xlim_scale=None, pdf=False, show_mdata=None, show_yticks=False):
        self._show(self._show_tof, xlabel_str=self._format_time_label('Time', time_unit), layout=layout, pdf=pdf,
                   xdata_key=xdata_key, ydata_key=ydata_key, time_unit=time_unit, xlim=xlim, xlim_scale=xlim_scale,
                   show_mdata=show_mdata, show_yticks=show_yticks)



class ViewPesList(ViewList):
    def __init__(self, speclist):
        self.speclist = speclist


    def _show_idx(self, spec, ax, layout_y, ydata_key='auto', xlim=['auto', 'auto'], xlim_scale=None, show_mdata=None):
        ViewList._show_idx(self, spec, ax, layout_y, ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale, show_mdata=show_mdata)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(), fontsize=10, text_pos='right')
        spec.view._addtext_statusmarker(ax, xdata_key='idx', ydata_key=ydata_key, text_pos='left', layout_y=layout_y)
        
    def _show_tof(self, spec, ax, layout_y, xdata_key='auto', ydata_key='auto', time_unit=1e-6,
                  xlim=['auto', 'auto'], xlim_scale=None, show_mdata=None):
        ViewList._show_tof(self, spec, ax, layout_y, xdata_key=xdata_key, ydata_key=ydata_key,
                   time_unit=time_unit, xlim=xlim, xlim_scale=xlim_scale, show_mdata=show_mdata)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(), fontsize=10, text_pos='right')
        #spec.view._addtext_statusmarker(ax, xdata_key=xdata_key, ydata_key=ydata_key, text_pos='left', layout_y=layout_y)          
        
    def _show_ekin(self, spec, ax, layout_y, xdata_key='auto', ydata_key='auto', xlim=['auto', 'auto'], xlim_scale=None, show_mdata=None):
        key_deps = {'ekin': ['jIntensity', 'jIntensitySub'],
                    'ekinGauged': ['jIntensityGauged', 'jIntensityGaugedSub']} 
        xdata_key, ydata_key = spec._auto_key_selection(xdata_key=xdata_key, ydata_key=ydata_key, key_deps=key_deps)        
        spec.view.plot_ekin(ax, xdata_key=xdata_key, ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale)
        spec.view._addtext_file_id(ax, layout_y=layout_y)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(), text_pos='right', fontsize=10)
        spec.view._addtext_statusmarker(ax, xdata_key=xdata_key, ydata_key=ydata_key, text_pos='left', layout_y=layout_y)
        if show_mdata is not None:
            spec.view._addtext_info(ax, spec.view._pretty_print_info(show_mdata), fontsize=6, text_pos='right')  
        
    def _show_ebin(self, spec, ax, layout_y, xdata_key='auto', ydata_key='auto', xlim=['auto', 'auto'], xlim_scale=None, show_mdata=None):
        key_deps = {'ebin': ['jIntensity', 'jIntensitySub'],
                    'ebinGauged': ['jIntensityGauged', 'jIntensityGaugedSub']} 
        xdata_key, ydata_key = spec._auto_key_selection(xdata_key=xdata_key, ydata_key=ydata_key, key_deps=key_deps)         
        spec.view.plot_ebin(ax, xdata_key=xdata_key, ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale)     
        spec.view._addtext_file_id(ax, layout_y=layout_y)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(), fontsize=10)
        spec.view._addtext_statusmarker(ax, xdata_key=xdata_key, ydata_key=ydata_key, text_pos='left', layout_y=layout_y)
        if show_mdata is not None:
            spec.view._addtext_info(ax, spec.view._pretty_print_info(show_mdata), fontsize=6) 
        


    def show_tof(self, layout=[7,3], xdata_key='auto', ydata_key='auto', time_unit=1e-6,
                 xlim=['auto', 'auto'], xlim_scale=None, pdf=False, show_mdata=None, show_yticks=False):
        self._show(self._show_tof, xlabel_str=self._format_time_label('Flight Time', time_unit), layout=layout, pdf=pdf,
                   xdata_key=xdata_key, ydata_key=ydata_key, time_unit=time_unit, xlim=xlim, xlim_scale=xlim_scale,
                   show_mdata=show_mdata, show_yticks=show_yticks)              
        
    def show_ekin(self, layout=[7,3], xdata_key='auto', ydata_key='auto',
                  xlim=['auto', 'auto'], xlim_scale=None, pdf=False, show_mdata=None):
        self._show(self._show_ekin, xlabel_str='E$_{kin}$ (eV)', layout=layout, pdf=pdf, xdata_key=xdata_key,
                   ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale, show_mdata=show_mdata)
        
    def show_ebin(self, layout=[7,3], xdata_key='auto', ydata_key='auto',
                  xlim=['auto', 'auto'], xlim_scale=None, pdf=False, show_mdata=None):
        self._show(self._show_ebin, xlabel_str='E$_{bin}$ (eV)', layout=layout, pdf=pdf, xdata_key=xdata_key,
                   ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale, show_mdata=show_mdata)        
        
        



class ViewPtFitList(ViewPesList):
    def __init__(self, speclist):
        self.speclist = speclist


    def _show_tof_fit(self, spec, ax, layout_y, fit_par='fitPar', time_unit=1e-6, xlim=['auto', 'auto'],
                      xlim_scale=None, show_mdata=None):
        xdata_key = 'tof'
        ydata_key = spec.mdata.data('fitYdataKey')
        self._show_tof(spec, ax, layout_y, xdata_key, ydata_key, time_unit, xlim, xlim_scale, show_mdata)
        spec.view.plot_tof_fit(ax, fit_par=fit_par, time_unit=time_unit)
        spec.view._addtext_gauge_par(ax, fit_par=fit_par, text_pos='right', fontsize=6)
        
    def _show_energy_fit(self, spec, ax, layout_y, xdata_key, fit_par, xlim, xlim_scale, show_mdata):
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
        spec.view._addtext_file_id(ax, layout_y=layout_y)
        spec.view._addtext_statusmarker(ax, xdata_key=xdata_key, ydata_key=ydata_key, text_pos='left', layout_y=layout_y)
        if show_mdata is not None:
            spec.view._addtext_info(ax, spec.view._pretty_print_info(show_mdata), fontsize=6)
        
    def _show_ekin_fit(self, spec, ax, layout_y, fit_par='fitPar', xlim=['auto', 'auto'], xlim_scale=None, show_mdata=None):
        self._show_energy_fit(spec, ax, layout_y, xdata_key='ekin', fit_par=fit_par, xlim=xlim, xlim_scale=xlim_scale, show_mdata=show_mdata)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(), text_pos='right', fontsize=10) 
        spec.view._addtext_gauge_par(ax, fit_par=fit_par, text_pos='right', fontsize=6)
        
    def _show_ebin_fit(self, spec, ax, layout_y, fit_par='fitPar', xlim=['auto', 'auto'], xlim_scale=None, show_mdata=None):
        self._show_energy_fit(spec, ax, layout_y, xdata_key='ebin', fit_par=fit_par, xlim=xlim, xlim_scale=xlim_scale, show_mdata=show_mdata)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(), fontsize=10) 
        spec.view._addtext_gauge_par(ax, fit_par=fit_par, fontsize=6)
                
        
    def show_tof_fit(self, layout=[7,3], fit_par='fitPar', time_unit=1e-6,
                     xlim=[0, 'auto'], xlim_scale=None, pdf=False, show_mdata=None, show_yticks=False):
        self._show(self._show_tof_fit, xlabel_str=self._format_time_label('Flight Time', time_unit),
                   layout=layout, pdf=pdf, fit_par=fit_par, time_unit=time_unit, xlim=xlim, xlim_scale=xlim_scale,
                   show_mdata=show_mdata, show_yticks=show_yticks)
            
    def show_ekin_fit(self, layout=[7,3], fit_par='fitPar', xlim=['auto', 'auto'],
                      xlim_scale=None, pdf=False, show_mdata=None):
        self._show(self._show_ekin_fit, xlabel_str='E$_{kin}$ (eV)', layout=layout, pdf=pdf,
                   fit_par=fit_par, xlim=xlim, xlim_scale=xlim_scale, show_mdata=show_mdata)
        
    def show_ebin_fit(self, layout=[7,3], fit_par='fitPar', xlim=['auto', 'auto'],
                      xlim_scale=None, pdf=False, show_mdata=None):
        self._show(self._show_ebin_fit, xlabel_str='E$_{bin}$ (eV)', layout=layout, pdf=pdf, fit_par=fit_par,
                   xlim=xlim, xlim_scale=xlim_scale, show_mdata=show_mdata)    



class ViewWaterFitList(ViewPesList):
    def __init__(self, speclist):
        self.speclist = speclist


    def _show_tof_fit(self, spec, ax, layout_y, fit_par='fitPar', time_unit=1e-6, time_label='Flight Time',
                      xlim=[0, 'auto'], xlim_scale=None, show_mdata=None):
        xdata_key = spec.mdata.data('fitXdataKey')
        ydata_key = spec.mdata.data('fitYdataKey')
        spec.view.plot_tof(ax, xdata_key=xdata_key, ydata_key=ydata_key, time_unit=time_unit,
                      xlim=xlim, xlim_scale=xlim_scale, color='black')
        spec.view.plot_tof_fit(ax, xdata_key=xdata_key, ydata_key=ydata_key, fit_par=fit_par,
                          time_unit=time_unit)
        spec.view._addtext_file_id(ax, layout_y=layout_y)
        spec.view._addtext_statusmarker(ax, xdata_key=xdata_key, ydata_key=ydata_key, text_pos='left', layout_y=layout_y)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(), text_pos='right', fontsize=10)
        spec.view._addtext_fitvalues(ax, plot_type='tof', fit_par=fit_par, time_unit=time_unit, text_pos='right', fontsize=6)
        if show_mdata is not None:
            spec.view._addtext_info(ax, spec.view._pretty_print_info(show_mdata), fontsize=6, text_vpos='top')

    def _show_energy_fit(self, spec, ax, layout_y, plot_type, fit_par, xlim, xlim_scale):
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
        spec.view._addtext_file_id(ax, layout_y=layout_y)
        spec.view._addtext_statusmarker(ax, xdata_key=xdata_key, ydata_key=ydata_key, text_pos='left', layout_y=layout_y)


    def _show_ekin_fit(self, spec, ax, layout_y, fit_par='fitPar', xlim=[0, 'auto'], xlim_scale=None, show_mdata=None):
        self._show_energy_fit(spec, ax, layout_y, plot_type='ekin', fit_par=fit_par, xlim=xlim, xlim_scale=xlim_scale)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(), text_pos='right', fontsize=10) 
        spec.view._addtext_fitvalues(ax, plot_type='ekin', fit_par=fit_par, text_pos='right', fontsize=6)
        if show_mdata is not None:
            spec.view._addtext_info(ax, spec.view._pretty_print_info(show_mdata), fontsize=6, text_vpos='top')

    def _show_ebin_fit(self, spec, ax, layout_y, fit_par='fitPar', xlim=[0, 'auto'], xlim_scale=None, show_mdata=None):
        self._show_energy_fit(spec, ax, layout_y, plot_type='ebin', fit_par=fit_par, xlim=xlim, xlim_scale=xlim_scale)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(), fontsize=10) 
        spec.view._addtext_fitvalues(ax, plot_type='ebin', fit_par=fit_par, fontsize=6)
        if show_mdata is not None:
            spec.view._addtext_info(ax, spec.view._pretty_print_info(show_mdata), fontsize=6, text_pos='right', text_vpos='top')


    def show_tof_fit(self, layout=[7,3], fit_par='fitPar', time_unit=1e-6,
                     xlim=[0, 'auto'], xlim_scale=None, pdf=False, show_mdata=None, show_yticks=False):
        self._show(self._show_tof_fit, xlabel_str=self._format_time_label('Flight Time', time_unit), layout=layout,
                   pdf=pdf, fit_par=fit_par, time_unit=time_unit, xlim=xlim, xlim_scale=xlim_scale,
                   show_mdata=show_mdata, show_yticks=show_yticks)

    def show_ekin_fit(self, layout=[7,3], fit_par='fitPar', xlim=[0, 'auto'], xlim_scale=None, pdf=False, show_mdata=None):
        self._show(self._show_ekin_fit, xlabel_str='E$_{kin}$ (eV)', layout=layout, pdf=pdf, fit_par=fit_par, xlim=xlim,
                   xlim_scale=xlim_scale, show_mdata=show_mdata)
        
    def show_ebin_fit(self, layout=[7,3], fit_par='fitPar', xlim=[0, 'auto'], xlim_scale=None, pdf=False, show_mdata=None):
        self._show(self._show_ebin_fit, xlabel_str='E$_{bin}$ (eV)', layout=layout, pdf=pdf, fit_par=fit_par, xlim=xlim,
                   xlim_scale=xlim_scale, show_mdata=show_mdata) 




class ViewMsList(ViewList):
    def __init__(self, speclist):
        self.speclist = speclist
        
    def _show_idx(self, spec, ax, layout_y, ydata_key='auto', xlim=['auto', 'auto'], xlim_scale=None, show_mdata=None):
        ViewList._show_idx(self, spec, ax, layout_y, ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale, show_mdata=show_mdata)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(ms=True), fontsize=10)
        spec.view._addtext_statusmarker(ax, xdata_key='idx', ydata_key=ydata_key, text_pos='left', layout_y=layout_y)
        
    def _show_tof(self, spec, ax, layout_y, xdata_key='auto', ydata_key='auto', time_unit=1e-6,
                  xlim=['auto', 'auto'], xlim_scale=None, show_mdata=None):
        ViewList._show_tof(self, spec, ax, layout_y, xdata_key=xdata_key, ydata_key=ydata_key,
                   time_unit=time_unit, xlim=xlim, xlim_scale=xlim_scale, show_mdata=show_mdata)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(ms=True), fontsize=10)        
                
    def _show_ms(self, spec, ax, layout_y, mass_key='cluster', xlim=['auto', 'auto'], xlim_scale=None, show_mdata=None):        
        spec.view.plot_ms(ax=ax, mass_key=mass_key, xlim=xlim, xlim_scale=xlim_scale)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(ms=True), fontsize=10)
        spec.view._addtext_file_id(ax, layout_y=layout_y) 
        if show_mdata is not None:
            spec.view._addtext_info(ax, spec.view._pretty_print_info(show_mdata), fontsize=6, text_pos='right')
            
    def _xlabel_str(self, mass_key):
        if mass_key == 'cluster':
            xlabel = 'Cluster Size (# cluster base units)'
        elif mass_key == 's_u':
            xlabel = 'Cluster Mass (simplified u)'
        else:
            xlabel = 'Cluster Mass (u)'
            
        return xlabel             
            
                    
    def show_tof(self, layout=[5,1], xdata_key='auto', ydata_key='auto', time_unit=1e-6,
                 xlim=['auto', 'auto'], xlim_scale=None, pdf=False, show_mdata=None, show_yticks=False):
        self._show(self._show_tof, xlabel_str=self._format_time_label('Flight Time', time_unit), layout=layout, pdf=pdf,
                   xdata_key=xdata_key, ydata_key=ydata_key, time_unit=time_unit, xlim=xlim, xlim_scale=xlim_scale,
                   show_mdata=show_mdata, show_yticks=show_yticks)  

        
    def show_ms(self, layout=[5,1], mass_key='cluster', xlim=['auto', 'auto'], xlim_scale=None,
                pdf=False, show_mdata=None):
        self._show(self._show_ms, xlabel_str=self._xlabel_str(mass_key), mass_key=mass_key,
                   layout=layout, pdf=pdf, xlim=xlim, xlim_scale=xlim_scale, show_mdata=show_mdata)        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
