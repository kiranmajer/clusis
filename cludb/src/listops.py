#import dbshell
import load
import time
import os

def updateMdata(specList, mdataDict, cfg):
    'TODO: open db only once'
    for entry in specList:
        print(entry[str('pickleFile')])
        cs =  load.loadPickle(cfg, entry[str('pickleFile')])
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
    

def removeTag(specList, tag, cfg):
    for entry in specList:
        cs =  load.loadPickle(cfg, entry[str('pickleFile')])
        try:
            cs.mdata.removeTag(tag)
        except:
            raise
        else:
            cs.commit(update=True)
            
        del cs
        
        
def listMdata(specList, items, cfg):
    mdataList = [items]
    rowCount = 1
    for s in specList:
        cs = load.loadPickle(cfg,s[str('pickleFile')])
        mdataList.append([])
        for key in items:
            mdataList[rowCount].append(cs.mdata.data(key))
        rowCount += 1
            
        #print cs.mdata.data('datFile'), cs.mdata.data('recTime'), cs.mdata.data('fitParTof')[-1]
        del cs
    
    for row in mdataList:
        for item in row:
            print(item, end=' ')



def listMdataPtFit(specList, cfg):
    def formatRecTime(unixtime):
        return time.strftime('%d.%m.%Y', time.localtime(unixtime))
    
    def formatDatFile(datfile):
        return os.path.basename(datfile)
    
    items = ['recTime', 'datFile', 'fitParTof']
    mdataList = []
    rowCount = 0
    for s in specList:
        cs = load.loadPickle(cfg,s[str('pickleFile')])
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
        if not formatRecTime(row[0]) == lastDate:
            print('-'*70)
        print(formatRecTime(row[0]).ljust(10+3), end=' ')
        print(formatDatFile(row[1]).ljust(13+3), end=' ')
        print(str(round(row[2][-1],3)).ljust(7+3), end=' ')
        print(str(round(row[2][-2]*1e9,2)).ljust(10+3), end=' ')
        print(str(round(row[2][-3]*1e3,2)).ljust(6))
        lastDate = formatRecTime(row[0])
        
        
def regaugePt(specList,cfg):
    for s in specList:
        cs = load.loadPickle(cfg,s[str('pickleFile')])
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
    listMdataPtFit(specList,cfg)
    
    
def showAll(specList,cfg):
    sl=[]
    for s in specList:
        cs = load.loadPickle(cfg,s[str('pickleFile')])
        cs.view.showTofFit('fitParTof')
        sl.append(cs)
    return sl

def specList(slist,cfg):
    sl=[]
    for s in slist:
        cs = load.loadPickle(cfg,s[str('pickleFile')])
        sl.append(cs)
    return sl    
        
            
            
