import matplotlib as mpl
from matplotlib.backends.backend_pdf import PdfPages
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
            pdf_file = PdfPages(fname)        
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
            #fig = plt.figure(figidx, figsize=(size[0]/2.54, size[1]/2.54))
            fig = plt.figure(figsize=(size[0]/2.54, size[1]/2.54))
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
            else:
                fig.show()
            figidx += 1
        if pdf:    
            pdf_file.close()
               
    def _show_idx(self, spec, ax, ydata_key='auto', xlim=['auto', 'auto'], xlim_scale=None,
                  n_xticks=None, show_mdata=None,
                  key_deps={'idx': ['rawVoltageSpec', 'rawVoltageRamp', 'rawVoltagePulse']}):
        x_key, y_key = spec._auto_key_selection(xdata_key='idx', ydata_key=ydata_key, key_deps=key_deps) 
        spec.view.plot_idx(ax, x_key, y_key, xlim, xlim_scale=None, n_xticks=n_xticks, color='black')
        spec.view._addtext_file_id(ax) 
        if show_mdata is not None:
            spec.view._addtext_info(ax, spec.view._pretty_print_info(show_mdata), fontsize=6, text_pos='right')  
        
    def _show_time(self, spec, ax, xdata_key='auto', ydata_key='auto', time_unit=1e-6,
                  xlim=['auto', 'auto'], xlim_scale=None, n_xticks=None, show_mdata=None,
                  key_deps={'time': ['rawVoltageSpec', 'rawVoltageRamp', 'rawVoltagePulse'],}):
        xdata_key, ydata_key = spec._auto_key_selection(xdata_key=xdata_key, ydata_key=ydata_key, key_deps=key_deps)      
        spec.view.plot_time(ax, xdata_key=xdata_key, ydata_key=ydata_key, time_unit=time_unit, 
                            xlim=xlim, xlim_scale=xlim_scale, n_xticks=n_xticks)
        spec.view._addtext_file_id(ax)
        spec.view._addtext_statusmarker(ax, xdata_key=xdata_key, ydata_key=ydata_key, text_pos='left')
        if show_mdata is not None:
            spec.view._addtext_info(ax, spec.view._pretty_print_info(show_mdata), fontsize=6, text_pos='right')           
    
    
    def show_idx(self, layout=[7,3], size=[21,29.7], ydata_key='auto', xlim=['auto', 'auto'],
                 xlim_scale=None, n_xticks=None, pdf=True, show_mdata=None, show_yticks=False):
        self._show(self._show_idx, xlabel_str='Index', layout=layout, size=size, pdf=pdf,
                   ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale, n_xticks=n_xticks,
                   show_mdata=show_mdata, show_yticks=show_yticks)

    def show_time(self, layout=[7,3], size=[21,29.7], xdata_key='auto', ydata_key='auto', time_unit=1e-6,
                 xlim=['auto', 'auto'], xlim_scale=None, n_xticks=None, pdf=True, show_mdata=None,
                 show_yticks=False):
        self._show(self._show_time, xlabel_str=self._format_time_label('Time', time_unit), layout=layout,
                   size=size, pdf=pdf, xdata_key=xdata_key, ydata_key=ydata_key, time_unit=time_unit,
                   xlim=xlim, xlim_scale=xlim_scale, n_xticks=n_xticks, show_mdata=show_mdata,
                   show_yticks=show_yticks)



class ViewTofList(ViewList):
    def __init__(self, speclist):
        self.speclist = speclist


    def _show_idx(self, spec, ax, ydata_key='auto', xlim=['auto', 'auto'], xlim_scale=None,
                  n_xticks=None, show_mdata=None, show_pulse=True):
        ViewList._show_idx(self, spec, ax, ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale,
                           n_xticks=n_xticks, show_mdata=show_mdata)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(ms=True), fontsize=10,
                                      text_pos='right')
        spec.view._addtext_statusmarker(ax, xdata_key='idx', ydata_key=ydata_key, text_pos='left')
        if show_pulse:
            spec.view.add_plot(ax, spec.xdata['idx'], spec.ydata['rawVoltagePulse'], batch_mode=True)
        
    def _show_time(self, spec, ax, xdata_key='auto', ydata_key='auto', time_unit=1e-6,
                  xlim=['auto', 'auto'], xlim_scale=None, n_xticks=None, show_mdata=None, show_pulse=True):
        ViewList._show_time(self, spec, ax, xdata_key=xdata_key, ydata_key=ydata_key,
                   time_unit=time_unit, xlim=xlim, xlim_scale=xlim_scale, n_xticks=n_xticks,
                   show_mdata=show_mdata)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(ms=True), fontsize=10,
                                      text_pos='right')
        if show_pulse:
            spec.view.add_plot(ax, spec.xdata['time'], spec.ydata['rawVoltagePulse'], batch_mode=True)
        #spec.view._addtext_statusmarker(ax, xdata_key=xdata_key, ydata_key=ydata_key, text_pos='left')          
               


    def show_time(self, layout=[7,3], size=[21,29.7], xdata_key='auto', ydata_key='auto', time_unit=1e-6,
                 xlim=['auto', 'auto'], xlim_scale=None, n_xticks=None, pdf=True, show_mdata=None,
                 show_yticks=False, show_pulse=True):
        self._show(self._show_time, xlabel_str=self._format_time_label('Time', time_unit),
                   layout=layout, size=size, pdf=pdf, xdata_key=xdata_key, ydata_key=ydata_key,
                   time_unit=time_unit, xlim=xlim, xlim_scale=xlim_scale, n_xticks=n_xticks,
                   show_mdata=show_mdata, show_yticks=show_yticks, show_pulse=show_pulse)              
        
       


    def _show_comp_spec(self, spec, ax, comp_spec_id, linestyle='-', linewidth=0.5, **keywords):
        base_plot_map = {'tof': self._show_time,
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
                       xlim_scale=None, n_xticks=None, pdf=True, show_mdata=None, linestyle='-',
                       linewidth=0.5,):
        self._show(self._show_comp_spec, xlabel_str='TODO', comp_spec_id=comp_spec_id,
                   linestyle=linestyle, linewidth=linewidth, layout=layout, size=size, pdf=pdf,
                   xlim=xlim, xlim_scale=xlim_scale, n_xticks=n_xticks, show_mdata=show_mdata)



class ViewMsList(ViewList):
    def __init__(self, speclist):
        self.speclist = speclist
        
    def _show_idx(self, spec, ax, ydata_key='auto', xlim=['auto', 'auto'], xlim_scale=None,
                  n_xticks=None, show_mdata=None, show_ramp=True):
        key_deps = {'idx': ['voltageSpec', 'rawVoltageSpec', 'rawVoltageRamp', 'rawVoltagePulse'],}
        ViewList._show_idx(self, spec, ax, ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale,
                           n_xticks=n_xticks, show_mdata=show_mdata, key_deps=key_deps)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(ms=True), fontsize=10)
        spec.view._addtext_statusmarker(ax, xdata_key='idx', ydata_key=ydata_key, text_pos='left')
        if show_ramp:
            spec.view.add_plot(ax, spec.xdata['idx'], spec.ydata['rawVoltageRamp'], batch_mode=True)
        
    def _show_time(self, spec, ax, xdata_key='auto', ydata_key='auto', time_unit=1e-6,
                  xlim=['auto', 'auto'], xlim_scale=None, n_xticks=None, show_mdata=None, show_ramp=True):
        key_deps = {'time': ['voltageSpec', 'rawVoltageSpec', 'rawVoltageRamp', 'rawVoltagePulse'],}
        ViewList._show_time(self, spec, ax, xdata_key=xdata_key, ydata_key=ydata_key,
                   time_unit=time_unit, xlim=xlim, xlim_scale=xlim_scale, n_xticks=n_xticks,
                   show_mdata=show_mdata, key_deps=key_deps)
        spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(ms=True), fontsize=10) 
        if show_ramp:
            spec.view.add_plot(ax, spec.xdata['time'], spec.ydata['rawVoltageRamp'], batch_mode=True,
                               unit_scale=spec.view.timeunit)   
    
    
    def _show_ramp(self, spec, ax, ramp_data_key='voltageRampFitted', ydata_key='voltageSpec', xlim=['auto', 'auto'],
                   xlim_scale=None, n_xticks=None,
                   show_mdata=False, show_ytics=False, fontsize_label=12, fontsize_ref=6,
                   export=False, show_xlabel=True, show_ylabel=True, size=None,):
        spec.view.plot_ramp(ax=ax, xdata_key=ramp_data_key, ydata_key=ydata_key, xlim=xlim,
                            xlim_scale=xlim_scale, n_xticks=n_xticks,)
        spec.view._addtext_file_id(ax)
        spec.view._addtext_statusmarker(ax, xdata_key=ramp_data_key, ydata_key=ydata_key, text_pos='left')
        if show_mdata is not None:
            spec.view._addtext_info(ax, spec.view._pretty_print_info(show_mdata), fontsize=6, text_pos='right')
        
                
    def _show_ms(self, spec, ax, mass_key='diam', mass_unit=None, xlim=['auto', 'auto'], xlim_scale=None,
                 n_xticks=None, fontsize_clusterid=10, show_mdata=None):        
        spec.view.plot_ms(ax=ax, mass_key=mass_key, mass_unit=mass_unit, xlim=xlim, xlim_scale=xlim_scale,
                          n_xticks=n_xticks)
        if fontsize_clusterid:
            spec.view._addtext_cluster_id(ax, spec.view._pretty_format_clusterid(ms=True),
                                          fontsize=fontsize_clusterid)
        spec.view._addtext_file_id(ax) 
        if show_mdata is not None:
            spec.view._addtext_info(ax, spec.view._pretty_print_info(show_mdata), fontsize=6, text_pos='left')
            
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
            
                    
    def show_time(self, layout=[5,1], size=[21,29.7], xdata_key='auto', ydata_key='auto', time_unit=1e-6,
                 xlim=['auto', 'auto'], xlim_scale=None, n_xticks=None, pdf=True, show_mdata=None,
                 show_yticks=False, show_ramp=True):
        self._show(self._show_time, xlabel_str=self._format_time_label('Time', time_unit),
                   layout=layout, size=size, pdf=pdf, xdata_key=xdata_key, ydata_key=ydata_key,
                   time_unit=time_unit, xlim=xlim, xlim_scale=xlim_scale, n_xticks=n_xticks,
                   show_mdata=show_mdata, show_yticks=show_yticks, show_ramp=show_ramp)
    
    
    def show_ramp(self, layout=[5,1], size=[21,29.7], ramp_data_key='voltageRampFitted', ydata_key='voltageSpec',
                 xlim=['auto', 'auto'], xlim_scale=None, n_xticks=None, pdf=True, show_mdata=None,
                 show_yticks=False):
        self._show(self._show_ramp, xlabel_str='Ramp Voltage (V)',
                   layout=layout, size=size, pdf=pdf, ramp_data_key=ramp_data_key, ydata_key=ydata_key,
                   xlim=xlim, xlim_scale=xlim_scale, n_xticks=n_xticks,
                   show_mdata=show_mdata, show_yticks=show_yticks)
    

        
    def show_ms(self, layout=[5,1], size=[21,29.7], mass_key='diam', mass_unit=None, xlim=['auto', 'auto'],
                xlim_scale=None, n_xticks=None, pdf=True, fontsize_clusterid=10, show_mdata=None):
        if not mass_unit:
            if mass_key=='diam':
                mass_unit = 1e-9
            else:
                mass_unit = 1
        self._show(self._show_ms, xlabel_str=self._xlabel_str(mass_key, mass_unit=mass_unit), mass_key=mass_key,
                   mass_unit=mass_unit, layout=layout, size=size, pdf=pdf, xlim=xlim, xlim_scale=xlim_scale,
                   n_xticks=n_xticks, fontsize_clusterid=fontsize_clusterid, show_mdata=show_mdata)        
        
        
