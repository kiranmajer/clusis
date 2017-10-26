from load import load_pickle, spec_from_specdatadir
from dbshell import Db
import time
import os
import viewlist
# for comparison methods
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA
import matplotlib.ticker as ticker
#from scipy.stats import linregress
from itertools import combinations
from tools import print_answer



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
        print_answer(self.dbanswer, self.spec_type)
        self.pfile_list = [row['dataStorageLocation'] for row in self.dbanswer]
        self.view = viewlist.ViewList(self)
        

#    def query(self, recTime=None, recTimeRange=None,
#              inTags=None, notInTags=None, datFileName=None):
#        with Db('casi', self.cfg) as db:
#            self.dbanswer = db.query(self.spec_type, recTime=recTime, recTimeRange=recTimeRange,
#                                     inTags=inTags, notInTags=notInTags, datFileName=datFileName)

    def get_spec(self, number, storage_type='json'):
        if storage_type is 'json':
            spec = spec_from_specdatadir(self.cfg, self.dbanswer[number]['dataStorageLocation'])
        elif storage_type is 'pickle':
            spec = load_pickle(self.cfg, self.dbanswer[number]['dataStorageLocation'])
        else:
            raise ValueError("storage_type must be either 'json' or 'pickle'. Got {} instead.".format(storage_type))
        return spec

    def update_mdata(self, mdataDict):
        'TODO: open db only once'
        for entry in self.dbanswer:
            #print(entry['dataStorageLocation'])
            cs = spec_from_specdatadir(self.cfg, entry['dataStorageLocation'])
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
            cs = spec_from_specdatadir(self.cfg, entry['dataStorageLocation'])
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
            cs = spec_from_specdatadir(self.cfg, s['dataStorageLocation'])
            values = [cs.mdata.data(k) for k in keys]
            print('{}:'.format(os.path.basename(cs.mdata.data('datFile'))), values)
            del cs
            
    def _export(self, fname='export.pdf', export_dir=os.path.expanduser('~'), size='p1h',
                figure=None, twin_axes=True, xy_labels=False, margins=None):
        if export_dir.startswith('~'):
            export_dir = os.path.expanduser(export_dir)
        f = os.path.join(export_dir, fname)
        'TODO: presets are mere personal. For a general approach probably not suitable.'
        presets = {'p1': [14, 14*3/7],
                   'p1h': [14, 9],
                   'p1s': [11,7],
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
        if margins:
            figure.subplots_adjust(left=margins[3]/size[0], bottom=margins[2]/size[1],
                                   right=1-margins[1]/size[0], top=1-margins[0]/size[1])
        elif twin_axes:
            figure.subplots_adjust(left=1.3/size[0], bottom=0.8/size[1],
                                   right=1-0.15/size[0], top=1-0.85/size[1])
        elif xy_labels: # size == presets['p2']:
            figure.subplots_adjust(left=1.25/size[0], bottom=0.9/size[1],
                                   right=1-0.15/size[0], top=1-0.15/size[1])
        else:
            figure.subplots_adjust(left=0.08, bottom=0.095, right=0.995, top=0.98)
#         'TODO: some of these margins are font size related, so they need to be adapted accordingly'
#         t = 0.2/size[1]
#         r = 0.3/size[0]
#         ax = figure.axes.get_xa
#         if figure.axes.get_xlabel():
#             b = 0.9/size[1] # 0.9 fits for font size 8
#         else:
#             b = 0.4/size[1]
#         if figure.axes.get_ylabel():
#             l = 0.4/size[0] # 0.4 dito
#         else:
#             l = 0.15/size[0]
#             r = 0.15/size[0]
#         figure.subplots_adjust(left=l, bottom=b, right=1-r, top=1-t)
        figure.savefig(f)
        #self.fig.set_size_inches(orig_size)
        
    def remove_spec(self):
        'TODO: query for confirmation, since you can cause great damage.'
        for entry in self.dbanswer:
            cs = spec_from_specdatadir(self.cfg, entry['dataStorageLocation'])
            cs.remove()
            del cs      
            
    def export_single_plots(self, plot_fct, export_dir='~/test', latex_fname=None, overwrite=True, 
                            linewidth=.8, layout=[8,4], size='latex', latex=True, firstpage_offset=0,
                            margins=None, xlabel_str='Binding energy (eV)', skip_plots=False,
                            **keywords):
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
                               linewidth=linewidth, margins=margins)
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
                                lf.write('\\makebox[{}cm]{{}}\n'.format(size[0]))
                            col_idx += 1
                            plotidx += 1
                        row_idx += 1
                    lf.write('\\\\*[-3mm]\n')
                    #print('added {} of {} plots per page'.format(plotcount, ppp))
                    if not use_raisebox and ((plotcount - (rows - firstpage_offset)*col)%plotidx == 0 or
                                              plotcount%plotidx == 0):
                        label_col = col
                    for c in range(label_col):
                        lf.write('\\makebox[{}cm]{{\\textsf{{\\scriptsize {}}}}}\n'.format(size[0], xlabel_str))
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
        print_answer(self.dbanswer, self.spec_type)
        self.pfile_list = [row['dataStorageLocation'] for row in self.dbanswer]
        self.view = viewlist.ViewPesList(self)
        
        
    def gauge(self, gauge_ref=None, ignore_wavelength=False):
        '''
        Gauge all spectra in list with gauge_ref or
        re-gauge them with their previous gauge_ref.
        '''
        for s in self.dbanswer:
            cs = spec_from_specdatadir(self.cfg, s['dataStorageLocation'])
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
            cs = spec_from_specdatadir(self.cfg,s[str('dataStorageLocation')])
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
            cs = spec_from_specdatadir(self.cfg,s[str('dataStorageLocation')])
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
            cs = spec_from_specdatadir(self.cfg,s[str('dataStorageLocation')])
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
            cs = spec_from_specdatadir(self.cfg,s[str('dataStorageLocation')])
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
            cs = spec_from_specdatadir(self.cfg, s['dataStorageLocation'])
            if gauge_ref is not None:
                cs.gauge(gauge_ref, refit=refit, ignore_wavelength=ignore_wavelength)
            elif 'gaugeRef' in cs.mdata.data().keys():
                cs.gauge(cs.mdata.data('gaugeRef'), refit=refit, ignore_wavelength=ignore_wavelength)
            else:
                print('Spec has no gauge reference yet; skipping.')
            
            del cs
        
    def fit(self, fit_par, fit_id='default_fit', cutoff=None, asym_par=None,
            use_boundaries=True):
        for s in self.dbanswer:
            cs = spec_from_specdatadir(self.cfg,s[str('dataStorageLocation')])
            cs.fit(fitPar0=fit_par, fit_id=fit_id, cutoff=cutoff, asym_par=asym_par,
                   use_boundaries=use_boundaries)
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
            inTags_list.append((self.fit_id,))  
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
            print('Using fit id: ', self.fit_id)
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
            cs = spec_from_specdatadir(self.cfg,s[str('dataStorageLocation')])
            'TODO: cant we remove the if clause?'
            if cs.mdata.data('specTypeClass') == 'specPeWater' and \
            'background' not in cs.mdata.data('systemTags') and \
            'fitted' in cs.mdata.data('systemTags'):
                mdataList.append([])
                for key in items:
                    if key == 'par':
                        mdataList[rowCount].append([round(float(cs.ebin(p)),2) for p in cs.mdata.data('fitData')[fit_id][key][:-2:2]])
                        #mdataList[rowCount].append(round(np.sum(cs.mdata.data(key)[-2:]), 3))
                        sigmas = cs._get_peakshape_par(key, fit_id, width=False, width_pars=True)
                        if np.sqrt(2*np.log(2))*sigmas[0] > sigmas[1]:
                            asymmetry = 'reversed'
                        else:
                            asymmetry = ''
                        mdataList[rowCount].append(asymmetry)
                        mdataList[rowCount].append(round(cs._get_peakshape_par(key, fit_id), 3))
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
              'asymmetry'.ljust(9+3),
              'Ebin of peaks [eV]')
        last_size = 0
        for row in mdataList:
            if not row[0] == last_size:
                print('-'*116)
            print(str(row[0]).ljust(4+3), 
                  str(round(row[1]*1e9)).ljust(6+3),
                  format_recTime(row[2]).ljust(10+3), end=' ')
            if row[3] is None:
                print('None'.ljust(6+3), end=' ')
            else:                                       
                print(str(round(row[3]*1e6, 2)).ljust(6+3), end=' ')
            print(str(round(row[4]*1e3, 3)).ljust(7+3),
                  str(row[7]).ljust(5+3),
                  str(row[8]).ljust(5+3),
                  str(row[9]).ljust(5+3),
                  str(row[6]).ljust(9+3),
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

    'TODO: replace with assort_fit_peaks from SpecPeWater'
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
                           fit_must_include_size=1000, mark_iso=True, fname=None,
                           export_dir=os.path.expanduser('~'), size=[20,14],
                           fontsize_label=12, markersize=6, xlim=[0,0.42],
                           ylim=[-4,0], ax2_ticks=[10, 20,40,80,150,350,1000, 5000],
                           color=None, alpha=1.0, markeredgecolor='black',
                           markertype_comp_data=None, markersize_comp_data=None,
                           fade_color=False, comp_data_hollow_marker=False,
                           color_comp_data=None, show_legend=True, show_own_data_legend=True,
                           show_sigma=False, generic_legend_labels=False,
                           show_fit_results=True, add_slopes=None, slope_lw=1, hw_data=None,
                           margins=None):
        
        fit_id = self._eval_fit_id()
        # get linear parameters depending on water type
        if self.heavy_water:
            linpar = self.cfg.water_isomer_limits['D2O']
        else:
            linpar = self.cfg.water_isomer_limits['H2O']
        # get linpar adopted for a certain fit_id, if any
        if fit_id in linpar:
            linpar = linpar[fit_id]
        else:
            linpar = linpar['default_fit']
            
        if hw_data is not None:
            hw_linpar = self.cfg.water_isomer_limits['D2O']
            if fit_id in hw_linpar:
                hw_linpar = hw_linpar[fit_id]
            else:
                hw_linpar = hw_linpar['default_fit']
            
        # disable marking isomer classes for single fit
        # TODO: Again, hard coded values are bad!
        color_faded = {'indigo': '#746282',
                       'limegreen': '#9acd9a',
                       'blue': '#bfbfff',
                       'red': '#ffbfbf'}
        
        hw_color = ['indigo', 'limegreen', 'blue', 'red']
        if fit_id == 'single_gl':
            mark_iso = False
            if fade_color:
                color = [color_faded['blue']]
                hw_color = ['blue']
            else:
                color = ['blue']
            
        if show_sigma:
            color.extend(['limegreen', 'grey'])
        
#         # show own legend if no comp data
#         if not comp_data:
#             show_own_data_legend = True
         
        if color is None:
            if fade_color:
                color = [color_faded['indigo'], color_faded['limegreen'],
                         color_faded['blue'], color_faded['red']]
            else:
                color = ['indigo', 'limegreen', 'blue', 'red']
        if mark_iso:
            if generic_legend_labels:
                leg_label = ['Peak II', 'Peak Ia', 'Peak Ib', 'Peak HE']
            else:
                leg_label = ['Isomer II', 'Isomer Ia', 'Isomer Ib', 'Vibrational']
        else:
            leg_label = ['Single GL Fit']
        if show_sigma:
            leg_label = ['-VDE', '-VDE$+\sqrt{2\ln(2)}\sigma_G$', '-VDE$-\sigma_L$']
        if color_comp_data is None:
            color_comp_data = ['lightblue', 'whitesmoke', 'black', 'yellow', 'violet',
                               'grey', 'navy']
        if color_comp_data == 'theo':
            color_comp_data = ['indigo', 'red', 'limegreen', 'blue', 'red','orange',
                               'yellow', 'pink', 'blue', 'green', 'yellow']
        if markertype_comp_data == 'theo':
            markertype_comp_data = ['D','D','D','o','o','o','o','>','>','<','<']
            
        if markeredgecolor == 'same':
            markeredgecolor = color
        else:
            markeredgecolor = [markeredgecolor]*4
                         
        def plot_comp(plot_data, fit_par, fit_res, cutoff, fontsize_label, markersize,
                      xlim, ylim, ax2_ticks, markertype_comp_data, markersize_comp_data,
                      comp_data=None, comp_data_hollow_marker=False, add_slopes=None,
                      slope_lw=1, hw_plot_data=None):
            fig = plt.figure()
            # setup lower axis
            ax = host_subplot(111, axes_class=AA.Axes)
            ax.set_xlabel('n$^{-1/3}$')
            ax.axis['bottom'].label.set_fontsize(fontsize_label)
            ax.set_xlim(xlim[0], xlim[1])
            if show_sigma:
                ax.set_ylabel('location of special curve points (eV)')
            else:
                ax.set_ylabel('-VDE (eV)')
            ax.axis['left'].label.set_fontsize(fontsize_label)
            ax.axis['bottom'].major_ticklabels.set_fontsize(fontsize_label)
            ax.axis['left'].major_ticklabels.set_fontsize(fontsize_label)
            ax.set_ylim(ylim[0], ylim[1])
            # setup upper axis
            ax2 = ax.twin()
            x2_ticks_list = np.array(ax2_ticks)**(-1/3)
            x2_ticklabel_list = [str(t) for t in ax2_ticks]
            if xlim[0] < 0:
                x2_ticks_list = np.append(x2_ticks_list, 0)
                x2_ticklabel_list.append('bulk')
            ax2.set_xticks(x2_ticks_list)
            ax2.set_xticklabels(x2_ticklabel_list)
            ax2.set_xlabel('number of water molecules (n)')
            ax2.axis['top'].label.set_fontsize(fontsize_label)
            ax2.axis['top'].major_ticklabels.set_fontsize(fontsize_label)
            ax2.axis["right"].major_ticklabels.set_visible(False)
            ax2.grid(b=True, color='black', linestyle=':', linewidth=.1)
            # write fit values
            if show_fit_results:
                if len(fit_par) > 0:
                    fit_par.sort(key=lambda fp: fp[-1], reverse=True)
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
                    ax.text(0.015, -0.2 + ylim[1], ex_str, verticalalignment='top',
                            fontsize=fontsize_label,bbox=bbox_props)
            # plot data
            idx = 0
            '''TODO: name peak groups! With idx label get wrong names, if range is plotted, which 
            does not coantain peak II.'''
            own_data = []
            for peak_set in plot_data:
                # mind the ',' after ods, because plot returns a list
                ods, = ax.plot(peak_set[2], peak_set[1], 's', markersize=markersize,
                               color=color[idx], label=leg_label[idx], alpha=alpha,
                               markeredgecolor=markeredgecolor[idx])
                own_data.append(ods)
                idx += 1
                
            # plot d2o data
            if hw_plot_data is not None:
                print('Plotting d2o data...')
                idx = 0
                '''TODO: name peak groups! With idx label get wrong names, if range is plotted, which 
                does not coantain peak II.'''
                hw_own_data = []
                for peak_set in hw_plot_data:
                    # mind the ',' after ods, because plot returns a list
                    ods, = ax.plot(peak_set[2], peak_set[1], 'o', markersize=markersize_comp_data,
                                   color=hw_color[idx], label=leg_label[idx], alpha=alpha)
                    hw_own_data.append(ods)
                    idx += 1            
            
            # optionally add legend for our data points
            if show_own_data_legend and (show_legend in ['r', 'b'] or add_slopes):
                # handles argument requires matplotlib >= 1.4(.2)
                if hw_data is not None:
                    own_data = hw_own_data
                own_legend = plt.legend(handles=own_data, loc=4, fontsize=fontsize_label,
                                        numpoints=1)
                ax.add_artist(own_legend)
            # plot fits
            c = 0.5
            if cutoff is not None:
                c = cutoff**(-1/3)            
            for par_set in fit_par:
                lin_fit = np.poly1d(par_set)
                ax.plot([xlim[0], c], lin_fit([xlim[0], c]), '-', color='grey', lw=.5)
                ax.plot([c, xlim[1]], lin_fit([c, xlim[1]]), '--', color='grey', lw=.5)
            # plot comparison data
            if comp_data is not None:
                idx = 0
                ext_data = []
                if markertype_comp_data is None:
                    markertype_comp_data = ['o']*len(comp_data)
                if markersize_comp_data is None:
                    markersize_comp_data = markersize
                for key, peak_set in sorted(comp_data.items()):
#                     if idx < 4:
#                         marker ='o'
#                     else:
#                         marker='D'
                    # TODO: this is shoulden't be hard coded
                    label = {'bowen_iso1_origin': 'Isomer I (Coe et al.)',
                             'bowen_iso1_stretch': 'Vibrational (Coe et al.)',
                             'neumark_iso1': 'Isomer I (Verlet et al.)',
                             'neumark_iso1_high_press': 'Isomer I [Ne] (Young et al.)',
                             'neumark_iso2': 'Isomer II (Verlet et al.)',
                             'neumark_iso3': 'Isomer III (Verlet et al.)',
                             'neumark_iso1_digitized': 'Isomer I (Verlet et al.) [digitized]',
                             'neumark_iso1_high_press_digitized': 'Isomer I [Ne] (Young et al.) [digitized]',
                             'neumark_iso2_digitized': 'Isomer II (Verlet et al.) [digitized]',
                             'neumark_iso3_digitized': 'Isomer III (Verlet et al.) [digitized]',
                             'water_jets': 'Water jets (several)',
                             'bowen_d2o_origin_1fit': 'Isomer I [1 fit] (Bowen)',
                             'bowen_d2o_origin_2fit': 'Isomer I [2 fit] (Bowen)',
                             'bowen_d2o_stretch': 'Vibrational (Bowen)',
                             'herbert_surface': 'surface (Jacobson, Herbert)',
                             'herbert_partial': 'part. embedded (Jacobson, Herbert)',
                             'herbert_cavity': 'cavity (Jacobson, Herbert)',
                             'herbert_cavity_aneal': 'cavity init. (Jacobson, Herbert)',
                             'turi_tb_surface': 'TB surface (Turi)',
                             'turi_tb_interior': 'TB interior (Turi)',
                             'turi_lgs_surface': 'LGS surface (Turi)',
                             'turi_lgs_interior': 'LGS interior (Turi)',
                             'barnett_surface': 'surface (Barnett et al.)',
                             'barnett_interior': 'interior (Barnett et al.)',
                             'barnett_diffuse': 'diffuse (Barnett et al.)',
                             'turi_tb_surface_digitized': 'TB surface (Turi) [digitized]',
                             'turi_tb_interior_digitized': 'TB interior (Turi) [digitized]',
                             'turi_lgs_surface_digitized': 'LGS surface (Turi) [digitized]',
                             'turi_lgs_interior_digitized': 'LGS interior (Turi) [digitized]',
                             }
                    if key == 'water_jets' and xlim[0] == 0:
                        eds, = ax.plot(peak_set[0], -1*peak_set[1], markertype_comp_data[idx],
                                       label=label[key], markersize=markersize_comp_data+1, 
                                       color=color_comp_data[idx])
                    elif comp_data_hollow_marker:
                        eds, = ax.plot(peak_set[0], -1*peak_set[1], markertype_comp_data[idx],
                                       label=label[key], markersize=markersize_comp_data,
                                       color=color_comp_data[idx], mfc='none', markeredgewidth=.1)
                    else:
                        eds, = ax.plot(peak_set[0], -1*peak_set[1], markertype_comp_data[idx],
                                       label=label[key], markersize=markersize_comp_data,
                                       color=color_comp_data[idx], markeredgewidth=.1,
                                       markeredgecolor='black')
                    ext_data.append(eds)
                    idx += 1
                if show_legend and show_legend in ['r', 'b']:
                    lpar = {'fig_hscale':{'r': 2.25, 'b': 2},
                            'margins': {'r': [.08, .07, .66, .98], # [left, bottom, right, top]
                                        'b': [.08, .48, .98, .98]},
                            'legend_anchor': {'r': (1.04, 1), 'b': (0.46, -.13)},
                            'legend_loc': {'r':2, 'b': 9},
                            'legend_col': {'r': 1, 'b': 2}
                            }
                    leg = ax.legend(handles=ext_data, bbox_to_anchor=lpar['legend_anchor'][show_legend],
                                    loc=lpar['legend_loc'][show_legend], borderaxespad=0.,
                                    ncol=lpar['legend_col'][show_legend], fontsize=fontsize_label,
                                    columnspacing=0)
                elif show_legend:
                    ax.legend(handles=ext_data, loc=0, fontsize=fontsize_label, numpoints=1)
                
            # add slopes for comparison
            slope_legend = []
            slope_legend_ref = []
            if add_slopes is not None:
                add_slopes.sort()
                for slope in add_slopes:
                    # TODO: use lambda
                    ir0=0
                    ir1=80**(-1/3)
                    ir2=xlim[1]
                    vde0=slope[1]
                    vde1=vde0 + ir1*slope[0]
                    vde2=vde0 + ir2*slope[0]
                    eds, = ax.plot([ir0, ir1], [vde0, vde1], '-', color=slope[2],
                                   label='A={}'.format(slope[0]), lw=slope_lw)
                    ax.plot([ir1, ir2], [vde1, vde2], '--', color=slope[2], lw=slope_lw)
                    if slope[0] not in slope_legend_ref:
                        slope_legend_ref.append(slope[0])
                        slope_legend.append(eds)
                
                ax.legend(handles=slope_legend, loc=0, fontsize=fontsize_label, numpoints=1)
            
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
                self._export(fname, export_dir, size, figure=fig, xy_labels=True, margins=margins)
                 
                          
        # main method
        p_2 = []
        p_1a = []
        p_1b = []
        p_vib = []
        p_sg = []
        p_sl = []
        for s in self.dbanswer:
            cs = spec_from_specdatadir(self.cfg,s[str('dataStorageLocation')])
            #peak_list = [cs.ebin(p) for p in cs.mdata.data('fitData')[fit_id]['par'][:-2:2]]
            peak_list = [cs.ebin(peak[0]) for peak in cs._get_fit_peaks(fit_par_type='par',
                                                                        fit_id=fit_id)]
            shape_par = cs._get_peakshape_par(fit_par='par', fit_id=fit_id, width=False,
                                              width_pars=True)
            sg, sl = shape_par[0], shape_par[1]
            for p in peak_list:
                    p_sg.append([cs.mdata.data('clusterBaseUnitNumber'),
                                 p - np.sqrt(2*np.log(2))*sg])
                    p_sl.append([cs.mdata.data('clusterBaseUnitNumber'), p + sl])
            if mark_iso:
                self._sort_peaks(cs.mdata.data('clusterBaseUnitNumber'), linpar,
                                 peak_list, p_2, p_1a, p_1b, p_vib)
            else:
                for p in peak_list:
                    p_1b.append([cs.mdata.data('clusterBaseUnitNumber'), p])
            
            del cs
            
        # add d2o data
        if hw_data is None:
            hw_plot_data = None
        else:
            hw_p_2 = []
            hw_p_1a = []
            hw_p_1b = []
            hw_p_vib = []
            hw_p_sg = []
            hw_p_sl = []
            for s in hw_data.dbanswer:
                cs = spec_from_specdatadir(self.cfg,s[str('dataStorageLocation')])
                #peak_list = [cs.ebin(p) for p in cs.mdata.data('fitData')[fit_id]['par'][:-2:2]]
                hw_peak_list = [cs.ebin(peak[0]) for peak in cs._get_fit_peaks(fit_par_type='par',
                                                                               fit_id=fit_id)]
                hw_shape_par = cs._get_peakshape_par(fit_par='par', fit_id=fit_id, width=False,
                                                     width_pars=True)
                hw_sg, hw_sl = hw_shape_par[0], hw_shape_par[1]
                for p in hw_peak_list:
                        hw_p_sg.append([cs.mdata.data('clusterBaseUnitNumber'),
                                        p - np.sqrt(2*np.log(2))*hw_sg])
                        hw_p_sl.append([cs.mdata.data('clusterBaseUnitNumber'), p + hw_sl])
                if mark_iso:
                    self._sort_peaks(cs.mdata.data('clusterBaseUnitNumber'), hw_linpar,
                                     hw_peak_list, hw_p_2, hw_p_1a, hw_p_1b, hw_p_vib)
                else:
                    for p in hw_peak_list:
                        hw_p_1b.append([cs.mdata.data('clusterBaseUnitNumber'), p])
                
                del cs            
 
            if not show_sigma:
                hw_p_sg, hw_p_sl = [], []
            hw_plot_data = [ps for ps in [hw_p_2, hw_p_1a, hw_p_1b, hw_p_vib, hw_p_sg, hw_p_sl] if len(ps) > 0]
            hw_plot_data = [np.array(ps).transpose() for ps in hw_plot_data]
            hw_plot_data = [np.vstack((ps, ps[0]**(-1/3))) for ps in hw_plot_data]
            for ps in hw_plot_data:
                ps[1] = ps[1]*-1 
         
        #print('p_* are:', p_2, p_1a, p_1b, p_vib)
        if not show_sigma:
            p_sg, p_sl = [], []
        plot_data = [ps for ps in [p_2, p_1a, p_1b, p_vib, p_sg, p_sl] if len(ps) > 0]
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
            #print('now fitting:')
            #print(peak_set[2], peak_set[1])
            if len(peak_set[2]) > 2 and fit_must_include_size in peak_set[0]: # use at least 3 points for linear fit
                fitpar, cov = np.polyfit(peak_set[2], peak_set[1], 1, cov=True)
                fit_par.append(fitpar)
                res=np.sqrt(np.diag(cov))
                fit_res.append(res)
 
             
        plot_comp(plot_data, fit_par, fit_res, cutoff, fontsize_label=fontsize_label,
                  markersize=markersize, xlim=xlim, ylim=ylim, ax2_ticks=ax2_ticks,
                  markertype_comp_data=markertype_comp_data,
                  markersize_comp_data=markersize_comp_data,
                  comp_data=comp_data, comp_data_hollow_marker=comp_data_hollow_marker,
                  add_slopes=add_slopes, slope_lw=slope_lw,
                  hw_plot_data=hw_plot_data)
        return fit_par, fit_res


    def compare_peak_widths(self, comp_data=None, color_comp_data=None, fname=None,
                            export_dir=os.path.expanduser('~'), fade_color=False,
                            markeredgecolor='black', markeredgewidth=.1, add_own_data_legend=False,
                            size=[20,14], fontsize_label=12, markersize=6, xlim=[0,0.42],
                            ylim=[0,1.2], ax2_ticks=[10, 20,40,80,150,350,1000, 5000],
                            color=None, show_legend=True, n_xticks=None, sfactor=1,
                            comp_legend_loc=0, margins=None, cutoff=None, show_fits=False):
        
        fit_id = self._eval_fit_id()
        # TODO: hard coded == bad idea
        color_faded = {'indigo': '#746282',
                       'limegreen': '#9acd9a',
                       'blue': '#bfbfff',
                       'red': '#ffbfbf'}
        
        widths = {1: [], 2: [], 3: [], 4: []}
        widths_all = []
        width_pars_s_g = []
        width_pars_s_l = []
        for s in self.dbanswer:
            cs = spec_from_specdatadir(self.cfg,s[str('dataStorageLocation')])
            csize = cs.mdata.data('clusterBaseUnitNumber')
            #width = np.sum(cs.mdata.data('fitPar')[-2:])
            width, width_pars = cs._get_peakshape_par('par', fit_id, width=True,
                                                      width_pars=True)
            peak_n = (len(cs.mdata.data('fitData')[fit_id]['par']) -2)/2
            #if 0.01 < width < 1.5:
            widths[peak_n].append([csize, width])
            widths_all.append([csize, width])
            width_pars_s_g.append([csize, width_pars[0]])
            width_pars_s_l.append([csize, width_pars[1]])
            del cs
        plot_data = {}
        for k,v in widths.items():
            if len(v) > 0:
                plot_data[str(k)] = np.transpose(v)
        plot_data['s_g'] = np.transpose(width_pars_s_g)
        plot_data['s_l'] = np.transpose(width_pars_s_l)
        #xdata = plot_data[0]**(-1/3)
        
        if color is None:
            if fade_color:
                color = {'s_g': 'lightgrey', 's_l': color_faded['limegreen'],
                         '1': color_faded['blue'], '2': color_faded['red'],
                         '3': color_faded['red'], '4': color_faded['red']}
            else:
                color = {'s_g': 'grey', 's_l': 'limegreen',
                         '1': 'blue', '2': 'yellow', '3': 'midnightblue', '4': 'red'}
        
        if markeredgecolor == 'same':
            markeredgecolor_dict = dict(color)
        else:
            markeredgecolor_dict = {}
            for k in color.keys():
                markeredgecolor_dict[k] = markeredgecolor
        
        labels = {'s_g': '$\sigma_G$', 's_l': '$\sigma_L$',
                  '1': '1 GL', '2': '2 GL', '3': '3 GL', '4': '4 GL'}
        if color_comp_data is None:
            color_comp_data = ['red', 'black', 'limegreen', 'grey',
                               'yellow', 'navy']
        # create plot
        fig = plt.figure()
        # setup lower axis
        ax = host_subplot(111, axes_class=AA.Axes)
        ax.set_xlabel('n$^{-1/3}$')
        ax.axis['bottom'].label.set_fontsize(fontsize_label)
        ax.set_xlim(xlim[0], xlim[1])
        ax.set_ylabel('fwhm, $\sigma_G$, $\sigma_L$ (eV)')
        ax.axis['left'].label.set_fontsize(fontsize_label)
        ax.axis['bottom'].major_ticklabels.set_fontsize(fontsize_label)
        ax.axis['left'].major_ticklabels.set_fontsize(fontsize_label)
        ax.set_ylim(ylim[0], ylim[1])
        if n_xticks:
            #xticks = ax.get_xticks()
            ax.xaxis.set_major_locator(ticker.MaxNLocator(n_xticks))
        else:
            ax.xaxis.set_major_locator(ticker.AutoLocator())
        # setup upper axis
        ax2 = ax.twin()
        ax2.set_xticks(np.array(ax2_ticks)**(-1/3))
        ax2.set_xticklabels([str(t) for t in ax2_ticks])
        ax2.set_xlabel('number of water molecules (n)')
        ax2.axis['top'].label.set_fontsize(fontsize_label)
        ax2.axis['top'].major_ticklabels.set_fontsize(fontsize_label)
        ax2.axis["right"].major_ticklabels.set_visible(False)
        ax2.grid(b=True, color='black', linestyle=':', linewidth=.1)
        # plot data
        own_data = []
        fit_par = []
        fit_res = []
        for k,v in sorted(plot_data.items()):
            xdata = v[0]**(-1/3)
            "TODO: remove scale factor later."
            if k == 's_l':
                ods, = ax.plot(xdata, v[1]*sfactor, 's', label=labels[k], markersize=markersize,
                               color=color[k], markeredgecolor=markeredgecolor_dict[k],
                               markeredgewidth=markeredgewidth)
            else:
                ods, = ax.plot(xdata, v[1], 's', label=labels[k], markersize=markersize,
                               color=color[k], markeredgecolor=markeredgecolor_dict[k],
                               markeredgewidth=markeredgewidth)
            
            own_data.append(ods)
        
        # make linear extrapolation to the data
        for v in [np.transpose(widths_all), plot_data['s_g'], plot_data['s_l']]:
            xdata = v[0]**(-1/3)
            xdata_fit = np.array(xdata)
            ydata_fit = np.array(v[1])
            if cutoff:
                b = xdata <= cutoff**(-1/3)
                xdata_fit = xdata[b]
                ydata_fit = v[1][b]
            if len(ydata_fit) > 2: # use at least 3 points for linear fit
                fitpar, cov = np.polyfit(xdata_fit, ydata_fit, 1, cov=True)
                fit_par.append(fitpar)
                res=np.sqrt(np.diag(cov))
                fit_res.append(res)
        # plot fits
        if show_fits:
            c = 0.5
            if cutoff:
                c = cutoff**(-1/3)            
            for par_set in fit_par:
                lin_fit = np.poly1d(par_set)
                ax.plot([xlim[0], c], lin_fit([xlim[0], c]), '-', color='grey', lw=.5)
                ax.plot([c, xlim[1]], lin_fit([c, xlim[1]]), '--', color='grey', lw=.5)
            
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
        if not comp_data and show_legend:
            leg = ax.legend(loc=0, fontsize=fontsize_label, numpoints=1)
            leg.get_title().set_fontsize(fontsize_label)
        # plot comparison data
        if comp_data is not None:
            idx = 0
            ext_data = []
            for key, width_set in sorted(comp_data.items()):
#                     if idx < 4:
#                         marker ='o'
#                     else:
#                         marker='D'
                # TODO: this is shoulden't be hard coded
                label = {'bowen_iso1_sg_1fit': '$\sigma_G$ (Bowen)',
                         'bowen_iso1_sl_1fit': '$\sigma_L$ (Bowen)',
                         'bowen_iso1_fwhm_1fit': '1 GL (Bowen)',
                         'bowen_iso1_sg_2fit': '$\sigma_G$ 2 fits (Bowen)',
                         'bowen_iso1_sl_2fit': '$\sigma_L$ 2 fits (Bowen)',
                         'bowen_iso1_fwhm_2fit': '2 fits (Bowen)',
                         'bowen_d2o_sg_1fit': '$\sigma_G$ (Bowen)',
                         'bowen_d2o_sl_1fit': '$\sigma_L$ (Bowen)',
                         'bowen_d2o_fwhm_1fit': '1 GL (Bowen)',
                         'bowen_d2o_sg_2fit': '$\sigma_G$ 2 fits (Bowen)',
                         'bowen_d2o_sl_2fit': '$\sigma_L$ 2 fits (Bowen)',
                         'bowen_d2o_fwhm_2fit': '2 fits (Bowen)',
                         }
                eds, = ax.plot(width_set[0], width_set[1], 's', label=label[key],
                               markersize=markersize, color=color_comp_data[idx])
                ext_data.append(eds)
                idx += 1
                
            ax.legend(handles=ext_data, loc=comp_legend_loc, fontsize=fontsize_label, numpoints=1)
#             if add_own_data_legend:
#                 leg_own = ax.legend(handles=own_data, loc=0, fontsize=fontsize_label, numpoints=1)
        if fname is None:
            fig.show()
        else:
            self._export(fname=fname, export_dir=export_dir, size=size, figure=fig, margins=margins)
        
        return fit_par, fit_res
 
    
    def plot_temp_peakpos(self, iso_keys=['1a', '1b'], xlim=[0, 425], fname_prefix=None,
                          export_dir=os.path.expanduser('~'), size=[20,14],
                          fontsize_clusterid=28, fontsize_label=12, markersize=6,
                          ylim_pp=[-2.2,-1.2], ylim_ph=[20,80], plot_mean=True,
                          fit_ids=['2_gl']):
                       
        def plot_single_size(temp_ebin, temp_diff, temp_ratio, ylim_pp, ylim_ph, plot_mean):
            iso_names ={'2': 'II', '1a': 'Ia', '1b': 'Ib', 'vib': 'HE'}
            colors = {'1b': {'2_gl': 'blue', '2_gl_alt': 'blue', 'multi_gl': 'midnightblue'},
                      'ratio': {'2_gl': 'grey', '2_gl_alt': 'grey', 'multi_gl': 'black'},
                      '1a': {'2_gl': 'limegreen', '2_gl_alt': 'limegreen', 'multi_gl': 'green'},
                      'vib': {'2_gl': 'red', '2_gl_alt': 'red', 'multi_gl': 'darkred'},
                      '2': {'2_gl': 'indigo', '2_gl_alt': 'indigo', 'multi_gl': 'indigo'},
                      }
            fid_labels = {'2_gl': '2 GL', '2_gl_alt': '2 GL', 'multi_gl': '3 GL'}
            fig = plt.figure()
            # setup ebin(T) plot
            ax = fig.add_subplot(3, 1, 1)
            fig.subplots_adjust(hspace=0.15)
            #ax.set_xlabel('Temperature (K)', fontsize=fontsize_label)
            ax.tick_params(labelsize=fontsize_label)
            ax.set_xlim(xlim)
            ax.set_ylim(ylim_pp)
            ax.set_ylabel('-VDE (eV)', fontsize=fontsize_label)
            ax.grid()
            cluster_id = temp_ebin.pop('id')
            ax.text(0.8, 0.9, cluster_id, transform = ax.transAxes, fontsize=fontsize_clusterid,
                    horizontalalignment='right', verticalalignment='top')
            for fit_id, ebin in temp_ebin.items():
                for iso, v in ebin.items():
                    temp_mean = []
                    vde_mean = []
                    vde_dev = []
                    for t, vdes in sorted(v['mean'].items()):
                        temp_mean.append(t)
                        vde_mean.append(np.mean(vdes))
                        vde_dev.append(np.std(vdes))
                    ax.plot(temp_mean, -1*np.array(vde_mean), color='grey')
                    if plot_mean:
                        ax.errorbar(temp_mean, -1*np.array(vde_mean), vde_dev, fmt='s', markersize=markersize,
                                     color=colors[iso][fit_id],
                                     label='{} ({})'.format(iso_names[iso], fid_labels[fit_id]))
                    else:
                        ax.plot(v['T'], -1*np.array(v['ebin']), 's', markersize=markersize,
                                color=colors[iso][fit_id],
                                label='{} ({})'.format(iso_names[iso], fid_labels[fit_id]))
            
            leg = ax.legend(title='Peaks:', loc=1, fontsize=fontsize_label,
                            numpoints=1)
            leg.get_title().set_fontsize(fontsize_label)
            # setup diff(T) plot
            if temp_diff:
                ax.set_xticklabels([])
                ax_diff = fig.add_subplot(3, 1, 2)
                #ax_diff.set_xlabel('Temperature (K)', fontsize=fontsize_label)
                ax_diff.tick_params(labelsize=fontsize_label)
                ax_diff.axhline(0, color='black', lw=.4)
                ax_diff.set_xlim(ax.get_xlim())
                ax_diff.set_ylim([-15, 15])
                ax_diff.set_ylabel('$\Delta E_{T} - \Delta E_{10K}$ (10 meV)',
                                   fontsize=fontsize_label)
                ax_diff.grid()
                for fit_id, diff in temp_diff.items():
                    for diff, v in diff.items():
                        temp_mean = []
                        diff_mean = []
                        diff_dev = []
                        for t, diffs in sorted(v['mean'].items()):
                            temp_mean.append(t)
                            diff_mean.append(np.mean(diffs))
                            diff_dev.append(np.std(diffs))
                        # plot grey guides
                        ax_diff.plot(temp_mean, np.array(diff_mean)*100, color='grey')
                        # get label names
                        p1, p2 = diff.split('_')[1], diff.split('_')[2]
                        #plot_label = '$E_{' + iso_names[p2] + '}-E_{' + iso_names[p1] + '}$ (' + fid_labels[fit_id] + ')'
                        if plot_mean:
                            ax_diff.errorbar(temp_mean, np.array(diff_mean)*100,
                                             np.array(diff_dev)*100, fmt='s', markersize=markersize,
                                             color=colors['ratio'][fit_id],
                                             label='{}, {} ({})'.format(iso_names[p1],
                                                                       iso_names[p2],
                                                                       fid_labels[fit_id]))                  
                        else:
                            ax_diff.plot(v['T'], np.array(v['diff'])*100, 's', markersize=markersize,
                                         color=colors['ratio'][fit_id],
                                         label='{}, {} ({})'.format(iso_names[p1],
                                                                   iso_names[p2],
                                                                   fid_labels[fit_id]))
                leg_diff = ax_diff.legend(title='Peaks:', loc=1, fontsize=fontsize_label,
                                          numpoints=1)
                leg_diff.get_title().set_fontsize(fontsize_label)
            # setup ratio(T) plot
            if temp_ratio:
                ax_diff.set_xticklabels([])
                ax_ratio = fig.add_subplot(3, 1, 3)
                ax_ratio.set_xlabel('Temperature (K)', fontsize=fontsize_label)
                ax_ratio.tick_params(labelsize=fontsize_label)
                ax_ratio.axhline(50, color='black', lw=.4)
                ax_ratio.set_xlim(ax.get_xlim())
                ax_ratio.set_ylim(ylim_ph)
                ax_ratio.set_ylabel('prop. int. (%)', fontsize=fontsize_label)
                ax_ratio.grid()
                for fit_id, ratio in temp_ratio.items():
                    for ratio, v in ratio.items():
                        temp_mean = []
                        ratio_mean = []
                        ratio_dev = []
                        for t, ratios in sorted(v['mean'].items()):
                            temp_mean.append(t)
                            ratio_mean.append(np.mean(ratios))
                            ratio_dev.append(np.std(ratios))
                        # plot grey guides
                        ax_ratio.plot(temp_mean, np.array(ratio_mean)*100, color='grey')
                        ax_ratio.plot(temp_mean, (1-np.array(ratio_mean))*100, color='grey')
                        # get label names
                        iso1 = ratio.split('/')[0]
                        iso2 = ratio.split('/')[1]
                        if plot_mean:
                            ax_ratio.errorbar(temp_mean, np.array(ratio_mean)*100,
                                              np.array(ratio_dev)*100,
                                              fmt='s', markersize=markersize,
                                              color=colors[iso1][fit_id],
                                              label='{} ({})'.format(iso_names[iso1],
                                                                     fid_labels[fit_id]))
                            ax_ratio.errorbar(temp_mean, (1-np.array(ratio_mean))*100,
                                              np.array(ratio_dev)*100,
                                              fmt='s', markersize=markersize,
                                              color=colors[iso2][fit_id],
                                              label='{} ({})'.format(iso_names[iso2],
                                                                     fid_labels[fit_id]))
                        else:
                            ax_ratio.plot(v['T'], np.array(v['ratio'])*100, 's',
                                          markersize=markersize,
                                          color=colors[iso1][fit_id],
                                          label='{} ({})'.format(iso_names[iso1],
                                                                 fid_labels[fit_id]))
                            ax_ratio.plot(v['T'], (1-np.array(v['ratio']))*100, 's',
                                          markersize=markersize,
                                          color=colors[iso2][fit_id],
                                          label='{} ({})'.format(iso_names[iso2],
                                                                 fid_labels[fit_id]))
                leg_ratio = ax_ratio.legend(title='Peaks:', loc=1, fontsize=fontsize_label,
                                            numpoints=1)
                leg_ratio.get_title().set_fontsize(fontsize_label)
            
            return fig
        
        # get data for plots
        add_fit_ids = list(fit_ids) # somwhow we need to make a copy here (?)
        if self.fit_id not in add_fit_ids:
            add_fit_ids.append(self.fit_id)
        ebin_dict = {}
        diff_dict = {} 
        diff_ref = {}
        ratio_dict = {}
        for s in self.dbanswer:
            cs = spec_from_specdatadir(self.cfg, s[str('dataStorageLocation')])
            cn = cs.mdata.data('clusterBaseUnitNumber')
            ct = cs.mdata.data('trapTemp')
            for fit_id in add_fit_ids:
                cic = cs._assort_fit_peaks(fit_id)
                # populate ebin_dict
                for iso in iso_keys:
                    if iso in cic.keys():
                        if cn not in ebin_dict.keys():
                            ebin_dict[cn] = {'id': cs.view._pretty_format_clusterid(),
                                             fit_id: {iso: {'T': [ct], 'ebin': [cic[iso][0]],
                                                            'mean': {ct: [cic[iso][0]]}
                                                            }
                                                      }
                                             }
                        if fit_id not in ebin_dict[cn]:
                            ebin_dict[cn][fit_id] = {iso: {'T': [ct], 'ebin': [cic[iso][0]],
                                                            'mean': {ct: [cic[iso][0]]}
                                                            }
                                                     }
                        if iso in ebin_dict[cn][fit_id].keys():
                            ebin_dict[cn][fit_id][iso]['T'].append(ct)
                            ebin_dict[cn][fit_id][iso]['ebin'].append(cic[iso][0])
                            if ct in ebin_dict[cn][fit_id][iso]['mean']:
                                ebin_dict[cn][fit_id][iso]['mean'][ct].append(cic[iso][0])
                            else:
                                ebin_dict[cn][fit_id][iso]['mean'][ct] = [cic[iso][0]]
                        else:
                            ebin_dict[cn][fit_id][iso] = {'T': [ct], 'ebin': [cic[iso][0]],
                                                  'mean': {ct: [cic[iso][0]]}}
                            
                # populate diff_dict
                i = 0
                while i+1 < len(iso_keys):
                    k1, k2 = iso_keys[i], iso_keys[i+1]
                    diff_id = 'd_{}_{}'.format(k1, k2)
                    i += 1
                    if k1 in cic.keys() and k2 in cic.keys():
                        'TODO: use mean of diff_ref if plot_mean.'
                        if cn in diff_ref:
                            if diff_id in diff_ref[cn].keys():
                                diff = diff_ref[cn][diff_id] - (cic[k1][0] - cic[k2][0])
                            else:
                                diff = 0
                                diff_ref[cn][diff_id] = cic[k1][0] - cic[k2][0]
                        else:
                            diff = 0
                            diff_ref[cn] = {diff_id: cic[k1][0] - cic[k2][0]}
                        if cn not in diff_dict.keys():
                            diff_dict[cn] = {}
                        if fit_id not in diff_dict[cn]:
                            diff_dict[cn][fit_id] = {}
                        if diff_id in diff_dict[cn][fit_id].keys():
                            diff_dict[cn][fit_id][diff_id]['T'].append(ct)
                            diff_dict[cn][fit_id][diff_id]['diff'].append(diff)
                            if ct in diff_dict[cn][fit_id][diff_id]['mean']:
                                diff_dict[cn][fit_id][diff_id]['mean'][ct].append(diff)
                            else:
                                diff_dict[cn][fit_id][diff_id]['mean'][ct] = [diff]
                        else:
                            diff_dict[cn][fit_id][diff_id] = {'T': [ct], 'diff': [diff],
                                                              'mean': {ct: [diff]}}
                            
                # populate ratio_dict
                for c in combinations(iso_keys, 2):
                    if c[0] in cic.keys() and c[1] in cic.keys():
                        ratio_str = '{}/{}'.format(c[0], c[1])
                        ratio =cic[c[0]][1]/(cic[c[0]][1] + cic[c[1]][1])
                        if cn not in ratio_dict:
                            ratio_dict[cn] = {}
                        if fit_id not in ratio_dict[cn]:
                            ratio_dict[cn][fit_id] = {}
                        if ratio_str in ratio_dict[cn][fit_id].keys():
                            ratio_dict[cn][fit_id][ratio_str]['T'].append(ct)
                            ratio_dict[cn][fit_id][ratio_str]['ratio'].append(ratio)
                            if ct in ratio_dict[cn][fit_id][ratio_str]['mean']:
                                ratio_dict[cn][fit_id][ratio_str]['mean'][ct].append(ratio)
                            else:
                                ratio_dict[cn][fit_id][ratio_str]['mean'][ct] = [ratio]
                        else:
                            ratio_dict[cn][fit_id][ratio_str] = {'T': [ct], 'ratio': [ratio],
                                                                 'mean': {ct: [ratio]}}
                        
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
                
            fig = plot_single_size(e, dd, rd, ylim_pp=ylim_pp, ylim_ph=ylim_ph,
                                   plot_mean=plot_mean)
                
            if fname_prefix is None:
                fig.show()
            else:
                fname = '{}_w{}.pdf'.format(fname_prefix, n)
                self._export(fname=fname, export_dir=export_dir, size=size, figure=fig,
                             twin_axes=False, xy_labels=True)
            
            
    def plot_temp_lineshape(self, fit_ids=['2_gl'], fname_prefix=None,
                            export_dir=os.path.expanduser('~'), size=[20,14],
                            fontsize_clusterid=28, fontsize_label=12, markersize=6,
                            xlim=[0,425], ylim=None, id_pos='right', show_legend=True,
                            plot_mean=True):
         
        def plot_single_size(ls_par, n, id_pos, show_legend, plot_mean):
            cluster_id = ls_par.pop('id')
            colors = {'fwhm': {'2_gl': 'blue', '2_gl_alt': 'blue', 'multi_gl': 'midnightblue'},
                      'sg': {'2_gl': 'grey', '2_gl_alt': 'grey', 'multi_gl': 'black'},
                      'sl': {'2_gl': 'limegreen', '2_gl_alt': 'limegreen', 'multi_gl': 'green'},
                      }
            fid_labels = {'2_gl': '2 GL', '2_gl_alt': '2 GL', 'multi_gl': '3 GL'}
            
            fig = plt.figure()
            # setup lower axis
            ax = fig.add_subplot(1, 1, 1)
            ax.set_xlabel('Temperature (K)', fontsize=fontsize_label)
            ax.tick_params(labelsize=fontsize_label)
            ax.set_ylabel('fwhm, $\sigma_G$, $\sigma_L$ (eV)', fontsize=fontsize_label)
            ax.grid()
            for fit_id, t_par in ls_par.items():
                temp = []
                temp_mean = []
                fwhm = []
                fwhm_mean = []
                fwhm_dev = []
                sg = []
                sg_mean = []
                sg_dev = []
                sl = []
                sl_mean = []
                sl_dev = []
                for t, pars in sorted(t_par.items()):
                    # populate single point data lists
                    for i in range(len(pars['fwhm'])):
                        temp.append(t)
                        fwhm.append(pars['fwhm'][i])
                        sg.append(pars['sg'][i])
                        sl.append(pars['sl'][i])
                    temp_mean.append(t)
                    fwhm_mean.append(np.mean(pars['fwhm']))
                    fwhm_dev.append(np.std(pars['fwhm']))
                    sg_mean.append(np.mean(pars['sg']))
                    sg_dev.append(np.std(pars['sg']))
                    sl_mean.append(np.mean(pars['sl']))
                    sl_dev.append(np.std(pars['sl']))
                # plot grey lines
                ax.plot(temp_mean, fwhm_mean, color='grey')
                ax.plot(temp_mean, sg_mean, color='grey')
                ax.plot(temp_mean, sl_mean, color='grey')
                # data points
                if plot_mean:
                    ax.errorbar(temp_mean, fwhm_mean, fwhm_dev, fmt='s', markersize=markersize,
                                label='fwhm ({})'.format(fid_labels[fit_id]),
                                color=colors['fwhm'][fit_id], capsize=markersize/2)
                    ax.errorbar(temp_mean, sg_mean, sg_dev, fmt='s', markersize=markersize,
                                label='$\sigma_G$ ({})'.format(fid_labels[fit_id]),
                                color=colors['sg'][fit_id], capsize=markersize/2)
                    ax.errorbar(temp_mean, sl_mean, sl_dev, fmt='s', markersize=markersize,
                                label='$\sigma_L$ ({})'.format(fid_labels[fit_id]),
                                color=colors['sl'][fit_id], capsize=markersize/2)
                else:
                    ax.plot(temp, fwhm, 's', markersize=markersize,
                            label='fwhm ({})'.format(fid_labels[fit_id]),
                            color=colors['fwhm'][fit_id])
                    ax.plot(temp, sg, 's', markersize=markersize,
                            label='$\sigma_G$ ({})'.format(fid_labels[fit_id]),
                            color=colors['sg'][fit_id])
                    ax.plot(temp, sl, 's', markersize=markersize,
                            label='$\sigma_L$ ({})'.format(fid_labels[fit_id]),
                            color=colors['sl'][fit_id])

            ax.set_xlim(xlim)
            if ylim:
                ax.set_ylim(ylim)
            #ax.axhline(1, color='black', lw=.4)
            ax.text(0.98, 0.93, cluster_id, transform = ax.transAxes, fontsize=fontsize_clusterid,
                    horizontalalignment='right', verticalalignment='top')
            if show_legend:
                leg = ax.legend(title='Peak shape parameter:', loc=4, fontsize=fontsize_label,
                                numpoints=1)
                leg.get_title().set_fontsize(fontsize_label)    
            if fname_prefix is None:
                fig.show()
            else:
                fname = '{}_w{}.pdf'.format(fname_prefix, n)
                self._export(fname=fname, export_dir=export_dir, size=size, figure=fig,
                             twin_axes=False, xy_labels=True)
         
        ls_par_dict = {}    
        for s in self.dbanswer:
            cs = spec_from_specdatadir(self.cfg, s[str('dataStorageLocation')])
            cn = cs.mdata.data('clusterBaseUnitNumber')
            ct = cs.mdata.data('trapTemp')
            
            
            # create cluster size key
            if cn not in ls_par_dict:
                ls_par_dict[cn] = {}
                # add cluster id
                ls_par_dict[cn]['id'] = cs.view._pretty_format_clusterid()
            
            if self.fit_id not in fit_ids:
                fit_ids.append(self.fit_id)
            for fid in fit_ids:
                if fid in cs.mdata.data('fitData').keys():
                    if fid not in ls_par_dict[cn]:
                        ls_par_dict[cn][fid] = {} #'T': [], 'fwhm': [], 'sg': [], 'sl': []}
                    if ct not in ls_par_dict[cn][fid]:
                        ls_par_dict[cn][fid][ct] = {'fwhm': [], 'sg': [], 'sl': []}
                    cfwhm, csigmas = cs._get_peakshape_par('par', fid, width=True, width_pars=True)
                    #ls_par_dict[cn][fid]['T'].append(ct)
                    ls_par_dict[cn][fid][ct]['fwhm'].append(cfwhm)
                    ls_par_dict[cn][fid][ct]['sg'].append(csigmas[0])
                    ls_par_dict[cn][fid][ct]['sl'].append(csigmas[1])

                 
        for n, v in ls_par_dict.items():
            plot_single_size(v, n, id_pos=id_pos, show_legend=show_legend, plot_mean=plot_mean)
            
                
            


    def plot_offset_energy_ratio(self, offset_peaks=['1a', '1b'], ref_fit_id=None,
                                 show_single_points=False, fname=None,
                                 export_dir=os.path.expanduser('~'), size=[20,14],
                                 fontsize_label=12, markersize=6, color='blue', xlim=None,
                                 ylim=None, error_lw=1, ref_temp_range=None):
        # this only makes sense for heavy water
        if not self.heavy_water:
            raise ValueError('Only applicable for heavy water.')
        fit_id = self._eval_fit_id()
        if not ref_fit_id:
            ref_fit_id=fit_id
 
        energy_ratio = []
        energy_ratio_by_size = {}
        peak_stats = {}
        # populate peak lists
        for s in self.dbanswer:
            d2o_isomers = {'2': [], '1a': [], '1b': [], 'vib': []} 
            cs = spec_from_specdatadir(self.cfg, s[str('dataStorageLocation')])
            cn = cs.mdata.data('clusterBaseUnitNumber')
            #peak_list = [cs.ebin(p) for p in cs.mdata.data('fitData')[fit_id]['par'][:-2:2]]
            peak_list = [cs.ebin(peak[0]) for peak in cs._get_fit_peaks(fit_par_type='par',
                                                                        fit_id=fit_id)]
            # sort d2o isomers
            d2o_lin_par = cs._get_isomer_limits_linpar(fit_id)
            self._sort_peaks(cn, d2o_lin_par, peak_list,
                             d2o_isomers['2'], d2o_isomers['1a'], d2o_isomers['1b'],
                             d2o_isomers['vib'])
            d2o_p1 = d2o_isomers[offset_peaks[0]]
            d2o_p2 = d2o_isomers[offset_peaks[1]]
            if len(d2o_p1)==1 and len(d2o_p2)==1:
                d2o_dE = np.abs(d2o_p1[0][1] - d2o_p2[0][1])
                # add h20 ref
                comp_list = SpecPeWaterFitList(self.cfg, clusterBaseUnitNumber=cn,
                                               fit_id=ref_fit_id, trapTempRange=ref_temp_range)
                for rs in comp_list.dbanswer:
                    h2o_isomers = {'2': [], '1a': [], '1b': [], 'vib': []}
                    crs = spec_from_specdatadir(self.cfg,rs[str('dataStorageLocation')])
                    #ref_peak_list = [crs.ebin(p) for p in crs.mdata.data('fitData')[ref_fit_id]['par'][:-2:2]]
                    ref_peak_list = [crs.ebin(peak[0]) for peak in 
                                     crs._get_fit_peaks(fit_par_type='par',
                                                        fit_id=ref_fit_id)]
                    h2o_lin_par = cs._get_isomer_limits_linpar(fit_id)
                    self._sort_peaks(cn, h2o_lin_par, ref_peak_list,
                                     h2o_isomers['2'], h2o_isomers['1a'], h2o_isomers['1b'],
                                     h2o_isomers['vib'])
                    h2o_p1 = h2o_isomers[offset_peaks[0]]
                    h2o_p2 = h2o_isomers[offset_peaks[1]]
                    if len(h2o_p1)==1 and len(h2o_p2)==1:
                        h2o_dE = np.abs(h2o_p1[0][1] - h2o_p2[0][1])
                        energy_ratio.append([cn, h2o_dE/d2o_dE])
                        if cn in energy_ratio_by_size.keys():
                            energy_ratio_by_size[cn].append(h2o_dE/d2o_dE)
                        else:
                            energy_ratio_by_size[cn] = [h2o_dE/d2o_dE]
                             
                        if cn not in peak_stats.keys():
                            peak_stats[cn] = [[], [], [], [], [], [], []]
                             
                        peak_stats[cn][0].append(h2o_p1[0][1])
                        peak_stats[cn][1].append(h2o_p2[0][1])
                        peak_stats[cn][2].append(h2o_dE)
                        peak_stats[cn][3].append(d2o_p1[0][1])
                        peak_stats[cn][4].append(d2o_p2[0][1])
                        peak_stats[cn][5].append(d2o_dE)
                        peak_stats[cn][6].append(h2o_dE/d2o_dE)
        plot_data = np.array([[ps[0], ps[1], ps[0]**(-1/3)] for ps in energy_ratio]).transpose()
        plot_data_mean = [[k, np.mean(item), np.std(item)] for k,item in energy_ratio_by_size.items()]
        plot_data_mean.sort()
        plot_data_mean = np.array(plot_data_mean).transpose()
        # create plot
        fig = plt.figure()
        # setup lower axis
        ax = fig.add_subplot(1, 1, 1)
        ax.set_xlabel('number of water molecules (n)', fontsize=fontsize_label)
        ax.tick_params(labelsize=fontsize_label)
        if xlim:
            ax.set_xlim(xlim[0], xlim[1])
        if ylim:
            ax.set_ylim(ylim[0], ylim[1])
        ax.set_ylabel('$\Delta E_{H_2O}/\Delta E_{D_2O}$', fontsize=fontsize_label)
        ax.xaxis.grid(True)
        # plot lines for 1 and sqrt(2)
        ax.axhline(1, color='black', lw=.4)
        ax.axhline(np.sqrt(2), color='black', lw=.4)
        # plot data
        if show_single_points:
            ax.plot(plot_data[0], plot_data[1], 's', color='limegreen',
                    markersize=markersize)
        ax.plot(plot_data_mean[0], plot_data_mean[1], color='grey')
        ax.errorbar(plot_data_mean[0], plot_data_mean[1], plot_data_mean[2], fmt='s',
                    color=color, markersize=markersize, capsize=markersize/2, lw=error_lw)
        if fname is None:
            fig.show()
        else:
            self._export(fname=fname, export_dir=export_dir, size=size, figure=fig,
                         twin_axes=False, xy_labels=True)
         
        return peak_stats, energy_ratio_by_size
            
        
            
        
        
    def refit(self, new_fit_id=None, fit_par=None, cutoff=None, asym_par=None,
              use_boundaries=True):
        '''TODO: inherit from fit or use super()'''
        ref_fit_id = self._eval_fit_id()
        if not new_fit_id:
            new_fit_id = ref_fit_id
        for s in self.dbanswer:
            cs = spec_from_specdatadir(self.cfg,s[str('dataStorageLocation')])
            cs._refit(fit_id=new_fit_id, ref_fit_id=ref_fit_id, fit_par=fit_par,
                      cutoff=cutoff, asym_par=asym_par, use_boundaries=use_boundaries,
                      commit_after=True)
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
            cs = spec_from_specdatadir(self.cfg, s['dataStorageLocation'])
            if gauge_ref is not None:
                cs.gauge(gauge_ref, refit=refit, commit_after=commit_after,
                         ignore_wavelength=ignore_wavelength)
            elif 'gaugeRef' in cs.mdata.data().keys():
                cs.gauge(cs.mdata.data('gaugeRef'), refit=refit,
                         commit_after=commit_after, ignore_wavelength=ignore_wavelength)
            else:
                print('Spec has no gauge reference yet; skipping.')
            
            del cs
            
            
    def export_single_plots(self, plot_fct, export_dir='~/test', latex_fname=None,
                            overwrite=True, linewidth=.8, layout=[8,4], size='latex',
                            latex=True, firstpage_offset=0, margins=None,
                            xlabel_str='Binding energy (eV)', skip_plots=False,
                            **keywords):
        '''Specialized version using fit_id'''
        SpecList.export_single_plots(self, plot_fct=plot_fct, export_dir=export_dir,
                                     latex_fname=latex_fname, overwrite=overwrite,
                                     linewidth=linewidth, layout=layout, size=size,
                                     latex=latex, firstpage_offset=firstpage_offset,
                                     margins=margins,
                                     xlabel_str=xlabel_str, skip_plots=skip_plots,
                                     fit_id=self.fit_id, **keywords)  




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
        print_answer(self.dbanswer, self.spec_type)
        self.pfile_list = [row['dataStorageLocation'] for row in self.dbanswer]
        self.view = viewlist.ViewMsList(self)


