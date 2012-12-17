from __future__ import unicode_literals
import matplotlib as mpl
import matplotlib.backends.backend_pdf as Pdf
import matplotlib.pyplot as plt
import scipy.constants as constants
import load
import os




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



    def show(self, specType='ebin', pdf=False):
        '''
        Takes a list of picklefile paths, and creates a 4*5 overview plot.
        '''
        specTypes = ['idx', 'tof', 'ekin', 'ebin']
        if specType not in specTypes:
            raise ValueError('specType must be one of: %s'%', '.join(specTypes))
        if pdf:
            fname = os.path.join(os.path.expanduser('~'), 'export.pdf')
            pdf_file = Pdf.PdfPages(fname)
        idx_list = [1, 5, 9, 13, 17,
                2, 6, 10, 14, 18,
                3, 7, 11, 15, 19,
                4, 8, 12, 16, 20]
        #totalplots = len(picklefilelist)
        plot_list = list(self.specList)
        plot_list.reverse()
        figidx = 1
        'TODO: clear or del remains from previous plots'
        while len(plot_list) > 0:
            # create page
            print 'Creating page', figidx
            fig = plt.figure(figidx, figsize=(0.21/constants.inch, 0.297/constants.inch))
            plt.subplots_adjust(left  = 0.05,
                                right = 0.95,
                                bottom = 0.05,
                                top = 0.95,
                                wspace = 0.15,
                                hspace = 0.2)
            plotidx = 0
            while plotidx < 20 and len(plot_list) > 0:
                #print 'Creating plot', plotidx
                row = plot_list.pop()
                #print 'type row is:', type(row)
                pf = row[5]
                currentspec = load.loadPickle(self.cfg, pf)
                currentax = fig.add_subplot(5,4,idx_list[plotidx])
                currentspec.view.plotEbin(currentax)
                currentspec.view.addTextFileId(currentax)
                currentspec.view.addTextClusterId(currentax, fontsize=16)
                #self.plotEkin(currentspec, currentax)
                self.format_overview_plot(currentax,currentspec)
                plotidx += 1
            if pdf:
                fig.savefig(pdf_file, dpi=None, facecolor='w', edgecolor='w', orientation='portrait', papertype='a4', format='pdf')
            figidx += 1
            
        pdf_file.close()
        
    def plotEkin(self, spec, ax):
        #self.ax.set_xlabel(r'E$_{kin}$ (eV)')
        #self.ax.set_ylabel('Intensity (a.u.)')
        ax.set_xlim(0,spec.photonEnergy(spec.mdata.data('waveLength')))
        ax.plot(spec.xdata['ebin'], spec.ydata['jacobyIntensity'], color='black')
        ax.relim()
        ax.autoscale(axis='y')
        ax.set_ylim(bottom=0)
        textId = ax.text(1.0, 1.01, '%s'%(os.path.basename(spec.mdata.data('datFile'))),
                                  transform = ax.transAxes, fontsize=6, horizontalalignment='right')
        #clusterLegend = '$\mathrm{\mathsf{{%s_{%s}}^{%s}}}$'%(spec.mdata.data('clusterBaseUnit'), 
        #                                                      #str(spec.mdata.data('clusterBaseUnitNumber')),
        #                                                      spec.mdata.data('ionType'))
        #ax.text(0.05, 0.8, clusterLegend, transform = ax.transAxes, fontsize=16, horizontalalignment='left')
 
        
        
    def format_overview_plot(self, ax, myspec):
          
        for tick in ax.xaxis.get_major_ticks():
            tick.tick2On=True
            tick.gridOn=True
            tick.label1On=True
            tick.label2On=False
            tick.tick1On=True
        for label in ax.xaxis.get_ticklabels():
            label.set_fontsize(7)
        #ax.text(1, 1, myspec.mdata.data('datFile'), fontsize=6,
        #          family='monospace', horizontalalignment='right',
        #         transform=ax.transAxes)
        #ax.text(.99, .92, myspec.legend, fontsize=11, weight='normal',
        #          family='sans-serif', horizontalalignment='right',
        #          verticalalignment='top', transform=ax.transAxes)
        ax.yaxis.set_major_locator(mpl.ticker.NullLocator())
        #ax.set_xlim(3.7217943154555377, 1.0)
        ax.legend_=None
        #ax.lines[0].set_color('black')
        ax.lines[0].set_linewidth(.5)
        ax.grid(linewidth=.1, linestyle=':', color='grey')

