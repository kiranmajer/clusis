import load_3f
from dbshell import Db
#import time
import os
#import viewlist
# for comparison methods
import numpy as np
import matplotlib.pyplot as plt
#from mpl_toolkits.axes_grid1 import host_subplot
#import mpl_toolkits.axisartist as AA
#import matplotlib.ticker as ticker
#from scipy.stats import linregress
#from itertools import combinations
import viewlist_3f



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
        self.spec_data_dir_list = [row['dataStorageLocation'] for row in self.dbanswer]
        self.view = viewlist_3f.ViewList(self)
        

#    def query(self, recTime=None, recTimeRange=None,
#              inTags=None, notInTags=None, datFileName=None):
#        with Db('casi', self.cfg) as db:
#            self.dbanswer = db.query(self.spec_type, recTime=recTime, recTimeRange=recTimeRange,
#                                     inTags=inTags, notInTags=notInTags, datFileName=datFileName)

    def get_spec(self, number):
        #ata_dir = self.dbanswer[number]['pickleFile'].rstrip('.pickle')
        spec = load_3f.spec_from_specdatadir(self.cfg,
                                          self.dbanswer[number]['dataStorageLocation'])
        #spec = load.load_pickle_3f(self.cfg, self.dbanswer[number]['pickleFile'])
        return spec

    def update_mdata(self, mdataDict):
        'TODO: open db only once'
        for entry in self.dbanswer:
            print(entry['dataStorageLocation'])
            #cs = load.load_pickle_3f(self.cfg, entry['pickleFile'])
            cs = load_3f.spec_from_specdatadir(self.cfg, entry['dataStorageLocation'])
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
            #cs = load.load_pickle_3f(self.cfg, entry['pickleFile'])
            cs = load_3f.spec_from_specdatadir(self.cfg, entry['dataStorageLocation'])
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
        for entry in self.dbanswer:
            #cs = load.load_pickle_3f(self.cfg, s['pickleFile'])
            cs = load_3f.spec_from_specdatadir(self.cfg, entry['dataStorageLocation'])
            values = [cs.mdata.data(k) for k in keys]
            print('{}:'.format(os.path.basename(cs.mdata.data('datFile'))), values)
            del cs
            
    def _export(self, fname='export.pdf', export_dir=os.path.expanduser('~'), size='p1h',
                figure=None, twin_axes=True, xy_labels=False):
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
        if twin_axes:
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
            #cs = load.load_pickle_3f(self.cfg, entry['pickleFile'])
            cs = load_3f.spec_from_specdatadir(self.cfg, entry['dataStorageLocation'])
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


class SpecTofList(SpecList):
    def __init__(self, cfg, clusterBaseUnit=None, recTime=None, recTimeRange=None,
                 inTags=None, notInTags=None, datFileName=None, hide_trash=True, order_by='recTime'):
        self.cfg = cfg
        self.spec_type = 'tof'
        with Db('3f', self.cfg) as db:
            self.dbanswer = db.query(self.spec_type, clusterBaseUnit=clusterBaseUnit,
                                     recTime=recTime, recTimeRange=recTimeRange, inTags=inTags,
                                     notInTags=notInTags, datFileName=datFileName,
                                     hide_trash=hide_trash, order_by=order_by)
        self.pfile_list = [row['dataStorageLocation'] for row in self.dbanswer]
        self.view = viewlist_3f.ViewTofList(self)
        
        



class SpecMList(SpecList):
    def __init__(self, cfg, clusterBaseUnit=None, recTime=None, recTimeRange=None,
                 inTags=None, notInTags=None, datFileName=None, hide_trash=True, order_by='recTime'):
        self.cfg = cfg
        self.spec_type = 'ms'
        with Db('3f', self.cfg) as db:
            self.dbanswer = db.query(self.spec_type, clusterBaseUnit=clusterBaseUnit,
                                     recTime=recTime, recTimeRange=recTimeRange, inTags=inTags,
                                     notInTags=notInTags, datFileName=datFileName,
                                     hide_trash=hide_trash, order_by=order_by)
        self.pfile_list = [row['dataStorageLocation'] for row in self.dbanswer]
        self.view = viewlist_3f.ViewMsList(self)


