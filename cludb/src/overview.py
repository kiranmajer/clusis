import matplotlib as mpl
import matplotlib.backends.backend_pdf as Pdf
import matplotlib.pyplot as plt
import scipy.constants as constants
import load
import os
import numpy as np




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
                spec.view._addtext_fitvalues(ax, plot_type='ebin', fontsize=9)
    
        def plot_pt_ebin_fit(spec, ax, fit_par):
            spec.view.plot_ebin(ax, xdata_key=xdata_key,
                                       ydata_key=ydata_key, xlim=xlim, xlim_scale=xlim_scale)
            spec.view.plot_energy_fit(ax, fit_par=fit_par, xdata_key=xdata_key)
            spec.view._addtext_gauge_par(ax, fit_par=fit_par, fontsize=9)            
            
             
             
             
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
            ax.lines[0].set_linewidth(.5)
            ax.grid(linewidth=.1, linestyle=':', color='grey')


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
            plt.subplots_adjust(left  = 0.05, right = 0.95, bottom = 0.05, top = 0.95,
                                wspace = 0.15, hspace = 0.2)
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
        
 
        
        


