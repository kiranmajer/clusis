from load import load_pickle
from dbshell import Db
import time
import os
import viewlist
# for comparison methods
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA
from scipy.stats import linregress
from itertools import combinations



class SpecList(object):
    '''
    Applies the methods of single spec-object to a list of spec-objects.
    '''
    def __init__(self, cfg, recTime=None, recTimeRange=None, inTags=None,
                 notInTags=None, datFileName=None, hide_trash=True, order_by='recTime'):
        self.cfg = cfg
        self.spec_type = 'generic'
        with Db('casi', self.cfg) as db:
            self.dbanswer = db.query(self.spec_type, recTime=recTime,
                                     recTimeRange=recTimeRange, inTags=inTags,
                                     notInTags=notInTags, datFileName=datFileName,
                                     hide_trash=hide_trash, order_by=order_by)
        self.pfile_list = [row['pickleFile'] for row in self.dbanswer]
        self.view = viewlist.ViewList(self)
        

#    def query(self, recTime=None, recTimeRange=None,
#              inTags=None, notInTags=None, datFileName=None):
#        with Db('casi', self.cfg) as db:
#            self.dbanswer = db.query(self.spec_type, recTime=recTime, recTimeRange=recTimeRange,
#                                     inTags=inTags, notInTags=notInTags, datFileName=datFileName)

    def get_spec(self, number):
        spec = load_pickle(self.cfg, self.dbanswer[number]['pickleFile'])
        return spec

    def update_mdata(self, mdataDict):
        'TODO: open db only once'
        for entry in self.dbanswer:
            print(entry['pickleFile'])
            cs = load_pickle(self.cfg, entry['pickleFile'])
            try:
                cs.mdata.update(mdataDict)
                if hasattr(cs, '_hv') and 'waveLength' in mdataDict.keys():
                    'TODO: better put this in mdata?'
                    cs._hv = cs._photon_energy(cs.mdata.data('waveLength'))
                    'TODO: this can seriously mix up data!'
                    cs.calc_spec_data()
            except:
                raise
            else:
                cs.commit(update=True)
                
            del cs
        
    def remove_tag(self, tag, tagkey='userTags'):
        for entry in self.dbanswer:
            cs = load_pickle(self.cfg, entry['pickleFile'])
            try:
                cs.mdata.remove_tag(tag, tagkey=tagkey)
            except ValueError:
                print('Key not applicable, skipping.')
            else:
                cs.commit(update=True)
                
            del cs
            
    def list_mdata(self, mdata_keys):
        keys = []
        if type(mdata_keys) is list:
            keys.extend(mdata_keys)
        else:
            keys.append(mdata_keys)
        print('datFile:', keys)
        print('-'*85)
        for s in self.dbanswer:
            cs = load_pickle(self.cfg, s['pickleFile'])
            values = [cs.mdata.data(k) for k in keys]
            print('{}:'.format(os.path.basename(cs.mdata.data('datFile'))), values)
            del cs
            
    def _export(self, fname='export.pdf', export_dir=os.path.expanduser('~'), size='p1h',
                figure=None, twin_axes=True):
        if export_dir.startswith('~'):
            export_dir = os.path.expanduser(export_dir)
        f = os.path.join(export_dir, fname)
        'TODO: presets are mere personal. For a general approach probably not suitable.'
        presets = {'p1': [14, 14*3/7],
                   'p1h': [14, 9],
                   'p2': [7, 7*5/7],
                   'p3': [4.8, 4.8*5/6]}
        if isinstance(size, str) and size in presets.keys():
            size = presets[size]
        w = size[0]/2.54
        h = size[1]/2.54
        #orig_size = self.fig.get_size_inches()
        if figure is None:
            figure = self.fig
        figure.set_size_inches(w,h)
        'TODO: hard coded margins are not a good idea.'
        if twin_axes:
            figure.subplots_adjust(left=0.09, bottom=0.088, right=0.995, top=0.905)
        else:
            figure.subplots_adjust(left=0.08, bottom=0.095, right=0.995, top=0.98)
        figure.savefig(f)
        #self.fig.set_size_inches(orig_size)
        
    def remove_spec(self):
        'TODO: query for confirmation, since you can cause great damage.'
        for entry in self.dbanswer:
            cs = load_pickle(self.cfg, entry['pickleFile'])
            cs.remove()
            del cs      
            
    def export_single_plots(self, plot_fct, export_dir='~/test', latex_fname=None, overwrite=True, 
                            linewidth=.8, layout=[8,4], size='latex', latex=True, firstpage_offset=0,
                            xlabel_str='Binding energy (eV)', skip_plots=False, **keywords):
        export_fnames = []
        total_plots = len(self.pfile_list)
        #print('number of spec to export:', total_plots)
        rows = layout[0]
        col = layout[1]
        if isinstance(size, str) and size=='latex':
            page_width = 14.576
            page_height = 20.7
            size = [page_width/col, page_height/rows]
        for si in range(total_plots):
            cs = self.get_spec(si)
            if not skip_plots:
                getattr(cs.view, plot_fct)(export=True, **keywords)
            if 'comp' in plot_fct:
                fname = '{}{}{}_{}.pdf'.format(cs.mdata.data('clusterBaseUnit'),
                                             cs.mdata.data('clusterBaseUnitNumber'),
                                             'comp',
                                             os.path.splitext(os.path.basename(cs.mdata.data('datFile')))[0])
            else:
                fname = '{}{}_{}.pdf'.format(cs.mdata.data('clusterBaseUnit'),
                                             cs.mdata.data('clusterBaseUnitNumber'),
                                            os.path.splitext(os.path.basename(cs.mdata.data('datFile')))[0])
            if not skip_plots:
                print('Exporting {} ...'.format(fname))
                cs.view.export(fname=fname, export_dir=export_dir, size=size, overwrite=overwrite,
                               linewidth=linewidth)
                plt.close(plt.gcf())
            export_fnames.append(fname)
        #print('number of fnames to export:', len(export_fnames))
            
        'latex output equivalent to the viewlist pdf export'
        'TODO: could be made more elegant; remove hard coded numbers.'
        if latex:
            if not latex_fname:
                latex_fname = '{}-{}.tex'.format(os.path.splitext(export_fnames[0])[0],
                                                 os.path.splitext(export_fnames[-1])[0])
            latex_fullpath = os.path.join(os.path.expanduser(export_dir), latex_fname)       
            plotcount = 0
            pagecount = 0
            fnames = export_fnames[:]
            print('Writing latex file to "{}" ...'.format(latex_fname))
            with open(latex_fullpath, mode='w', encoding='utf-8') as lf:
                while plotcount < total_plots:
                    # start new page
                    print('Generating page', pagecount + 1)
                    #print('{} plots of {} finished'.format(plotcount, total_plots))
                    if pagecount:
                        rows = layout[0]
                        ppp = rows*col
                        lf.write('\\newpage\n')
                    else:
                        rows -= firstpage_offset
                        ppp = rows*col
                    #lf.write('\\begin{center}\n')
                    fname_idx = np.arange(0,ppp).reshape(col,rows).transpose().reshape(ppp)
                    plotidx = 0
                    label_col = 1
                    use_raisebox = False
                    row_idx = 0
#                     while plotidx < ppp and plotcount < total_plots:
#                         row_idx = 0
                    while row_idx < rows and plotcount < total_plots:
                        # start new row
                        if row_idx:
                            lf.write('\\newline\n')
                        else:
                            lf.write('\\noindent\n')
                        #lf.write('% line {}\n'.format(row_idx + 1))
                        col_idx = 0
                        while col_idx < col:
                            # start new col
                            if fname_idx[plotidx] < len(fnames):
                                lf.write('\\includegraphics{{{}}}\n'.format(fnames[fname_idx[plotidx]]))
                                plotcount += 1
                                label_col = col_idx + 1
                                #print('added plot', plotcount)
                            elif fname_idx[plotidx] == len(fnames) and row_idx > 0 and col_idx > 0:
                                raisebox_raise = size[1] - 0.18
                                lf.write('\\raisebox{{{}cm}}[0cm][0cm]{{\\makebox[{}cm]{{\\textsf{{\\scriptsize {}}}}}}}\n'.format(raisebox_raise, page_width/col, xlabel_str))
                                label_col = col_idx
                                use_raisebox = True
                            else:
                                lf.write('\\makebox[{}cm]{{}}\n'.format(page_width/col))
                            col_idx += 1
                            plotidx += 1
                        row_idx += 1
                    lf.write('\\\\*[-3mm]\n')
                    #print('added {} of {} plots per page'.format(plotcount, ppp))
                    if not use_raisebox and ((plotcount - (rows - firstpage_offset)*col)%plotidx == 0 or
                                              plotcount%plotidx == 0):
                        label_col = col
                    for c in range(label_col):
                        lf.write('\\makebox[{}cm]{{\\textsf{{\\scriptsize {}}}}}\n'.format(page_width/col, xlabel_str))
                    #lf.write('\\end{center}\n')
                    pagecount += 1
                    fnames = export_fnames[plotcount:]
                    #print('number of remaining fnames:', len(fnames))


class SpecPeList(SpecList):
    def __init__(self, cfg, clusterBaseUnit=None, clusterBaseUnitNumber=None,
                 clusterBaseUnitNumberRange=None, recTime=None, recTimeRange=None,
                 inTags=None, notInTags=None, datFileName=None, waveLength=None, trapTemp=None,
                 trapTempRange=None, hide_trash=True, order_by='recTime'):
        self.cfg = cfg
        self.spec_type = 'pes'
        with Db('casi', self.cfg) as db:
            self.dbanswer = db.query(self.spec_type, clusterBaseUnit=clusterBaseUnit,
                                     clusterBaseUnitNumber=clusterBaseUnitNumber,
                                     clusterBaseUnitNumberRange=clusterBaseUnitNumberRange,
                                     recTime=recTime, recTimeRange=recTimeRange, inTags=inTags,
                                     notInTags=notInTags, datFileName=datFileName,
                                     waveLength=waveLength, trapTemp=trapTemp,
                                     trapTempRange=trapTempRange,
                                     hide_trash=hide_trash, order_by=order_by)
        self.pfile_list = [row['pickleFile'] for row in self.dbanswer]
        self.view = viewlist.ViewPesList(self)
        
        
    def gauge(self, gauge_ref=None, ignore_wavelength=False):
        '''
        Gauge all spectra in list with gauge_ref or
        re-gauge them with their previous gauge_ref.
        '''
        for s in self.dbanswer:
            cs = load_pickle(self.cfg, s['pickleFile'])
            if gauge_ref is not None:
                cs.gauge(gauge_ref, ignore_wavelength=ignore_wavelength)
            elif 'gaugeRef' in cs.mdata.data().keys():
                cs.gauge(cs.mdata.data('gaugeRef'), ignore_wavelength=ignore_wavelength)
            else:
                print('Spec has no gauge reference yet; skipping.')
            
            del cs


    def plot_ea(self, return_data=False, fontsize_label=12):
        fig = plt.figure()
        #print 'Figure created.'
        ax = fig.add_subplot(1,1,1)
        ax.set_xlabel('cluster size (#)', fontsize=fontsize_label)
        ax.set_ylabel('electron affinity (eV)', fontsize=fontsize_label)
        ax.tick_params(labelsize=fontsize_label)
        ax.grid()
        csize = []
        ea = []
        for s in self.dbanswer:
            cs = load_pickle(self.cfg,s[str('pickleFile')])
            if 'electronAffinity' in cs.mdata.data().keys():
                csize.append(cs.mdata.data('clusterBaseUnitNumber'))
                ea.append(cs.mdata.data('electronAffinity'))
            else:
                print('Spec has no value for electron affinity. Skipping.')
                
        ax.plot(csize, ea)
                
        #ax.legend(loc=2)
        fig.show()
        if return_data:
            return csize, ea



class SpecPePtList(SpecPeList):
    def __init__(self, cfg, clusterBaseUnitNumber=None, recTime=None, recTimeRange=None,
                 inTags=None, notInTags=None, datFileName=None, waveLength=None,
                 hide_trash=True, order_by='recTime'):
        SpecPeList.__init__(self, cfg, clusterBaseUnit='Pt', clusterBaseUnitNumber=clusterBaseUnitNumber,
                            recTime=recTime, recTimeRange=recTimeRange, inTags=inTags,
                                     notInTags=notInTags, datFileName=datFileName,
                                     waveLength=waveLength, hide_trash=hide_trash, order_by=order_by)
        self.view = viewlist.ViewPesList(self)
        
    def gauge(self):
        '''Overwrites inherited gauge method.'''
        raise ValueError('gauge() is not applicable for a pt pes list.')



class SpecPePtFitList(SpecPeList):
    def __init__(self, cfg, clusterBaseUnitNumber=None, recTime=None, recTimeRange=None,
                 inTags=None, notInTags=None, datFileName=None, waveLength=None,
                 hide_trash=True, order_by='recTime'):
        inTags_list = []
        if inTags is not None:
            if type(inTags) is str:
                inTags_list.append(inTags)
            else:
                inTags_list.extend(inTags)
        if not 'fitted' in inTags_list:
            inTags_list.append('fitted')       
        notInTags_list = []
        if notInTags is not None:
            if type(notInTags) is str:
                notInTags_list.append(notInTags)
            else:
                notInTags_list.extend(notInTags)
        if not 'background' in notInTags_list:
            notInTags_list.append('background')
        SpecPePtList.__init__(self, cfg, clusterBaseUnitNumber=clusterBaseUnitNumber, 
                              recTime=recTime, recTimeRange=recTimeRange, inTags=inTags_list,
                              notInTags=notInTags_list, datFileName=datFileName,
                              waveLength=waveLength, hide_trash=hide_trash, order_by=order_by)
        self.view = viewlist.ViewPtFitList(self)


    def list_fit_par(self):
        def format_recTime(unixtime):
            return time.strftime('%d.%m.%Y', time.localtime(unixtime))
        
        def format_datFile(datfile):
            return os.path.basename(datfile)
        
        items = ['recTime', 'datFile', 'fitPar', 'flightLength']
        mdataList = []
        rowCount = 0
        for s in self.dbanswer:
            cs = load_pickle(self.cfg,s[str('pickleFile')])
            'TODO: cant we remove the if clause?' 
            if cs.mdata.data('specTypeClass') == 'specPePt' and \
            'background' not in cs.mdata.data('systemTags') and \
            'fitted' in cs.mdata.data('systemTags'):
                mdataList.append([])
                for key in items:
                    mdataList[rowCount].append(cs.mdata.data(key))
                rowCount += 1
            else:
                print('{} not a fitted Pt-Spec, skipping.'.format(cs.mdata.data('datFile')))              
            #print cs.mdata.data('datFile'), cs.mdata.data('recTime'), cs.mdata.data('fitParTof')[-1]
            del cs
        
        print('recTime'.ljust(10+3), end=' ')
        print('datFile'.ljust(13+3), end=' ')
        print('l_scale'.ljust(7+3), end=' ')
        print('delta_l [mm]'.ljust(12+3), end=' ')
        print('t_off [ns]'.ljust(10+3), end=' ')
        print('E_off [meV]'.ljust(6))
        lastDate = ''
        for row in mdataList:
            if not format_recTime(row[0]) == lastDate:
                print('-'*85)
            print(format_recTime(row[0]).ljust(10+3), end=' ')
            print(format_datFile(row[1]).ljust(13+3), end=' ')
            print(str(round(row[2][-1],3)).ljust(7+3), end=' ')
            print(str(round(row[3]*1e3*(1/np.sqrt(row[2][-1])-1),3)).ljust(12+3), end=' ')
            print(str(round(row[2][-2]*1e9,2)).ljust(10+3), end=' ')
            print(str(round(row[2][-3]*1e3,2)).ljust(6))
            lastDate = format_recTime(row[0])
            
            
    def plot_fit_par(self, var='time', max_tof=10e-6, fontsize_label=12, fname=None, export_dir='~',
                     legend_pos='r', ymax=20, stepsize=5, hv=6):
        
        lpar = {'fig_hscale':{'r': 2.25, 'b': 2},
                'margins': {'r': [.08, .07, .66, .98], # [left, bottom, right, top]
                            'b': [.08, .48, .98, .98]},
                'legend_anchor': {'r': (1.04, 1), 'b': (.47, -.2)},
                'legend_loc': {'r':2, 'b': 9},
                'legend_col': {'r': 1, 'b': 3}}
        if export_dir.startswith('~'):
            export_dir = os.path.expanduser(export_dir)
        if fname:
            if not os.path.isdir(export_dir):
                os.makedirs(export_dir, exist_ok=False)
            f = os.path.join(export_dir, fname)
        fig = plt.figure()
        #print 'Figure created.'
        ax1 = fig.add_subplot(2,1,1)
        ax1.tick_params(labelsize=fontsize_label)
        ax1.grid()
        axes_max = [max_tof*1e6, ymax]
        ax1.set_xlim(0, axes_max[0])
        ax1.set_ylim(0,axes_max[1])
        ax1.xaxis.set_ticks(np.arange(0, axes_max[0]+stepsize/2, stepsize))
        ax1.yaxis.set_ticks(np.arange(0, axes_max[1]+stepsize/2, stepsize))
        ax2 = fig.add_subplot(2,1,2)
        ax2.tick_params(labelsize=fontsize_label)
        ax2.grid()
        axes_max = [max_tof*1e6, hv]
        ax2.set_xlim(0, axes_max[0])
        ax2.set_ylim(0,axes_max[1])
        ax2.xaxis.set_ticks(np.arange(0, axes_max[0]+stepsize/2, stepsize))
        ax2.yaxis.set_ticks(np.arange(0, axes_max[1]+stepsize/2, stepsize))
        fig.subplots_adjust(left=lpar['margins'][legend_pos][0],
                            bottom=lpar['margins'][legend_pos][1], 
                            right=lpar['margins'][legend_pos][2],
                            top=lpar['margins'][legend_pos][3],
                            hspace=0.17)
        fig.set_size_inches(14/2.54, lpar['fig_hscale'][legend_pos]*(18*3/7)/2.54)
        fx=np.arange(1e-9, max_tof+1e-7, 1e-7)
        def g_time(xdata, lscale, Eoff, toff, pFactor):
            return 1/np.sqrt(lscale*(1/(xdata)**2 - Eoff/pFactor)) - toff 
        #Ex=np.arange(0, 6, 1e-7)
        def E_t(xdata, pFactor):
            return pFactor/xdata**2
        def E_cal(xdata, lscale, Eoff, toff, pFactor):
            return pFactor/(lscale*(xdata - toff)**2) - Eoff
        def colormap(rec_date):
            if rec_date < time.mktime(time.strptime('01.2008', '%m.%Y')):
                color = 'black'
            elif time.mktime(time.strptime('01.2008', '%m.%Y')) < rec_date < time.mktime(time.strptime('01.2009', '%m.%Y')):
                color = 'blue'
            elif time.mktime(time.strptime('01.2011', '%m.%Y')) < rec_date < time.mktime(time.strptime('28.02.2012', '%d.%m.%Y')):
                color = 'grey'
            elif time.mktime(time.strptime('28.02.2012', '%d.%m.%Y')) < rec_date < time.mktime(time.strptime('01.2013', '%m.%Y')):
                color = 'green'
            else:
                color = 'red'
            return color
        
        for s in self.dbanswer:
            cs = load_pickle(self.cfg,s[str('pickleFile')])
            if cs.mdata.data('specTypeClass') == 'specPePt' and \
            'background' not in cs.mdata.data('systemTags') and \
            'fitted' in cs.mdata.data('systemTags'):
                lscale = cs.mdata.data('fitPar')[-1]
                toff = cs.mdata.data('fitPar')[-2]
                Eoff = cs.mdata.data('fitPar')[-3]
                dat_filename = os.path.basename(cs.mdata.data('datFile')).strip('.dat')
                #if var == 'time':
                ax1.plot(fx*1e6, g_time(fx, lscale, Eoff, toff, cs._pFactor)*1e6,
                        label='{}: $E_{{off}}={:.1f}$'.format(dat_filename, Eoff*1000),
                        color=colormap(cs.mdata.data('recTime')))
                #ylabel = 'calibrated tof ($\mu$s)'
                #elif var == 'energy':
                ax2.plot(fx*1e6, hv - E_cal(fx, lscale, Eoff, toff, cs._pFactor),
                        label='{}: $E_{{off}}={:.1f}$'.format(dat_filename, Eoff*1000),
                        color=colormap(cs.mdata.data('recTime')))
                #ylabel = 'calibrated binding energy (eV)'
#                 else:
#                     raise ValueError('var must be one of: "time", "energy".')
        
        ax1.set_xlabel('measured tof ($\mu$s)', fontsize=fontsize_label)
        ax1.set_ylabel('calibrated tof ($\mu$s)', fontsize=fontsize_label)
        ax2.set_xlabel('measured tof ($\mu$s)', fontsize=fontsize_label)
        ax2.set_ylabel('calibrated binding energy (eV)', fontsize=fontsize_label) 
        leg = ax1.legend(bbox_to_anchor=lpar['legend_anchor'][legend_pos],
                        loc=lpar['legend_loc'][legend_pos], borderaxespad=0.,
                        ncol=lpar['legend_col'][legend_pos], fontsize=fontsize_label)
        for legobj in leg.legendHandles:
            legobj.set_linewidth(4)
        if fname:
            fig.savefig(f)
        else:
            fig.show()            


    def regauge(self, rel_y_min=None, cutoff=None):
        for s in self.dbanswer:
            cs = load_pickle(self.cfg,s[str('pickleFile')])
            cs._regauge(rel_y_min=rel_y_min, cutoff=cutoff)
            cs.commit()
            del cs
            


class SpecPeWaterList(SpecPeList):
    def __init__(self, cfg, clusterBaseUnitNumber=None, clusterBaseUnitNumberRange=None,
                 recTime=None, recTimeRange=None, inTags=None, notInTags=None,
                 datFileName=None, waveLength=None, trapTemp=None,
                 trapTempRange=None, hide_trash=True, order_by='recTime', heavy_water=False):
        water_type = 'H2O'
        if heavy_water:
            water_type = 'D2O'
        SpecPeList.__init__(self, cfg, clusterBaseUnit=water_type, clusterBaseUnitNumber=clusterBaseUnitNumber,
                            clusterBaseUnitNumberRange=clusterBaseUnitNumberRange,
                            recTime=recTime, recTimeRange=recTimeRange, inTags=inTags,
                            notInTags=notInTags, datFileName=datFileName,
                            waveLength=waveLength, trapTemp=trapTemp,
                            trapTempRange=trapTempRange, hide_trash=hide_trash, order_by=order_by)
        self.view = viewlist.ViewPesList(self)
        
    def gauge(self, gauge_ref=None, refit=None, ignore_wavelength=False):
        '''
        Gauge all spectra in list with gauge_ref or
        re-gauge them with their previous gauge_ref.
        '''
        for s in self.dbanswer:
            cs = load_pickle(self.cfg, s['pickleFile'])
            if gauge_ref is not None:
                cs.gauge(gauge_ref, refit=refit, ignore_wavelength=ignore_wavelength)
            elif 'gaugeRef' in cs.mdata.data().keys():
                cs.gauge(cs.mdata.data('gaugeRef'), refit=refit, ignore_wavelength=ignore_wavelength)
            else:
                print('Spec has no gauge reference yet; skipping.')
            
            del cs
        
    def fit(self, fit_par, fit_id='default_fit', cutoff=None):
        for s in self.dbanswer:
            cs = load_pickle(self.cfg,s[str('pickleFile')])
            cs.fit(fitPar0=fit_par, fit_id=fit_id, cutoff=cutoff)
            cs.commit()
            del cs


class SpecPeWaterFitList(SpecPeWaterList):
    def __init__(self, cfg, clusterBaseUnitNumber=None, clusterBaseUnitNumberRange=None,
                 recTime=None, recTimeRange=None, inTags=None, notInTags=None,
                 datFileName=None, waveLength=None, trapTemp=None, trapTempRange=None,
                 hide_trash=True, order_by='recTime', heavy_water=False, fit_id='default_fit'):
        '''
        Creates a water fit list of spectra with certain fit id.
        fit_id: A valid fit id or None (in which case all fitted spectra are included. However some
                list methods work only, if fit_id is specified).
        '''
        self.heavy_water = heavy_water
        self.fit_id = fit_id
        inTags_list = []
        if inTags is not None:
            if type(inTags) is str:
                inTags_list.append(inTags)
            else:
                inTags_list.extend(inTags)
        if not 'fitted' in inTags_list:
            inTags_list.append('fitted')
        if self.fit_id and self.fit_id not in inTags_list:
            inTags_list.append(self.fit_id)  
        notInTags_list = []
        if notInTags is not None:
            if type(notInTags) is str:
                notInTags_list.append(notInTags)
            else:
                notInTags_list.extend(notInTags)
        if not 'background' in notInTags_list:
            notInTags_list.append('background')
        SpecPeWaterList.__init__(self, cfg, clusterBaseUnitNumber=clusterBaseUnitNumber,
                                 clusterBaseUnitNumberRange=clusterBaseUnitNumberRange,
                                 recTime=recTime, recTimeRange=recTimeRange, inTags=inTags_list,
                                 notInTags=notInTags_list, datFileName=datFileName,
                                 waveLength=waveLength, trapTemp=trapTemp,
                                 trapTempRange=trapTempRange, hide_trash=hide_trash, order_by=order_by,
                                 heavy_water=heavy_water)
        self.view = viewlist.ViewWaterFitList(self)
        
    def _eval_fit_id(self):
        if not self.fit_id:
            raise ValueError('No fit id specified. Create a water fit list with a fit id.')
        else:
            return self.fit_id

    def list_fit_par(self):
        fit_id = self._eval_fit_id()
            
        def format_recTime(unixtime):
            return time.strftime('%d.%m.%Y', time.localtime(unixtime))
        
        def format_datFile(datfile):
            return os.path.basename(datfile)
        
        def format_fitpeaks(peaklist):
            return ', '.join(str(e) for e in peaklist)
        
        
        items = ['clusterBaseUnitNumber', 'waveLength', 'recTime', 'cutoff', 'info', 'par']
        mdataList = []
        rowCount = 0
        for s in self.dbanswer:
            cs = load_pickle(self.cfg,s[str('pickleFile')])
            'TODO: cant we remove the if clause?'
            if cs.mdata.data('specTypeClass') == 'specPeWater' and \
            'background' not in cs.mdata.data('systemTags') and \
            'fitted' in cs.mdata.data('systemTags'):
                mdataList.append([])
                for key in items:
                    if key == 'par':
                        mdataList[rowCount].append([round(float(cs.ebin(p)),2) for p in cs.mdata.data('fitData')[fit_id][key][:-2:2]])
                        #mdataList[rowCount].append(round(np.sum(cs.mdata.data(key)[-2:]), 3))
                        mdataList[rowCount].append(round(cs._get_peak_width(key, fit_id), 3))
                        mdataList[rowCount].append(round(cs.mdata.data('fitData')[fit_id][key][-2], 3))
                        mdataList[rowCount].append(round(cs.mdata.data('fitData')[fit_id][key][-1], 3))
                    elif key in ['info']:
                        mdataList[rowCount].append(cs.mdata.data('fitData')[fit_id][key][0])
                    elif key in ['cutoff']:
                        mdataList[rowCount].append(cs.mdata.data('fitData')[fit_id][key])
                    else:
                        mdataList[rowCount].append(cs.mdata.data(key))
                rowCount += 1
            else:
                print('{} not a fitted Water-Spec, skipping'.format(cs.mdata.data('datFile')))              
            #print cs.mdata.data('datFile'), cs.mdata.data('recTime'), cs.mdata.data('fitParTof')[-1]
            del cs
        
        print('size'.ljust(4+3),
              'lambda'.ljust(6+3),
              'recTime'.ljust(10+3),
              'cutoff'.ljust(6+3),
              'chi2*1e3'.ljust(7+3),
              'fwhm'.ljust(5+3),
              's_g'.ljust(5+3),
              's_l'.ljust(5+3),
              'Ebin of peaks [eV]')
        last_size = 0
        for row in mdataList:
            if not row[0] == last_size:
                print('-'*101)
            print(str(row[0]).ljust(4+3), 
                  str(round(row[1]*1e9)).ljust(6+3),
                  format_recTime(row[2]).ljust(10+3), end=' ')
            if row[3] is None:
                print('None'.ljust(6+3), end=' ')
            else:                                       
                print(str(round(row[3]*1e6, 2)).ljust(6+3), end=' ')
            print(str(round(row[4]*1e3, 3)).ljust(7+3),
                  str(row[6]).ljust(5+3),
                  str(row[7]).ljust(5+3),
                  str(row[8]).ljust(5+3),
                  format_fitpeaks(row[5]))
            last_size = row[0]
            

    def load_comp_data(self, dat_file_list):
        comp_data = {}
        for dat_file in dat_file_list:
            with open(dat_file, 'rb') as f:
                x,y = np.loadtxt(f, unpack=True)
            legend = os.path.splitext(os.path.basename(dat_file))[0]
            comp_data[legend] = [x, y]
        return comp_data

        
    def __iso_border(self, lpar, inv_size):
        border = None
        i = 1
        while i < len(lpar) and inv_size:
            if inv_size >= lpar[i][0]:
                border = (lpar[i][1] - lpar[i-1][1])/np.abs(lpar[i][0] - lpar[i-1][0])*(inv_size - lpar[i-1][0]) - lpar[i-1][1]
                inv_size = None
                i += 1
            else:
                i += 1
                 
        if not border:
            i -= 1
            border = (lpar[i][1] - lpar[i-1][1])/np.abs(lpar[i][0] - lpar[i-1][0])*(inv_size - lpar[i-1][0]) - lpar[i-1][1]
         
        return border

    
    def _sort_peaks(self, size, linpar, peak_list, p_2, p_1a, p_1b, p_vib):
        for p in peak_list:
            if -1*p > self.__iso_border(linpar['2'], size**(-1/3)):
                p_2.append([size, p])
                #print('p_2:', p_2)
            elif self.__iso_border(linpar['2'], size**(-1/3)) >= -1*p > self.__iso_border(linpar['1a'], size**(-1/3)):
                p_1a.append([size, p])
                #print('p_1a:', p_1a)
            elif self.__iso_border(linpar['1a'], size**(-1/3)) >= -1*p > self.__iso_border(linpar['1b'], size**(-1/3)):
                p_1b.append([size, p])
                #print('p_1b:', p_1b)
            else:
                p_vib.append([size, p])
                #print('p_vib:', p_vib)


    def compare_water_fits(self, plot_iso_borders=False, comp_data=None, cutoff=None,
                           mark_iso=True, fname=None, export_dir=os.path.expanduser('~'),
                           size=[20,14], fontsize_label=12, markersize=6, xlim=[0,0.42],
                           ylim=[-4,0], ax2_ticks=[10, 20,40,80,150,350,1000, 5000], color=None,
                           color_comp_data=None, show_own_data_legend=False):
        
        fit_id = self._eval_fit_id()
        
        if self.heavy_water:
#             linpar = self.cfg.d2o_isoborder_linpar
            linpar = self.cfg.water_isomer_limits['D2O']
        else:
#             linpar = self.cfg.h2o_isoborder_linpar
            linpar = self.cfg.water_isomer_limits['H2O']
        
         
        if color is None:
            color = ['indigo', 'limegreen', 'blue', 'red']
        if mark_iso:
            leg_label = ['Isomer II', 'Isomer Ia', 'Isomer Ib', 'Vibrational']
        else:
            leg_label = ['Single GL Fit']
        if color_comp_data is None:
            color_comp_data = ['lightblue', 'whitesmoke', 'black', 'yellow', 'violet', 'grey', 'navy']
                         
        def plot_comp(plot_data, fit_par, fit_res, cutoff, fontsize_label, markersize,
                      xlim, ylim, ax2_ticks, comp_data=None):
            fig = plt.figure()
            # setup lower axis
            ax = host_subplot(111, axes_class=AA.Axes)
            ax.set_xlabel('n$^{-1/3}$')
            ax.axis['bottom'].label.set_fontsize(fontsize_label)
            ax.set_xlim(xlim[0], xlim[1])
            ax.set_ylabel('-VDE (eV)')
            ax.axis['left'].label.set_fontsize(fontsize_label)
            ax.axis['bottom'].major_ticklabels.set_fontsize(fontsize_label)
            ax.axis['left'].major_ticklabels.set_fontsize(fontsize_label)
            ax.set_ylim(ylim[0], ylim[1])
            # setup upper axis
            ax2 = ax.twin()
            ax2.set_xticks(np.array(ax2_ticks)**(-1/3))
            ax2.set_xticklabels([str(t) for t in ax2_ticks])
            ax2.set_xlabel('number of water molecules (n)')
            ax2.axis['top'].label.set_fontsize(fontsize_label)
            ax2.axis['top'].major_ticklabels.set_fontsize(fontsize_label)
            ax2.axis["right"].major_ticklabels.set_visible(False)
            ax2.grid(b=True)
            # write fit values
            if len(fit_par) > 0:
                if cutoff is None:
                    ex_str = 'Extrapolation to bulk:'
                else:
                    ex_str = 'Extrapolation to bulk (from size {}):'.format(cutoff)
                i = 0
                for par_set in fit_par:
                    if i == 1:
                        ex_str = ex_str.replace('Extrapolation', 'Extrapolations')
                    res_set = fit_res[i]
                    i += 1
                    ex_str += '\n{:.2f}$\pm${:.2f}eV'.format(par_set[1], res_set[1])
                bbox_props = {'boxstyle': 'square', 'facecolor': 'white'} 
                # TODO: text position relative to axis?
                ax.text(0.015, -0.2 + ylim[1], ex_str, verticalalignment='top', fontsize=fontsize_label,
                        bbox=bbox_props)
            # plot data
            idx = 0
            own_data = []
            for peak_set in plot_data:
                # mind the ',' after ods, because plot returns a list
                ods, = ax.plot(peak_set[2], peak_set[1], 's', markersize=markersize, color=color[idx],
                        label=leg_label[idx])
                own_data.append(ods)
                idx += 1
            # optionally add legend for our data points
            if show_own_data_legend and not comp_data:
                # handles argument requires matplotlib >= 1.4(.2)
                own_legend = plt.legend(handles=own_data, loc=4, fontsize=fontsize_label, numpoints=1)
                ax.add_artist(own_legend)
            # plot comparison data
            if comp_data is not None:
                idx = 0
                ext_data = []
                for key, peak_set in sorted(comp_data.items()):
#                     if idx < 4:
#                         marker ='o'
#                     else:
#                         marker='D'
                    # TODO: this is shoulden't be hard coded
                    label = {'bowen_iso1_table': 'Isomer I (Bowen)',
                             'bowen_iso1_stretch': 'Vibrational (Bowen)',
                             'neumark_iso1': 'Isomer I (Neumark)',
                             'neumark_iso1_high_press': 'Isomer I [Ne] (Neumark)',
                             'neumark_iso2': 'Isomer II (Neumark)',
                             'neumark_iso3': 'Isomer III (Neumark)',
                             'water_jets': 'Water jets (several)'
                             }
                    eds, = ax.plot(peak_set[0], -1*peak_set[1], 'o', label=label[key], markersize=markersize,
                            color=color_comp_data[idx])
                    ext_data.append(eds)
                    idx += 1
                ax.legend(handles=ext_data, loc=4, fontsize=fontsize_label, numpoints=1)
            # plot fits
            c = 0.5
            if cutoff is not None:
                c = cutoff**(-1/3)            
            for par_set in fit_par:
                lin_fit = np.poly1d(par_set)
                ax.plot([xlim[0], c], lin_fit([xlim[0], c]), '-', color='grey')
                ax.plot([c, xlim[1]], lin_fit([c, xlim[1]]), '--', color='grey')
            # plot borders for isomer classification
            if plot_iso_borders:
                for par in linpar.values():
                    s = [p[0] for p in par]
                    s[0] = 0.5
                    s[-1] = 1e-7
                    ax.plot(s, [self.__iso_border(par, y) for y in s], color='black')
                    ax.plot([p[0] for p in par], [-p[1] for p in par], 'D', color='black')
            if fname is None:
                fig.show()
            else:
                self._export(fname, export_dir, size, figure=fig)
                 
                          
        # main method
        p_2 = []
        p_1a = []
        p_1b = []
        p_vib = []
        for s in self.dbanswer:
            cs = load_pickle(self.cfg,s[str('pickleFile')])
            peak_list = [cs.ebin(p) for p in cs.mdata.data('fitData')[fit_id]['par'][:-2:2]]
            if mark_iso:
                self._sort_peaks(cs.mdata.data('clusterBaseUnitNumber'), linpar, peak_list, p_2, p_1a, p_1b, p_vib)
            else:
                for p in peak_list:
                    p_1b.append([cs.mdata.data('clusterBaseUnitNumber'), p])
            del cs
         
        #print('p_* are:', p_2, p_1a, p_1b, p_vib)
        plot_data = [ps for ps in [p_2, p_1a, p_1b, p_vib] if len(ps) > 0]
        plot_data = [np.array(ps).transpose() for ps in plot_data]
        plot_data = [np.vstack((ps, ps[0]**(-1/3))) for ps in plot_data]
        for ps in plot_data:
            ps[1] = ps[1]*-1
        #print('plot_data:', plot_data)
        if cutoff is not None:
            f_data = []
            for peak_set in plot_data:
                b = peak_set[0] >= cutoff
                peak_set = np.array([peak_set[0][b],peak_set[1][b],peak_set[2][b]])
                if len(peak_set) == 3:
                    f_data.append(peak_set)
        else:
            f_data = plot_data
        fit_data = [ps for ps in f_data if len(ps[0]) > 1 and np.abs(ps[0][0]-ps[0][-1]) > 20]
        #print('fit_data:', fit_data)
         
        # linear fit
        fit_par = []
        fit_res = []
        for peak_set in fit_data:
#             slope, intercept, r_value, p_value, std_err = linregress(peak_set[2], peak_set[1])
#             fit_par.append(np.array([slope, intercept]))
#             fit_res.append(std_err)            
            fitpar, cov = np.polyfit(peak_set[2], peak_set[1], 1, cov=True)
            fit_par.append(fitpar)
            res=np.sqrt(np.diag(cov))
            fit_res.append(res)
 
             
        plot_comp(plot_data, fit_par, fit_res, cutoff, fontsize_label=fontsize_label,
                  markersize=markersize, xlim=xlim, ylim=ylim, ax2_ticks=ax2_ticks,
                  comp_data=comp_data)
        return fit_par, fit_res


    def compare_peak_widths(self, fname=None, export_dir=os.path.expanduser('~'),
                            size=[20,14], fontsize_label=12, markersize=6, color=None):
        
        fit_id = self._eval_fit_id()
        
        widths = {1: [], 2: [], 3: [], 4: []}
        for s in self.dbanswer:
            cs = load_pickle(self.cfg,s[str('pickleFile')])
            csize = cs.mdata.data('clusterBaseUnitNumber')
            #width = np.sum(cs.mdata.data('fitPar')[-2:])
            width = cs._get_peak_width('par', fit_id)
            peak_n = (len(cs.mdata.data('fitData')[fit_id]['par']) -2)/2
            if 0.1 < width < 1.5:
                widths[peak_n].append([csize, width])
            del cs
        plot_data = {}
        for k,v in widths.items():
            if len(v) > 0:
                plot_data[k] = np.transpose(v)
        #xdata = plot_data[0]**(-1/3)
        
        if color is None:
            color = ['blue', 'grey', 'limegreen', 'red']
        # create plot
        fig = plt.figure()
        # setup lower axis
        ax = host_subplot(111, axes_class=AA.Axes)
        ax.set_xlabel('n$^{-1/3}$')
        ax.axis['bottom'].label.set_fontsize(fontsize_label)
        ax.set_xlim(0,0.42)
        ax.set_ylabel('fwhm (eV)')
        ax.axis['left'].label.set_fontsize(fontsize_label)
        ax.axis['bottom'].major_ticklabels.set_fontsize(fontsize_label)
        ax.axis['left'].major_ticklabels.set_fontsize(fontsize_label)
        ax.set_ylim(0,1.3)
        # setup upper axis
        ax2 = ax.twin()
        ax2.set_xticks(np.array([10, 20,40,80,150,350,1000, 5000])**(-1/3))
        ax2.set_xticklabels(["10","20","40","80","150","350","1000","5000"])
        ax2.set_xlabel('number of water molecules (n)')
        ax2.axis['top'].label.set_fontsize(fontsize_label)
        ax2.axis['top'].major_ticklabels.set_fontsize(fontsize_label)
        ax2.axis["right"].major_ticklabels.set_visible(False)
        ax2.grid(b=True)
        # plot data
        color_idx = 0
        for k,v in plot_data.items():
            xdata = v[0]**(-1/3)
            ax.plot(xdata, v[1], 's', label='{}'.format(k), markersize=markersize,
                    color=color[color_idx])
            color_idx += 1
# linear fits make no sense here, its something asymptotic.
#             # linear fit
#             if len(v[0]) > 2 and np.abs(v[0][0] - v[0][-1]) > 20: 
#                 fitpar = np.polyfit(xdata, v[1], 1)
#                 # plot fit
#                 xdata_fit = np.arange(0, 1, 0.1)
#                 lin_fit = np.poly1d(fitpar)
#                 ax.plot(xdata_fit, lin_fit(xdata_fit), '--', color='grey')#             # linear fit
#             if len(v[0]) > 2 and np.abs(v[0][0] - v[0][-1]) > 20: 
#                 fitpar = np.polyfit(xdata, v[1], 1)
#                 # plot fit
#                 xdata_fit = np.arange(0, 1, 0.1)
#                 lin_fit = np.poly1d(fitpar)
#                 ax.plot(xdata_fit, lin_fit(xdata_fit), '--', color='grey')
        leg = ax.legend(title='Number of GL functions:', loc=3, fontsize=fontsize_label,
                        numpoints=1)
        leg.get_title().set_fontsize(fontsize_label)
        if fname is None:
            fig.show()
        else:
            self._export(fname=fname, export_dir=export_dir, size=size, figure=fig)
 
    
    def plot_temp_peakpos(self, iso_keys=['1a', '1b'], fname_prefix=None,
                          export_dir=os.path.expanduser('~'), size=[20,14],
                          fontsize_clusterid=28, fontsize_label=12, markersize=6):
        
        fit_id = self._eval_fit_id()
                       
        def plot_single_size(temp_ebin, temp_diff, temp_ratio):
            fig = plt.figure()
            # setup ebin(T) plot
            ax = fig.add_subplot(3, 1, 1)
            #ax.set_xlabel('Temperature (K)', fontsize=fontsize_label)
            ax.tick_params(labelsize=fontsize_label)
            ax.set_ylim([-2.6,-1.2])
            ax.grid()
            cluster_id = temp_ebin.pop('id')
            ax.text(0.05, 0.9, cluster_id, transform = ax.transAxes, fontsize=fontsize_clusterid,
                    horizontalalignment='left', verticalalignment='top')
            for iso, v in temp_ebin.items():
                ax.plot(v['T'], -1*np.array(v['ebin']), color='grey')
                ax.plot(v['T'], -1*np.array(v['ebin']), 's', markersize=markersize,
                        color=self.cfg.water_isomer_color_map[iso], label=iso)
            
            leg = ax.legend(title='Isomer Classes:', loc=1, fontsize=fontsize_label,
                            numpoints=1)
            leg.get_title().set_fontsize(fontsize_label)
            # setup diff(T) plot
            if temp_diff:
                ax_diff = fig.add_subplot(3, 1, 2)
                #ax_diff.set_xlabel('Temperature (K)', fontsize=fontsize_label)
                ax_diff.tick_params(labelsize=fontsize_label)
                ax_diff.axhline(0, color='black', lw=.4)
                ax_diff.set_xlim(ax.get_xlim())
                ax_diff.set_ylim([-.15, .15])
                ax_diff.grid()
                for diff, v in temp_diff.items():
                    ax_diff.plot(v['T'], v['diff'], color='grey')
                    ax_diff.plot(v['T'], v['diff'], 's', markersize=markersize,
                                 label=diff)
                leg_diff = ax_diff.legend(title='Differences:', loc=1, fontsize=fontsize_label,
                                          numpoints=1)
                leg_diff.get_title().set_fontsize(fontsize_label)
            # setup ratio(T) plot
            if temp_ratio:
                ax_ratio = fig.add_subplot(3, 1, 3)
                ax_ratio.set_xlabel('Temperature (K)', fontsize=fontsize_label)
                ax_ratio.tick_params(labelsize=fontsize_label)
                ax_ratio.axhline(.5, color='black', lw=.4)
                ax_ratio.set_xlim(ax.get_xlim())
                ax_ratio.set_ylim([0, 1])
                ax_ratio.grid()
                for ratio, v in temp_ratio.items():
                    ax_ratio.plot(v['T'], v['ratio'], color='grey')
                    ax_ratio.plot(v['T'], v['ratio'], 's', markersize=markersize,
                                  label=ratio)
                leg_ratio = ax_ratio.legend(title='Ratios:', loc=1, fontsize=fontsize_label,
                                            numpoints=1)
                leg_ratio.get_title().set_fontsize(fontsize_label)
            
            return fig
            
        ebin_dict = {}
        diff_dict = {} 
        diff_ref = {}
        ratio_dict = {}
        for s in self.dbanswer:
            cs = load_pickle(self.cfg, s[str('pickleFile')])
            cn = cs.mdata.data('clusterBaseUnitNumber')
            ct = cs.mdata.data('trapTemp')
            cic = cs._assort_fit_peaks(fit_id)
            # populate ebin_dict
            for iso in iso_keys:
                if iso in cic.keys():
                    if cn not in ebin_dict.keys():
                        ebin_dict[cn] = {'id': cs.view._pretty_format_clusterid(),
                                         iso: {'T': [ct], 'ebin': [cic[iso][0]]}
                                         }
                    if iso in ebin_dict[cn].keys():
                        ebin_dict[cn][iso]['T'].append(ct)
                        ebin_dict[cn][iso]['ebin'].append(cic[iso][0])
                    else:
                        ebin_dict[cn][iso] = {'T': [ct], 'ebin': [cic[iso][0]]}
                        
            # populate diff_dict
            i = 0
            while i+1 < len(iso_keys):
                k1, k2 = iso_keys[i], iso_keys[i+1]
                diff_id = 'd_{}_{}'.format(k1, k2)
                i += 1
                if k1 in cic.keys() and k2 in cic.keys():
                    if cn in diff_ref:
                        diff = diff_ref[cn] - (cic[k1][0] - cic[k2][0])
                    else:
                        diff = 0
                        diff_ref[cn] = cic[k1][0] - cic[k2][0]
                    if cn not in diff_dict.keys():
                        diff_dict[cn] = {}
                    if diff_id in diff_dict[cn].keys():
                        diff_dict[cn][diff_id]['T'].append(ct)
                        diff_dict[cn][diff_id]['diff'].append(diff)
                    else:
                        diff_dict[cn][diff_id] = {'T': [ct], 'diff': [diff]}
                        
            # populate ratio_dict
            for c in combinations(iso_keys, 2):
                if c[0] in cic.keys() and c[1] in cic.keys():
                    ratio_str = '{}/{}'.format(c[0], c[1])
                    ratio =cic[c[0]][1]/(cic[c[0]][1] + cic[c[1]][1])
                    if cn not in ratio_dict.keys():
                        ratio_dict[cn] = {}
                    if ratio_str in ratio_dict[cn].keys():
                        ratio_dict[cn][ratio_str]['T'].append(ct)
                        ratio_dict[cn][ratio_str]['ratio'].append(ratio)
                    else:
                        ratio_dict[cn][ratio_str] = {'T': [ct], 'ratio': [ratio]}
                        
        for n, e in ebin_dict.items():
#             if n in diff_dict.keys():
#                 fig = plot_single_size(e, diff_dict[n])
#             else:
#                 fig = plot_single_size(e, None)
            if n in diff_dict.keys():
                dd = diff_dict[n]
            else:
                dd = None
            if n in ratio_dict.keys():
                rd = ratio_dict[n]
            else:
                rd = None
                
            fig = plot_single_size(e, dd, rd)
                
            if fname_prefix is None:
                fig.show()
            else:
                fname = '{}_w{}.pdf'.format(fname_prefix, n)
                self._export(fname=fname, export_dir=export_dir, size=size, figure=fig)
            
            
#     def plot_temp_peakheight_ratio(self, ratio_keys=['1a', '1b'], fontsize_clusterid=28,
#                                    fontsize_label=12, markersize=6, xlim=[0,300], ylim=[0,2]):
#         
#         def plot_single_size(temp, ratios, cluster_id):
#             fig = plt.figure()
#             # setup lower axis
#             ax = fig.add_subplot(1, 1, 1)
#             ax.set_xlabel('Temperature (K)', fontsize=fontsize_label)
#             ax.tick_params(labelsize=fontsize_label)
#             ax.plot(temp, ratios, 's', markersize=markersize)
#             ax.plot(temp, ratios, color='grey')
#             ax.set_xlim(xlim)
#             ax.set_ylim(ylim)
#             ax.axhline(1, color='black', lw=.4)
#             ax.text(0.05, 0.9, cluster_id, transform = ax.transAxes, fontsize=fontsize_clusterid,
#                     horizontalalignment='left', verticalalignment='top')
# #             leg = ax.legend(title='Isomer Classes:', loc=0, fontsize=fontsize_label,
# #                             numpoints=1)
# #             leg.get_title().set_fontsize(fontsize_label)    
#             fig.show()
#         
#         ratio_dict = {}    
#         for s in self.dbanswer:
#             cs = load_pickle(self.cfg, s[str('pickleFile')])
#             cn = cs.mdata.data('clusterBaseUnitNumber')
#             ct = cs.mdata.data('trapTemp')
#             cic = cs._assort_fit_peaks()
#             for c in combinations(ratio_keys):
#                 if c[0] in cic.keys() and c[1] in cic.keys():
#                     ratio_str = '{}/{}'.format(c[0], c[1])
#                     ratio =cic[c[0]][1]/cic[c[1]][1]
#                     if cn not in ratio_dict.keys():
#                         ratio_dict[cn] = {'id': cs.view._pretty_format_clusterid(),
#                                           ratio_str: {'T': [], 'ratio': []}
#                                           }
#                     if ratio_str in ratio_dict[cn].keys():
#                         ratio_dict[cn][ratio_str]['T'].append(ct)
#                         ratio_dict[cn][ratio_str]['ratio'].append(ratio)
#                     else:
#                         ratio_dict[cn][ratio_str] = {'T': [], 'ratio': []}
#                 
#         for s,v in ratio_dict.items():
#             plot_single_size(v['T'], v['ratio'], v['id'])
            
                
            


#     def plot_offset_energy_ratio(self, offset_peaks=['1a', '1b'],
#                                  show_single_points=False, fname=None,
#                                  export_dir=os.path.expanduser('~'), size=[20,14],
#                                  fontsize_label=12, markersize=6, color='blue', xlim=None,
#                                  ylim=None):
#         # this only makes sense for heavy water
#         if not self.heavy_water:
#             raise ValueError('Only applicable for heavy water.')
#         fit_id = self._eval_fit_id()
# 
#         energy_ratio = []
#         energy_ratio_by_size = {}
#         peak_stats = {}
#         # populate peak lists
#         for s in self.dbanswer:
#             d2o_isomers = {'2': [], '1a': [], '1b': [], 'vib': []} 
#             cs = load_pickle(self.cfg, s[str('pickleFile')])
#             cn = cs.mdata.data('clusterBaseUnitNumber')
#             peak_list = [cs.ebin(p) for p in cs.mdata.data('fitData')[fit_id]['par'][:-2:2]]
#             # sort d2o isomers
#             self._sort_peaks(cn, self.cfg.water_isomer_limits['D2O'], peak_list,
#                              d2o_isomers['2'], d2o_isomers['1a'], d2o_isomers['1b'],
#                              d2o_isomers['vib'])
#             d2o_p1 = d2o_isomers[offset_peaks[0]]
#             d2o_p2 = d2o_isomers[offset_peaks[1]]
#             if len(d2o_p1)==1 and len(d2o_p2)==1:
#                 d2o_dE = np.abs(d2o_p1[0][1] - d2o_p2[0][1])
#                 # add h20 ref
#                 comp_list = SpecPeWaterFitList(self.cfg, clusterBaseUnitNumber=cn)
#                 for rs in comp_list.dbanswer:
#                     h2o_isomers = {'2': [], '1a': [], '1b': [], 'vib': []}
#                     crs = load_pickle(self.cfg,rs[str('pickleFile')])
#                     ref_peak_list = [crs.ebin(p) for p in crs.mdata.data('fitData')[fit_id]['par'][:-2:2]]
#                     self._sort_peaks(cn, self.cfg.water_isomer_limits['H2O'], ref_peak_list,
#                                      h2o_isomers['2'], h2o_isomers['1a'], h2o_isomers['1b'],
#                                      h2o_isomers['vib'])
#                     h2o_p1 = h2o_isomers[offset_peaks[0]]
#                     h2o_p2 = h2o_isomers[offset_peaks[1]]
#                     if len(h2o_p1)==1 and len(h2o_p2)==1:
#                         h2o_dE = np.abs(h2o_p1[0][1] - h2o_p2[0][1])
#                         energy_ratio.append([cn, h2o_dE/d2o_dE])
#                         if cn in energy_ratio_by_size.keys():
#                             energy_ratio_by_size[cn].append(h2o_dE/d2o_dE)
#                         else:
#                             energy_ratio_by_size[cn] = [h2o_dE/d2o_dE]
#                             
#                         if cn not in peak_stats.keys():
#                             peak_stats[cn] = [[], [], [], [], [], [], []]
#                             
#                         peak_stats[cn][0].append(h2o_p1[0][1])
#                         peak_stats[cn][1].append(h2o_p2[0][1])
#                         peak_stats[cn][2].append(h2o_dE)
#                         peak_stats[cn][3].append(d2o_p1[0][1])
#                         peak_stats[cn][4].append(d2o_p2[0][1])
#                         peak_stats[cn][5].append(d2o_dE)
#                         peak_stats[cn][6].append(h2o_dE/d2o_dE)
#         plot_data = np.array([[ps[0], ps[1], ps[0]**(-1/3)] for ps in energy_ratio]).transpose()
#         plot_data_mean = [[k, np.mean(item), np.std(item)] for k,item in energy_ratio_by_size.items()]
#         plot_data_mean.sort()
#         plot_data_mean = np.array(plot_data_mean).transpose()
#         # create plot
#         fig = plt.figure()
#         # setup lower axis
#         ax = fig.add_subplot(1, 1, 1)
#         ax.set_xlabel('number of water molecules (n)', fontsize=fontsize_label)
#         ax.tick_params(labelsize=fontsize_label)
#         if xlim:
#             ax.set_xlim(xlim[0], xlim[1])
#         if ylim:
#             ax.set_ylim(ylim[0], ylim[1])
#         ax.set_ylabel('$\Delta E_{H_2O}/\Delta E_{D_2O}$', fontsize=fontsize_label)
#         ax.xaxis.grid(True)
#         # plot lines for 1 and sqrt(2)
#         ax.axhline(1, color='black', lw=.4)
#         ax.axhline(np.sqrt(2), color='black', lw=.4)
#         # plot data
#         if show_single_points:
#             ax.plot(plot_data[0], plot_data[1], 's', color='limegreen', markersize=markersize)
#         ax.plot(plot_data_mean[0], plot_data_mean[1], color='grey')
#         ax.errorbar(plot_data_mean[0], plot_data_mean[1], plot_data_mean[2], fmt='s',
#                     color=color, markersize=markersize, capsize=markersize/2)
#         if fname is None:
#             fig.show()
#         else:
#             self._export(fname=fname, export_dir=export_dir, size=size, figure=fig,
#                          twin_axes=False)
#         
#         return peak_stats, energy_ratio_by_size
            
        
            
        
        
    def refit(self, fit_par=None, cutoff=None):
        '''TODO: inherit from fit or use super()'''
        fit_id = self._eval_fit_id()
        for s in self.dbanswer:
            cs = load_pickle(self.cfg,s[str('pickleFile')])
            cs._refit(fit_id=fit_id, fit_par=fit_par, cutoff=cutoff, commit_after=True)
            #cs.commit()
            del cs
            
    def gauge(self, gauge_ref=None, refit='y', commit_after=True, ignore_wavelength=False):
        '''
        Gauge all spectra in list with gauge_ref or
        re-gauge them with their previous gauge_ref.
        refit:  None - ask if you want to refit
                'y'  - do all refits
                'n'  - skip refittting
        '''
        #SpecPeList.gauge(gauge_ref=gauge_ref, refit=refit)
        for s in self.dbanswer:
            cs = load_pickle(self.cfg, s['pickleFile'])
            if gauge_ref is not None:
                cs.gauge(gauge_ref, refit=refit, commit_after=commit_after, ignore_wavelength=ignore_wavelength)
            elif 'gaugeRef' in cs.mdata.data().keys():
                cs.gauge(cs.mdata.data('gaugeRef'), refit=refit, commit_after=commit_after, ignore_wavelength=ignore_wavelength)
            else:
                print('Spec has no gauge reference yet; skipping.')
            
            del cs    




class SpecMList(SpecList):
    def __init__(self, cfg, clusterBaseUnit=None, clusterBaseUnitNumber=None,
                 clusterBaseUnitNumberRange=None, recTime=None, recTimeRange=None,
                 inTags=None, notInTags=None, datFileName=None, trapTemp=None,
                 trapTempRange=None, hide_trash=True, order_by='recTime'):
        self.cfg = cfg
        self.spec_type = 'ms'
        with Db('casi', self.cfg) as db:
            self.dbanswer = db.query(self.spec_type, clusterBaseUnit=clusterBaseUnit,
                                     clusterBaseUnitNumber=clusterBaseUnitNumber,
                                     clusterBaseUnitNumberRange=clusterBaseUnitNumberRange,
                                     recTime=recTime, recTimeRange=recTimeRange, inTags=inTags,
                                     notInTags=notInTags, datFileName=datFileName,
                                     trapTemp=trapTemp, trapTempRange=trapTempRange,
                                     hide_trash=hide_trash, order_by=order_by)
        self.pfile_list = [row['pickleFile'] for row in self.dbanswer]
        self.view = viewlist.ViewMsList(self)


# class Batch(object):
#     def __init__(self, cfg, specType, clusterBaseUnit=None, clusterBaseUnitNumber=None,
#                  clusterBaseUnitNumberRange=None, recTime=None, recTimeRange=None,
#                  inTags=None, notInTags=None, datFileName=None, waveLength=None, trapTemp=None,
#                  trapTempRange=None):
#         self.cfg = cfg
#         self.query(specType, clusterBaseUnit=clusterBaseUnit,
#                    clusterBaseUnitNumber=clusterBaseUnitNumber,
#                    clusterBaseUnitNumberRange=clusterBaseUnitNumberRange,
#                    recTime=recTime, recTimeRange=recTimeRange,
#                    inTags=inTags, notInTags=notInTags,
#                    datFileName=datFileName, waveLength=waveLength,
#                    trapTemp=trapTemp, trapTempRange=trapTempRange)
# 
#         
#     def query(self, specType, clusterBaseUnit=None, clusterBaseUnitNumber=None,
#               clusterBaseUnitNumberRange=None, recTime=None, recTimeRange=None,
#               inTags=None, notInTags=None, datFileName=None, waveLength=None,
#               trapTemp=None, trapTempRange=None):
#         with Db('casi', self.cfg) as db:
#             self.dbanswer = db.query(specType, clusterBaseUnit=clusterBaseUnit,
#                                      clusterBaseUnitNumber=clusterBaseUnitNumber,
#                                      clusterBaseUnitNumberRange=clusterBaseUnitNumberRange,
#                                      recTime=recTime, recTimeRange=recTimeRange,
#                                      inTags=inTags, notInTags=notInTags,
#                                      datFileName=datFileName, waveLength=waveLength,
#                                      trapTemp=trapTemp, trapTempRange=trapTempRange)
#             
# 
# 
#             
#             
#     def list_temp(self):
#         def format_recTime(unixtime):
#             return time.strftime('%d.%m.%Y', time.localtime(unixtime))
#         
#         def format_datFile(datfile):
#             return os.path.basename(datfile)
#         
#         items = ['clusterBaseUnitNumber', 'waveLength', 'recTime', 'datFile', 'trapTemp']
#         mdataList = []
#         rowCount = 0
#         for s in self.dbanswer:
#             cs = load_pickle(self.cfg,s[str('pickleFile')])        
#             mdataList.append([])
#             for key in items:
#                 if key in cs.mdata.data().keys():
#                     mdataList[rowCount].append(cs.mdata.data(key))
#                 else:
#                     mdataList[rowCount].append(0)
#             rowCount += 1             
#         print('size'.ljust(4+3), end=' ')
#         print('lambda'.ljust(5+3), end=' ')
#         print('recTime'.ljust(10+3), end=' ')
#         print('datFile'.ljust(13+3), end=' ')
#         print('trapTemp'.ljust(8))
#         for row in mdataList:
#             print(str(row[0]).ljust(4+3), end=' ')
#             print(str(round(row[1]*1e9,1)).ljust(5+3), end=' ')
#             print(format_recTime(row[2]).ljust(10+3), end=' ')
#             print(format_datFile(row[3]).ljust(13+3), end=' ')
#             print(str(round(row[4],1)).ljust(8))  
#   
#     
#     
# 
#     
#             
# 
#         
#         
# 
# 
#     
#     
#     
#             
#             
#     def regauge_pt(self):
#         for s in self.dbanswer:
#             cs = load_pickle(self.cfg,s[str('pickleFile')])
#             try:
#                 cs.gauge('tof', 
#                          lscale=1.006,  #cs.mdata.data('fitParTof')[-1], 
#                          Eoff=cs.mdata.data('fitParTof')[-3]#, 
#                          #toff=63e-9  #cs.mdata.data('fitParTof')[-2]
#                          )
#             except:
#                 print(cs.mdata.data('datFile'), 'Fit failed.')
#             else:
#                 cs.commit()
#             del cs
#         self.list_mdata_ptfit()
#         
#         
#     def show_all(self):
#         sl=[]
#         for s in self.dbanswer:
#             cs = load_pickle(self.cfg,s[str('pickleFile')])
#             cs.view.showTofFit('fitParTof')
#             sl.append(cs)
#         return sl
#     
#     def list_of_specs(self, slist):
#         sl=[]
#         for s in slist:
#             cs = load_pickle(self.cfg,s[str('pickleFile')])
#             sl.append(cs)
#         return sl    
#             
            
            
