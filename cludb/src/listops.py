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
        
        
            