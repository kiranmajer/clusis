from __future__ import unicode_literals
#import dbshell
import load

def updateMdata(specList, mdataDict, cfg):
    'TODO: open db only once'
    for entry in specList:
        print entry[str('pickleFile')]
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
            print item,



def listMdataPtFit(specList, cfg):
    items = ['recTime', 'datFile', 'fitParTof']
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
    
        mdataList.reverse()
        header = mdataList.pop()
        
            
            
