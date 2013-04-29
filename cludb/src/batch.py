#import dbshell
from load import load_pickle
import time
import os


class Batch(object):
    def __init__(self, spec_list, cfg):
        self.spec_list = spec_list
        self.cfg = cfg

    def update_mdata(self, mdataDict):
        'TODO: open db only once'
        for entry in self.spec_list:
            print(entry['pickleFile'])
            cs = load_pickle(self.cfg, entry['pickleFile'])
            try:
                cs.mdata.update(mdataDict)
                if hasattr(cs, '_hv'):
                    cs._hv = cs.photonEnergy(cs.mdata.data('waveLength'))
                    cs.calcSpec()
            except:
                raise
            else:
                cs.commit(update=True)
                
            del cs
        
    
    def remove_tag(self, tag):
        for entry in self.spec_list:
            cs = load_pickle(self.cfg, entry['pickleFile'])
            try:
                cs.mdata.remove_tag(tag)
            except:
                raise
            else:
                cs.commit(update=True)
                
            del cs
            
            
    #def list_mdata(specList, items):
    #    mdataList = [items]
    #    rowCount = 1
    #    for s in self.spec_list:
    #        cs = load_pickle(self.cfg,s[str('pickleFile')])
    #        mdataList.append([])
    #        for key in items:
    #            mdataList[rowCount].append(cs.mdata.data(key))
    #        rowCount += 1
    #            
    #        #print cs.mdata.data('datFile'), cs.mdata.data('recTime'), cs.mdata.data('fitParTof')[-1]
    #        del cs
    #    
    #    for row in mdataList:
    #        for item in row:
    #            print(item, end=' ')
    
    
    
    def list_mdata_ptfit(self):
        def format_recTime(unixtime):
            return time.strftime('%d.%m.%Y', time.localtime(unixtime))
        
        def format_datFile(datfile):
            return os.path.basename(datfile)
        
        items = ['recTime', 'datFile', 'fitPar']
        mdataList = []
        rowCount = 0
        for s in self.spec_list:
            cs = load_pickle(self.cfg,s[str('pickleFile')])
            mdataList.append([])
            for key in items:
                mdataList[rowCount].append(cs.mdata.data(key))
            rowCount += 1
                
            #print cs.mdata.data('datFile'), cs.mdata.data('recTime'), cs.mdata.data('fitParTof')[-1]
            del cs
        
        print('recTime'.ljust(10+3), end=' ')
        print('datFile'.ljust(13+3), end=' ')
        print('l_scale'.ljust(7+3), end=' ')
        print('t_off [ns]'.ljust(10+3), end=' ')
        print('E_off [meV]'.ljust(6))
        lastDate = ''
        for row in mdataList:
            if not format_recTime(row[0]) == lastDate:
                print('-'*70)
            print(format_recTime(row[0]).ljust(10+3), end=' ')
            print(format_datFile(row[1]).ljust(13+3), end=' ')
            print(str(round(row[2][-1],3)).ljust(7+3), end=' ')
            print(str(round(row[2][-2]*1e9,2)).ljust(10+3), end=' ')
            print(str(round(row[2][-3]*1e3,2)).ljust(6))
            lastDate = format_recTime(row[0])
            
            
    def list_mdata_waterfit(self):
        def format_recTime(unixtime):
            return time.strftime('%d.%m.%Y', time.localtime(unixtime))
        
        def format_datFile(datfile):
            return os.path.basename(datfile)
        
        def format_fitpeaks(peaklist):
            return [round(float(spec.ebin(p)),2) for p in peaklist[:-2:2]]
        
        items = ['recTime', 'datFile', 'fitPar']
        mdataList = []
        rowCount = 0
        for s in self.spec_list:
            cs = load_pickle(self.cfg,s[str('pickleFile')])
            mdataList.append([])
            for key in items:
                mdataList[rowCount].append(cs.mdata.data(key))
            rowCount += 1
                
            #print cs.mdata.data('datFile'), cs.mdata.data('recTime'), cs.mdata.data('fitParTof')[-1]
            del cs
        
        print('recTime'.ljust(10+3), end=' ')
        print('datFile'.ljust(13+3), end=' ')
        print('l_scale'.ljust(7+3), end=' ')
        print('t_off [ns]'.ljust(10+3), end=' ')
        print('E_off [meV]'.ljust(6))
        lastDate = ''
        for row in mdataList:
            if not format_recTime(row[0]) == lastDate:
                print('-'*70)
            print(format_recTime(row[0]).ljust(10+3), end=' ')
            print(format_datFile(row[1]).ljust(13+3), end=' ')
            print(str(round(row[2][-1],3)).ljust(7+3), end=' ')
            print(str(round(row[2][-2]*1e9,2)).ljust(10+3), end=' ')
            print(str(round(row[2][-3]*1e3,2)).ljust(6))
            lastDate = format_recTime(row[0])
            
            
            
    def regauge_pt(self):
        for s in self.spec_list:
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
        for s in self.spec_list:
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
            
            
            
