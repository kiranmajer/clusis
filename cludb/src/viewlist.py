import matplotlib as mpl
import matplotlib.backends.backend_pdf as Pdf
import matplotlib.pyplot as plt
import scipy.constants as constants
#import load
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
         
        
    def _show(self, show_fct, xlabel_str, layout=[7,3], size=[21,29.7], pdf=True,
              show_yticks=False, **keywords):
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
        figidx = 101 # prevents reusing open plot windows
        while plotcount < total_plots:
            # create page
            print('Plotting page', figidx -100)
            fig = plt.figure(figidx, figsize=(size[0]/2.54, size[1]/2.54))
            plt.subplots_adjust(left  = margin, right = 1-margin, bottom = margin+0.01, top = 1-margin,
                                wspace = wspace, hspace = hspace)
            plotidx = 0
            while plotidx < layout[0]*layout[1] and plotcount < total_plots:
                #print('Creating plot', plotidx)
                cs = self.speclist.get_spec(plotcount)
                ax = fig.add_subplot(layout[0], layout[1], subplt_idx[plotidx])
                show_fct(cs, ax, **keywords)
                self._format_overview_plot(ax, show_yticks=show_yticks)
                if (plotidx + 1) % layout[0] == 0 or plotcount + 1 == total_plots:
                    ax.set_xlabel(xlabel_str, fontsize=8)
                del cs
                plotidx += 1
                plotcount += 1
            if pdf:
                fig.savefig(pdf_file, dpi=None, facecolor='w', edgecolor='w',
                            orientation='portrait', format='pdf') #papertype='a4', format='pdf')
                plt.close(fig) # may produce some console noise (which can be ignored)
            figidx += 1
        if pdf:    
            pdf_file.close()
               
    def _show_idx(self, spec, ax, ydata_key='auto', xlim=['auto', 'auto'], xlim_scale=None, show_mdata=None):
        key_deps = {'idx': ['intensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw']}
        x_key, y_key = spec._auto_key_selection(xdata_key='idx', ydata_key=ydata_key, key_deps=key_deps) 
        spec.view.plot_idx(ax, x_key, y_key, xlim, xlim_scale=None, color='black')
        spec.view._addtext_file_id(ax) 
        if show_mdata is not None:
            spec.view._addtext_info(ax, spec.view._pretty_print_info(show_mdata), fontsize=6, text_pos='right')  
        
    def _show_tof(self, spec, ax, xdata_key='auto', ydata_key='auto', time_unit=1e-6,
                  xlim=['auto', 'auto'], xlim_scale=None, show_mdata=None):
        key_deps = {'tof': ['intensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw'],
                    'tofGauged': ['intensity', 'intensitySub', 'rawIntensity', 'intensitySubRaw']} 
        xdata_key, ydata_key = spec._auto_key_selection(xdata_key=xdata_key, ydata_key=ydata_key, key_deps=key_deps)      
        spec.view.plot_tof(ax, xdata_key=xdata_key, ydata_key=ydata_key, time_unit=time_unit, 
                           xlim=xlim, xlim_scale=xlim_scale)
        spec.view._addtext_file_id(ax)
        spec.view._addtext_statusmarker(ax, xdata_key=xdata_key, ydata_key=ydata_key, text_pos='left')
        if show_mdata is not None:
            spec.view._addtext_info(ax, spec.view._pretty_print_info(show_mdata), fontsize=6, text_pos='right')           
    
    
    def show_idx(self, layout=[7,3], size=[21,29.7], ydata_key='auto', xlim=['auto', 'auto'], xlim_scale=None,
                 pdf=True, show_mdata=None, show_yticks=False):
        self._show(self._show_idx, xlabel_str='Index', layout=layout, size=size, pdf=pdf, ydata_key=ydata_key, xlim=xlim,
                   xlim_scale=xlim_scale, show_mdata=show_mdata, show_yticks=show_yticks)

    def show_tof(self, layout=[7,3], size=[21,29.7], xdata_key='auto', ydata_key='auto', time_unit=1e-6,
                 xlim=['auto', 'auto'], xlim_scale=None, pdf=True, show_mdata=None, show_yticks=False):
        self._show(self._show_tof, xlabel_str=self._format_time_label('Time', time_unit), layout=layout, size=size, pdf=pdf,
                   xdata_key=xdata_key, ydata_key=ydata_key, time_unit=time_unit, xlim=xlim, xlim_scale=xlim_scale,
                   show_mdata=show_mdata, show_yticks=show_yticks)



class ViewPesList(ViewList):
    def __init__(self, speclist):
        self.speclist = speclist


    def _show_idx(self, spec, ax, ydata_key='auto', xlim=['auto', 'auto'], xlim_scale=None, show_mdata=None):
        ViewList._show_idx(self, spec, ax, ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale, show_mdata=show_mdata)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(), fontsize=10, text_pos='right')
        spec.view._addtext_statusmarker(ax, xdata_key='idx', ydata_key=ydata_key, text_pos='left')
        
    def _show_tof(self, spec, ax, xdata_key='auto', ydata_key='auto', time_unit=1e-6,
                  xlim=['auto', 'auto'], xlim_scale=None, show_mdata=None):
        ViewList._show_tof(self, spec, ax, xdata_key=xdata_key, ydata_key=ydata_key,
                   time_unit=time_unit, xlim=xlim, xlim_scale=xlim_scale, show_mdata=show_mdata)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(), fontsize=10, text_pos='right')
        #spec.view._addtext_statusmarker(ax, xdata_key=xdata_key, ydata_key=ydata_key, text_pos='left')          
        
    def _show_ekin(self, spec, ax, xdata_key='auto', ydata_key='auto', xlim=['auto', 'auto'], xlim_scale=None, show_mdata=None):
        key_deps = {'ekin': ['jIntensity', 'jIntensitySub'],
                    'ekinGauged': ['jIntensityGauged', 'jIntensityGaugedSub']} 
        xdata_key, ydata_key = spec._auto_key_selection(xdata_key=xdata_key, ydata_key=ydata_key, key_deps=key_deps)        
        spec.view.plot_ekin(ax, xdata_key=xdata_key, ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale)
        spec.view._addtext_file_id(ax)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(), text_pos='right', fontsize=10)
        spec.view._addtext_statusmarker(ax, xdata_key=xdata_key, ydata_key=ydata_key, text_pos='left')
        if show_mdata is not None:
            spec.view._addtext_info(ax, spec.view._pretty_print_info(show_mdata), fontsize=6, text_pos='right')  
        
    def _show_ebin(self, spec, ax, xdata_key='auto', ydata_key='auto', xlim=['auto', 'auto'], xlim_scale=None, show_mdata=None):
        key_deps = {'ebin': ['jIntensity', 'jIntensitySub'],
                    'ebinGauged': ['jIntensityGauged', 'jIntensityGaugedSub']} 
        xdata_key, ydata_key = spec._auto_key_selection(xdata_key=xdata_key, ydata_key=ydata_key, key_deps=key_deps)         
        spec.view.plot_ebin(ax, xdata_key=xdata_key, ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale)     
        spec.view._addtext_file_id(ax)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(), fontsize=10)
        spec.view._addtext_statusmarker(ax, xdata_key=xdata_key, ydata_key=ydata_key, text_pos='left')
        if show_mdata is not None:
            spec.view._addtext_info(ax, spec.view._pretty_print_info(show_mdata), fontsize=6) 
        


    def show_tof(self, layout=[7,3], size=[21,29.7], xdata_key='auto', ydata_key='auto', time_unit=1e-6,
                 xlim=['auto', 'auto'], xlim_scale=None, pdf=True, show_mdata=None, show_yticks=False):
        self._show(self._show_tof, xlabel_str=self._format_time_label('Flight Time', time_unit), layout=layout, size=size, pdf=pdf,
                   xdata_key=xdata_key, ydata_key=ydata_key, time_unit=time_unit, xlim=xlim, xlim_scale=xlim_scale,
                   show_mdata=show_mdata, show_yticks=show_yticks)              
        
    def show_ekin(self, layout=[7,3], size=[21,29.7], xdata_key='auto', ydata_key='auto',
                  xlim=['auto', 'auto'], xlim_scale=None, pdf=True, show_mdata=None):
        self._show(self._show_ekin, xlabel_str='E$_{kin}$ (eV)', layout=layout, size=size, pdf=pdf, xdata_key=xdata_key,
                   ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale, show_mdata=show_mdata)
        
    def show_ebin(self, layout=[7,3], size=[21,29.7], xdata_key='auto', ydata_key='auto',
                  xlim=['auto', 'auto'], xlim_scale=None, pdf=True, show_mdata=None):
        self._show(self._show_ebin, xlabel_str='E$_{bin}$ (eV)', layout=layout, size=size, pdf=pdf, xdata_key=xdata_key,
                   ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale, show_mdata=show_mdata)        


    def _show_comp_spec(self, spec, ax, comp_spec_id, linestyle='-', linewidth=0.5, **keywords):
        base_plot_map = {'tof': self._show_tof,
                         'ekin': self._show_ekin,
                         'ebin': self._show_ebin}
        if type(comp_spec_id) is not list:
            comp_spec_id = [comp_spec_id]
        base_plot_mode = None
        for csid in comp_spec_id:
            if csid not in spec.mdata.data('compSpecs').keys():
                raise ValueError('No comparison spec with id "{}" is attached to this spec.')
            # set mode for base plot and plot
            if base_plot_mode is None:
                for k in base_plot_map.keys():
                    if k in spec.mdata.data('compSpecs')[csid]['xdata_key']:
                        base_plot_map[k](spec, ax, **keywords)
                        base_plot_mode = k
                        break
            elif base_plot_mode not in spec.mdata.data('compSpecs')[csid]['xdata_key']:
                raise ValueError('Comparison spectrum type ({}) does not fit to chosen view ({}).'.format(spec.mdata.data('compSpecs')[csid]['xdata_key'],
                                                                                                          base_plot_mode))
            if 'xscale_type' in spec.mdata.data('compSpecs')[csid].keys() and spec.mdata.data('compSpecs')[csid]['xscale_type'] == 'fermi_energy':
                spec.view._add_fermiscaled_spec(specfile=spec.mdata.data('compSpecs')[csid]['specfile'],
                                                xscale=spec.mdata.data('compSpecs')[csid]['xscale_type'],
                                                yscale=spec.mdata.data('compSpecs')[csid]['yscale'],
                                                yscale_type=spec.mdata.data('compSpecs')[csid]['yscale_type'],
                                                color=spec.mdata.data('compSpecs')[csid]['color'],
                                                linestyle=linestyle,
                                                linewidth=linewidth,
                                                fontsize_clusterid=10,
                                                ax=ax)
            else:
                spec.view._add_spec(spec.mdata.data('compSpecs')[csid]['specfile'],
                              spec.mdata.data('compSpecs')[csid]['xscale'],
                              spec.mdata.data('compSpecs')[csid]['yscale'],
                              spec.mdata.data('compSpecs')[csid]['yscale_type'],
                              spec.mdata.data('compSpecs')[csid]['xoffset'],
                              spec.mdata.data('compSpecs')[csid]['yoffset'],
                              spec.mdata.data('compSpecs')[csid]['color'],
                              linestyle=linestyle,
                              linewidth=linewidth,
                              fontsize_clusterid=10,
                              ax=ax)
    
        
    def show_comp_spec(self, comp_spec_id, layout=[7,3], size=[21,29.7], xlim=['auto', 'auto'],
                       xlim_scale=None, pdf=True, show_mdata=None, linestyle='-', linewidth=0.5,):
        self._show(self._show_comp_spec, xlabel_str='TODO', comp_spec_id=comp_spec_id, linestyle=linestyle,
                   linewidth=linewidth, layout=layout, size=size, pdf=pdf, xlim=xlim, xlim_scale=xlim_scale, show_mdata=show_mdata)



class ViewPtFitList(ViewPesList):
    def __init__(self, speclist):
        self.speclist = speclist


    def _show_tof_fit(self, spec, ax, fit_par='fitPar', time_unit=1e-6, xlim=['auto', 'auto'],
                      xlim_scale=None, show_mdata=None, single_peaks=False):
        xdata_key = 'tof'
        ydata_key = spec.mdata.data('fitYdataKey')
        self._show_tof(spec, ax, xdata_key, ydata_key, time_unit, xlim, xlim_scale, show_mdata)
        spec.view.plot_tof_fit(ax, fit_par=fit_par, time_unit=time_unit, single_peaks=single_peaks)
        spec.view._addtext_gauge_par(ax, fit_par=fit_par, text_pos='right', fontsize=6)
        
    def _show_energy_fit(self, spec, ax, xdata_key, fit_par, xlim, xlim_scale, show_mdata, single_peaks=False):
        'TODO: use method from View instead (after minimal modification).'
        plot_method = {'ekin': spec.view.plot_ekin, 'ebin': spec.view.plot_ebin}
        if xdata_key not in ['ekin', 'ebin']:
            raise ValueError("xdata_key must be one of: 'ekin', 'ebin'")
        if 'Sub' in spec.mdata.data('fitYdataKey'):
            ydata_key = 'jIntensitySub'
        else:
            ydata_key = 'jIntensity'        
        plot_method[xdata_key](ax, xdata_key=xdata_key, ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale)
        spec.view.plot_energy_fit(ax, fit_par=fit_par, xdata_key=xdata_key, single_peaks=single_peaks)      
        spec.view._addtext_file_id(ax)
        spec.view._addtext_statusmarker(ax, xdata_key=xdata_key, ydata_key=ydata_key, text_pos='left')
        if show_mdata is not None:
            spec.view._addtext_info(ax, spec.view._pretty_print_info(show_mdata), fontsize=6)
        
    def _show_ekin_fit(self, spec, ax, fit_par='fitPar', xlim=['auto', 'auto'], xlim_scale=None, show_mdata=None, single_peaks=False):
        self._show_energy_fit(spec, ax, xdata_key='ekin', fit_par=fit_par, xlim=xlim, xlim_scale=xlim_scale,
                              show_mdata=show_mdata, single_peaks=single_peaks)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(), text_pos='right', fontsize=10) 
        spec.view._addtext_gauge_par(ax, fit_par=fit_par, text_pos='right', fontsize=6)
        
    def _show_ebin_fit(self, spec, ax, fit_par='fitPar', xlim=['auto', 'auto'], xlim_scale=None, show_mdata=None, single_peaks=False):
        self._show_energy_fit(spec, ax, xdata_key='ebin', fit_par=fit_par, xlim=xlim, xlim_scale=xlim_scale,
                              show_mdata=show_mdata, single_peaks=single_peaks)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(), fontsize=10) 
        spec.view._addtext_gauge_par(ax, fit_par=fit_par, fontsize=6)
                
        
    def show_tof_fit(self, layout=[7,3], size=[21,29.7], fit_par='fitPar', time_unit=1e-6,
                     xlim=[0, 'auto'], xlim_scale=None, pdf=True, show_mdata=None, show_yticks=False, single_peaks=False):
        self._show(self._show_tof_fit, xlabel_str=self._format_time_label('Flight Time', time_unit),
                   layout=layout, size=size, pdf=pdf, fit_par=fit_par, time_unit=time_unit, xlim=xlim, xlim_scale=xlim_scale,
                   show_mdata=show_mdata, show_yticks=show_yticks, single_peaks=single_peaks)
            
    def show_ekin_fit(self, layout=[7,3], size=[21,29.7], fit_par='fitPar', xlim=['auto', 'auto'],
                      xlim_scale=None, pdf=True, show_mdata=None, single_peaks=False):
        self._show(self._show_ekin_fit, xlabel_str='E$_{kin}$ (eV)', layout=layout, size=size, pdf=pdf,
                   fit_par=fit_par, xlim=xlim, xlim_scale=xlim_scale, show_mdata=show_mdata, single_peaks=single_peaks)
        
    def show_ebin_fit(self, layout=[7,3], size=[21,29.7], fit_par='fitPar', xlim=['auto', 'auto'],
                      xlim_scale=None, pdf=True, show_mdata=None, single_peaks=False):
        self._show(self._show_ebin_fit, xlabel_str='E$_{bin}$ (eV)', layout=layout, size=size, pdf=pdf, fit_par=fit_par,
                   xlim=xlim, xlim_scale=xlim_scale, show_mdata=show_mdata, single_peaks=single_peaks)    



class ViewWaterFitList(ViewPesList):
    def __init__(self, speclist):
        self.speclist = speclist


    def _show_tof_fit(self, spec, ax, fit_par='fitPar', time_unit=1e-6, time_label='Flight Time',
                      xlim=[0, 'auto'], xlim_scale=None, show_mdata=None):
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
        if show_mdata is not None:
            spec.view._addtext_info(ax, spec.view._pretty_print_info(show_mdata), fontsize=6, text_vpos='top')

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


    def _show_ekin_fit(self, spec, ax, fit_par='fitPar', xlim=[0, 'auto'], xlim_scale=None,
                       show_mdata=None):
        self._show_energy_fit(spec, ax, plot_type='ekin', fit_par=fit_par, xlim=xlim,
                              xlim_scale=xlim_scale)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(), text_pos='right',
                                      fontsize=10) 
        spec.view._addtext_fitvalues(ax, plot_type='ekin', fit_par=fit_par, text_pos='right', fontsize=6)
        if show_mdata is not None:
            spec.view._addtext_info(ax, spec.view._pretty_print_info(show_mdata), fontsize=6,
                                    text_vpos='top')

    def _show_ebin_fit(self, spec, ax, fit_par='fitPar', xlim=[0, 'auto'], xlim_scale=None,
                       show_mdata=None):
        self._show_energy_fit(spec, ax, plot_type='ebin', fit_par=fit_par, xlim=xlim,
                              xlim_scale=xlim_scale)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(), fontsize=10) 
        spec.view._addtext_fitvalues(ax, plot_type='ebin', fit_par=fit_par, fontsize=6)
        if show_mdata is not None:
            spec.view._addtext_info(ax, spec.view._pretty_print_info(show_mdata), fontsize=6,
                                    text_pos='right', text_vpos='top')


    def show_tof_fit(self, layout=[7,3], size=[21,29.7], fit_par='fitPar', time_unit=1e-6,
                     xlim=[0, 'auto'], xlim_scale=None, pdf=True, show_mdata=None, show_yticks=False):
        self._show(self._show_tof_fit, xlabel_str=self._format_time_label('Flight Time', time_unit),
                   layout=layout, pdf=pdf, fit_par=fit_par, time_unit=time_unit, xlim=xlim,
                   xlim_scale=xlim_scale, show_mdata=show_mdata, show_yticks=show_yticks)

    def show_ekin_fit(self, layout=[7,3], size=[21,29.7], fit_par='fitPar', xlim=[0, 'auto'],
                      xlim_scale=None, pdf=True, show_mdata=None):
        self._show(self._show_ekin_fit, xlabel_str='E$_{kin}$ (eV)', layout=layout, size=size,
                   pdf=pdf, fit_par=fit_par, xlim=xlim, xlim_scale=xlim_scale,
                   show_mdata=show_mdata)
        
    def show_ebin_fit(self, layout=[7,3], size=[21,29.7], fit_par='fitPar', xlim=[0, 'auto'],
                      xlim_scale=None, pdf=True, show_mdata=None):
        self._show(self._show_ebin_fit, xlabel_str='E$_{bin}$ (eV)', layout=layout, size=size,
                   pdf=pdf, fit_par=fit_par, xlim=xlim, xlim_scale=xlim_scale,
                   show_mdata=show_mdata) 




class ViewMsList(ViewList):
    def __init__(self, speclist):
        self.speclist = speclist
        
    def _show_idx(self, spec, ax, ydata_key='auto', xlim=['auto', 'auto'], xlim_scale=None, show_mdata=None):
        ViewList._show_idx(self, spec, ax, ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale, show_mdata=show_mdata)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(ms=True), fontsize=10)
        spec.view._addtext_statusmarker(ax, xdata_key='idx', ydata_key=ydata_key, text_pos='left')
        
    def _show_tof(self, spec, ax, xdata_key='auto', ydata_key='auto', time_unit=1e-6,
                  xlim=['auto', 'auto'], xlim_scale=None, show_mdata=None):
        ViewList._show_tof(self, spec, ax, xdata_key=xdata_key, ydata_key=ydata_key,
                   time_unit=time_unit, xlim=xlim, xlim_scale=xlim_scale, show_mdata=show_mdata)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(ms=True), fontsize=10)        
                
    def _show_ms(self, spec, ax, mass_key='cluster', xlim=['auto', 'auto'], xlim_scale=None,
                 fontsize_clusterid=10, show_mdata=None):        
        spec.view.plot_ms(ax=ax, mass_key=mass_key, xlim=xlim, xlim_scale=xlim_scale)
        if fontsize_clusterid:
            spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(ms=True),
                                          fontsize=fontsize_clusterid)
        spec.view._addtext_file_id(ax) 
        if show_mdata is not None:
            spec.view._addtext_info(ax, spec.view._pretty_print_info(show_mdata), fontsize=6, text_pos='left')
            
    def _xlabel_str(self, mass_key):
        if mass_key == 'cluster':
            xlabel = 'Cluster Size (# cluster base units)'
        elif mass_key == 's_u':
            xlabel = 'Cluster Mass (simplified u)'
        else:
            xlabel = 'Cluster Mass (u)'
            
        return xlabel             
            
                    
    def show_tof(self, layout=[5,1], size=[21,29.7], xdata_key='auto', ydata_key='auto', time_unit=1e-6,
                 xlim=['auto', 'auto'], xlim_scale=None, pdf=True, show_mdata=None, show_yticks=False):
        self._show(self._show_tof, xlabel_str=self._format_time_label('Flight Time', time_unit), layout=layout, size=size, pdf=pdf,
                   xdata_key=xdata_key, ydata_key=ydata_key, time_unit=time_unit, xlim=xlim, xlim_scale=xlim_scale,
                   show_mdata=show_mdata, show_yticks=show_yticks)  

        
    def show_ms(self, layout=[5,1], size=[21,29.7], mass_key='cluster', xlim=['auto', 'auto'], xlim_scale=None,
                pdf=True, fontsize_clusterid=10, show_mdata=None):
        self._show(self._show_ms, xlabel_str=self._xlabel_str(mass_key), mass_key=mass_key,
                   layout=layout, size=size, pdf=pdf, xlim=xlim, xlim_scale=xlim_scale, fontsize=fontsize_clusterid,
                   show_mdata=show_mdata)        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
