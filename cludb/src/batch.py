from load import load_pickle
from dbshell import Db
import time
import os
# for comparison methods
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA


class Batch(object):
    def __init__(self, cfg, specType, clusterBaseUnit=None, clusterBaseUnitNumber=None,
                 clusterBaseUnitNumberRange=None, recTime=None, recTimeRange=None,
                 inTags=None, notInTags=None, datFileName=None, waveLength=None):
        self.cfg = cfg
        self.query(specType, clusterBaseUnit=clusterBaseUnit,
                   clusterBaseUnitNumber=clusterBaseUnitNumber,
                   clusterBaseUnitNumberRange=clusterBaseUnitNumberRange,
                   recTime=recTime, recTimeRange=recTimeRange,
                   inTags=inTags, notInTags=notInTags,
                   datFileName=datFileName, waveLength=waveLength)

        
    def query(self, specType, clusterBaseUnit=None, clusterBaseUnitNumber=None,
              clusterBaseUnitNumberRange=None, recTime=None, recTimeRange=None,
              inTags=None, notInTags=None, datFileName=None, waveLength=None):
        with Db('casi', self.cfg) as db:
            self.dbanswer = db.query(specType, clusterBaseUnit=clusterBaseUnit,
                                     clusterBaseUnitNumber=clusterBaseUnitNumber,
                                     clusterBaseUnitNumberRange=clusterBaseUnitNumberRange,
                                     recTime=recTime, recTimeRange=recTimeRange,
                                     inTags=inTags, notInTags=notInTags,
                                     datFileName=datFileName, waveLength=waveLength)
            
            
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
            
            
    def list_mdata_waterfit(self):
        def format_recTime(unixtime):
            return time.strftime('%d.%m.%Y', time.localtime(unixtime))
        
        def format_datFile(datfile):
            return os.path.basename(datfile)
        
        def format_fitpeaks(peaklist):
            return ', '.join(str(e) for e in peaklist)
        
        
        items = ['clusterBaseUnitNumber', 'waveLength', 'recTime', 'fitPar']
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
                    else:
                        mdataList[rowCount].append(cs.mdata.data(key))
                rowCount += 1
            else:
                print('{} not a fitted Water-Spec, skipping'.format(cs.mdata.data('datFile')))              
            #print cs.mdata.data('datFile'), cs.mdata.data('recTime'), cs.mdata.data('fitParTof')[-1]
            del cs
        
        print('size'.ljust(4+3), end=' ')
        print('lambda'.ljust(6+3), end=' ')
        print('recTime'.ljust(10+3), end=' ')
        print('Ebin of peaks [eV]')
        last_size = 0
        for row in mdataList:
            if not row[0] == last_size:
                print('-'*70)
            print(str(row[0]).ljust(4+3), end=' ')
            print(str(round(row[1]*1e9)).ljust(6+3), end=' ')
            print(format_recTime(row[2]).ljust(10+3), end=' ')
            print(format_fitpeaks(row[3]))
            last_size = row[0]
            


    def compare_water_fits(self):
        # methods to sort peak position to isomers
        def border_iso(size):
            linear_par = {'iso2': [[abs((2.525-2.075)/0.1), -2.525], [abs((2.525-2.075)/0.1), -2.525]],
                          'iso1a': [[abs((3-2.5)/0.1), 3], [abs((4.275-3.3)/0.1), -4.275]],
                          'iso1b': [[abs((3.3-2.9)/0.1), -3.3], [abs((4.5-3.6)/0.1), -4.5]]
                          }
            def b_part1(iso, size):
                return linear_par[iso][0][0]*size**(-1/3) + linear_par[iso][0][1]
            def b_part2(iso, size):
                return linear_par[iso][1][0]*size**(-1/3) + linear_par[iso][1][1]
            iso2 = b_part1('iso2', size) if size < 50 else b_part2('iso2', size)
            iso1a = b_part1('iso1a', size) if size < 50 else b_part2('iso1a', size)
            iso1b = b_part1('iso1b', size) if size < 50 else b_part2('iso1b', size)
            print('Border parameter for size {} are:'.format(str(size)), iso2, iso1a, iso1b)
            return iso2, iso1a, iso1b
        
        def sort_peaks(size, peak_list, p_2, p_1a, p_1b, p_vib):
            iso2, iso1a, iso1b = border_iso(size)
            for p in peak_list:
                if -1*p > iso2:
                    p_2.append([size, p])
                    print('p_2:', p_2)
                elif iso2 >= -1*p > iso1a:
                    p_1a.append([size, p])
                    print('p_1a:', p_1a)
                elif iso1a >= -1*p > iso1b:
                    p_1b.append([size, p])
                    print('p_1b:', p_1b)
                else:
                    p_vib.append([size, p])
                    print('p_vib:', p_vib)
                    
        def plot_comp(plot_data, fit_par):
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
            # plot fits
            xdata_fit = np.arange(0, 1, 0.1)
            for par_set in fit_par:
                lin_fit = np.poly1d(par_set)
                ax.plot(xdata_fit, lin_fit(xdata_fit), '--', color='grey')
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
        
        print('p_* are:', p_2, p_1a, p_1b, p_vib)
        plot_data = [ps for ps in [p_2, p_1a, p_1b, p_vib] if len(ps) > 0]
        plot_data = [np.array(ps).transpose() for ps in plot_data]
        plot_data = [np.vstack((ps, ps[0]**(-1/3))) for ps in plot_data]
        for ps in plot_data:
            ps[1] = ps[1]*-1
        print('plot_data:', plot_data)
        fit_data = [ps for ps in plot_data if len(ps[0]) > 1]
        print('fit_data:', fit_data)
        
        # linear fit
        fit_par = []
        for peak_set in fit_data:
            fitpar = np.polyfit(peak_set[2], peak_set[1], 1)
            fit_par.append(fitpar)
            
        plot_comp(plot_data, fit_par)
        
        


    
    
    
            
            
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
            
            
            
