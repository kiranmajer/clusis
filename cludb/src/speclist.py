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



class SpecList(object):
    def __init__(self, cfg, specType, recTime=None, recTimeRange=None,
                 inTags=None, notInTags=None, datFileName=None):
        self.cfg = cfg
        self.spec_type = specType
        print('Calling query with:', specType, recTime, recTimeRange)
        self.query( recTime=recTime, recTimeRange=recTimeRange,
                   inTags=inTags, notInTags=notInTags, datFileName=datFileName)
        self.pfile_list = [row['pickleFile'] for row in self.dbanswer]
        self.view = viewlist.ViewList(self)
        

    def query(self, recTime=None, recTimeRange=None,
              inTags=None, notInTags=None, datFileName=None):
        with Db('casi', self.cfg) as db:
            self.dbanswer = db.query(self.spec_type, recTime=recTime, recTimeRange=recTimeRange,
                                     inTags=inTags, notInTags=notInTags, datFileName=datFileName)

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
                if hasattr(cs, '_hv'):
                    cs._hv = cs._photon_energy(cs.mdata.data('waveLength'))
                    'TODO: this can seriously mix up data!'
                    cs.calc_spec_data()
            except:
                raise
            else:
                cs.commit(update=True)
                
            del cs
        
    def remove_tag(self, tag):
        for entry in self.dbanswer:
            cs = load_pickle(self.cfg, entry['pickleFile'])
            try:
                cs.mdata.remove_tag(tag)
            except ValueError:
                print('Key not applicable, skipping.')
            else:
                cs.commit(update=True)
                
            del cs








class Batch(object):
    def __init__(self, cfg, specType, clusterBaseUnit=None, clusterBaseUnitNumber=None,
                 clusterBaseUnitNumberRange=None, recTime=None, recTimeRange=None,
                 inTags=None, notInTags=None, datFileName=None, waveLength=None, trapTemp=None,
                 trapTempRange=None):
        self.cfg = cfg
        self.query(specType, clusterBaseUnit=clusterBaseUnit,
                   clusterBaseUnitNumber=clusterBaseUnitNumber,
                   clusterBaseUnitNumberRange=clusterBaseUnitNumberRange,
                   recTime=recTime, recTimeRange=recTimeRange,
                   inTags=inTags, notInTags=notInTags,
                   datFileName=datFileName, waveLength=waveLength,
                   trapTemp=trapTemp, trapTempRange=trapTempRange)

        
    def query(self, specType, clusterBaseUnit=None, clusterBaseUnitNumber=None,
              clusterBaseUnitNumberRange=None, recTime=None, recTimeRange=None,
              inTags=None, notInTags=None, datFileName=None, waveLength=None,
              trapTemp=None, trapTempRange=None):
        with Db('casi', self.cfg) as db:
            self.dbanswer = db.query(specType, clusterBaseUnit=clusterBaseUnit,
                                     clusterBaseUnitNumber=clusterBaseUnitNumber,
                                     clusterBaseUnitNumberRange=clusterBaseUnitNumberRange,
                                     recTime=recTime, recTimeRange=recTimeRange,
                                     inTags=inTags, notInTags=notInTags,
                                     datFileName=datFileName, waveLength=waveLength,
                                     trapTemp=trapTemp, trapTempRange=trapTempRange)
            
            

            
            
    def list_temp(self):
        def format_recTime(unixtime):
            return time.strftime('%d.%m.%Y', time.localtime(unixtime))
        
        def format_datFile(datfile):
            return os.path.basename(datfile)
        
        items = ['clusterBaseUnitNumber', 'waveLength', 'recTime', 'datFile', 'trapTemp']
        mdataList = []
        rowCount = 0
        for s in self.dbanswer:
            cs = load_pickle(self.cfg,s[str('pickleFile')])        
            mdataList.append([])
            for key in items:
                if key in cs.mdata.data().keys():
                    mdataList[rowCount].append(cs.mdata.data(key))
                else:
                    mdataList[rowCount].append(0)
            rowCount += 1             
        print('size'.ljust(4+3), end=' ')
        print('lambda'.ljust(5+3), end=' ')
        print('recTime'.ljust(10+3), end=' ')
        print('datFile'.ljust(13+3), end=' ')
        print('trapTemp'.ljust(8))
        for row in mdataList:
            print(str(row[0]).ljust(4+3), end=' ')
            print(str(round(row[1]*1e9,1)).ljust(5+3), end=' ')
            print(format_recTime(row[2]).ljust(10+3), end=' ')
            print(format_datFile(row[3]).ljust(13+3), end=' ')
            print(str(round(row[4],1)).ljust(8))  
  
    
    
    def list_mdata_ptfit(self):
        def format_recTime(unixtime):
            return time.strftime('%d.%m.%Y', time.localtime(unixtime))
        
        def format_datFile(datfile):
            return os.path.basename(datfile)
        
        items = ['recTime', 'datFile', 'fitPar']
        mdataList = []
        rowCount = 0
        for s in self.dbanswer:
            cs = load_pickle(self.cfg,s[str('pickleFile')])
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
            'TODO: adapt for mdata flightLength.'
            print(str(round(1600*(1/np.sqrt(row[2][-1])-1),3)).ljust(12+3), end=' ')
            print(str(round(row[2][-2]*1e9,2)).ljust(10+3), end=' ')
            print(str(round(row[2][-3]*1e3,2)).ljust(6))
            lastDate = format_recTime(row[0])
            
            
    def compare_pt_fits(self):

        fig = plt.figure()
        #print 'Figure created.'
        ax = fig.add_subplot(1,1,1)
        ax.set_xlabel('tof ($\mu$s)')
        ax.set_ylabel('corrected tof ($\mu$s)')
        ax.grid()
        fx=np.arange(0, 10e-6, 1e-7)
        def g_time(xdata, lscale, Eoff, toff, pFactor):
            return 1/np.sqrt(lscale*(1/(xdata)**2 - Eoff/pFactor)) - toff        
        
        for s in self.dbanswer:
            cs = load_pickle(self.cfg,s[str('pickleFile')])
            if cs.mdata.data('specTypeClass') == 'specPePt' and \
            'background' not in cs.mdata.data('systemTags') and \
            'fitted' in cs.mdata.data('systemTags'):
                lscale = cs.mdata.data('fitPar')[-1]
                toff = cs.mdata.data('fitPar')[-2]
                Eoff = cs.mdata.data('fitPar')[-3]
                dat_filename = os.path.basename(cs.mdata.data('datFile'))
                ax.plot(fx*1e6,g_time(fx, lscale, Eoff, toff, cs._pFactor)*1e6, label=dat_filename)
                
        ax.legend(loc=2)
        fig.show()
    
            
    def list_mdata_waterfit(self):
        def format_recTime(unixtime):
            return time.strftime('%d.%m.%Y', time.localtime(unixtime))
        
        def format_datFile(datfile):
            return os.path.basename(datfile)
        
        def format_fitpeaks(peaklist):
            return ', '.join(str(e) for e in peaklist)
        
        
        items = ['clusterBaseUnitNumber', 'waveLength', 'recTime', 'fitCutoff', 'fitInfo', 'fitPar']
        mdataList = []
        rowCount = 0
        for s in self.dbanswer:
            cs = load_pickle(self.cfg,s[str('pickleFile')])
            if cs.mdata.data('specTypeClass') == 'specPeWater' and \
            'background' not in cs.mdata.data('systemTags') and \
            'fitted' in cs.mdata.data('systemTags'):
                mdataList.append([])
                for key in items:
                    if key == 'fitPar':
                        mdataList[rowCount].append([round(float(cs.ebin(p)),2) for p in cs.mdata.data(key)[:-2:2]])
                    elif key == 'fitInfo':
                        mdataList[rowCount].append(cs.mdata.data(key)[0])
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
              'chi2*3'.ljust(5+3),
              'Ebin of peaks [eV]')
        last_size = 0
        for row in mdataList:
            if not row[0] == last_size:
                print('-'*85)
            print(str(row[0]).ljust(4+3), 
                  str(round(row[1]*1e9)).ljust(6+3),
                  format_recTime(row[2]).ljust(10+3), end=' ')
            if row[3] is None:
                print('None'.ljust(6+3), end=' ')
            else:                                       
                print(str(round(row[3]*1e6, 2)).ljust(6+3), end=' ')
            print(str(round(row[4]*1e3, 3)).ljust(5+3),
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


    def compare_water_fits(self, plot_iso_borders=False, comp_data=None):
        # methods to sort peak position to isomers
        linear_par = {'iso2': [[abs((2-1.62)/0.1), -2.2]], #, [abs((2-1.62)/0.1), -2.25]],
                      'iso1a': [[abs((3.26-2.69)/0.1), -3.26]], #, [abs((3.3-2.71)/0.1), 3.3]],  #[abs((4.275-3.3)/0.1), -4.275]],
                      'iso1b': [[abs((3.8-3.2)/0.1), -3.77]] #, [abs((3.93-2.82)/0.1), -3.93]]   #[abs((4.5-3.6)/0.1), -4.5]]
                      }
        def border_iso(size):
            def b_part1(iso, size):
                return linear_par[iso][0][0]*size**(-1/3) + linear_par[iso][0][1]
            def b_part2(iso, size):
                return linear_par[iso][1][0]*size**(-1/3) + linear_par[iso][1][1]
            iso2 = b_part1('iso2', size) #if size < 50 else b_part2('iso2', size)
            iso1a = b_part1('iso1a', size) #if size < 50 else b_part2('iso1a', size)
            iso1b = b_part1('iso1b', size) #if size < 50 else b_part2('iso1b', size)
            #print('Border parameter for size {} are:'.format(str(size)), iso2, iso1a, iso1b)
            return iso2, iso1a, iso1b
        
        def sort_peaks(size, peak_list, p_2, p_1a, p_1b, p_vib):
            iso2, iso1a, iso1b = border_iso(size)
            for p in peak_list:
                if -1*p > iso2:
                    p_2.append([size, p])
                    #print('p_2:', p_2)
                elif iso2 >= -1*p > iso1a:
                    p_1a.append([size, p])
                    #print('p_1a:', p_1a)
                elif iso1a >= -1*p > iso1b:
                    p_1b.append([size, p])
                    #print('p_1b:', p_1b)
                else:
                    p_vib.append([size, p])
                    #print('p_vib:', p_vib)
                    
        def plot_comp(plot_data, fit_par, comp_data=None):
            fig = plt.figure()
            # setup lower axis
            ax = host_subplot(111, axes_class=AA.Axes)
            ax.set_xlabel('n$^{-1/3}$')
            ax.set_xlim(0,0.4)
            ax.set_ylabel('-VDE (eV)')
            ax.set_ylim(-4,0)
            # setup upper axis
            ax2 = ax.twin()
            ax2.set_xticks(np.array([10, 20,40,80,150,350,1000, 5000])**(-1/3))
            ax2.set_xticklabels(["10","20","40","80","150","350","1000","5000"])
            ax2.set_xlabel('number of water molecules')
            ax2.axis["right"].major_ticklabels.set_visible(False)
            ax2.grid(b=True)
            # plot data
            for peak_set in plot_data:
                ax.plot(peak_set[2], peak_set[1], 's')
            # plot comparison data
            if comp_data is not None:
                print('Got comparison data. Plotting...')
                for key, peak_set in comp_data.items():
                    ax.plot(peak_set[0], -1*peak_set[1], 'o', label=key)
                ax.legend(loc=2)
            # plot fits
            xdata_fit = np.arange(0, 1, 0.1)
            for par_set in fit_par:
                lin_fit = np.poly1d(par_set)
                ax.plot(xdata_fit, lin_fit(xdata_fit), '--', color='grey')
            # plot borders for isomer classification
            if plot_iso_borders:
                for par in linear_par.values():
                    ax.plot(xdata_fit, par[0][0]*xdata_fit + par[0][1], '-', color='grey')
            fig.show()
                
                
                
        # main method
        p_2 = []
        p_1a = []
        p_1b = []
        p_vib = []
        for s in self.dbanswer:
            cs = load_pickle(self.cfg,s[str('pickleFile')])
            if cs.mdata.data('specTypeClass') == 'specPeWater' and \
            'background' not in cs.mdata.data('systemTags') and \
            'fitted' in cs.mdata.data('systemTags'):
                peak_list = [cs.ebin(p) for p in cs.mdata.data('fitPar')[:-2:2]]
                sort_peaks(cs.mdata.data('clusterBaseUnitNumber'), peak_list, p_2, p_1a, p_1b, p_vib)
            else:
                print('{} not a fitted Water-Spec, skipping'.format(cs.mdata.data('datFile')))
            del cs
        
        #print('p_* are:', p_2, p_1a, p_1b, p_vib)
        plot_data = [ps for ps in [p_2, p_1a, p_1b, p_vib] if len(ps) > 0]
        plot_data = [np.array(ps).transpose() for ps in plot_data]
        plot_data = [np.vstack((ps, ps[0]**(-1/3))) for ps in plot_data]
        for ps in plot_data:
            ps[1] = ps[1]*-1
        #print('plot_data:', plot_data)
        fit_data = [ps for ps in plot_data if len(ps[0]) > 1]
        #print('fit_data:', fit_data)
        
        # linear fit
        fit_par = []
        for peak_set in fit_data:
            fitpar = np.polyfit(peak_set[2], peak_set[1], 1)
            fit_par.append(fitpar)
            
        plot_comp(plot_data, fit_par, comp_data=comp_data)
        
        


    
    
    
            
            
    def regauge_pt(self):
        for s in self.dbanswer:
            cs = load_pickle(self.cfg,s[str('pickleFile')])
            try:
                cs.gauge('tof', 
                         lscale=1.006,  #cs.mdata.data('fitParTof')[-1], 
                         Eoff=cs.mdata.data('fitParTof')[-3]#, 
                         #toff=63e-9  #cs.mdata.data('fitParTof')[-2]
                         )
            except:
                print(cs.mdata.data('datFile'), 'Fit failed.')
            else:
                cs.commit()
            del cs
        self.list_mdata_ptfit()
        
        
    def show_all(self):
        sl=[]
        for s in self.dbanswer:
            cs = load_pickle(self.cfg,s[str('pickleFile')])
            cs.view.showTofFit('fitParTof')
            sl.append(cs)
        return sl
    
    def list_of_specs(self, slist):
        sl=[]
        for s in slist:
            cs = load_pickle(self.cfg,s[str('pickleFile')])
            sl.append(cs)
        return sl    
            
            
            
