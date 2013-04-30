from load import load_pickle
from dbshell import Db
import time
import os


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
                    cs._hv = cs.photonEnergy(cs.mdata.data('waveLength'))
                    'TODO: this can seriously mix up data!'
                    cs.calcSpec()
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
            print(str(row[1]*1e9).ljust(6+3), end=' ')
            print(format_recTime(row[2]).ljust(10+3), end=' ')
            print(format_fitpeaks(row[3]))
            last_size = row[0]
            






            
            
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
            
            
            
