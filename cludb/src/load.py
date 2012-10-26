from spec import *
#import config
#import MdataUtils
#import pickle
#import os
#import numpy as np


#def sha1Unique(mdata):
#    return db.tableHas(mdata['specType'], ['sha1', mdata['sha1']])


def fileStoragePossible(mdata):
    paths = [mdata['datFile'], mdata['pickleFile']]
    if 'cfgFile' in mdata:
        paths.append(mdata['cfgFile'])
    
    try:
        for p in paths:
            if os.path.exists(p):
                raise ValueError, 'Import error: %s already exists' % p
    except:
        filestoragepossible = False
        raise
    else:
        filestoragepossible = True
    finally:
        return filestoragepossible


def archive(mdata):
    """Move raw data file(s) *.dat (and *.cfg) to raw data archive.
    Update mdata with file location.
    """
    old_file = mdata['datFileOrig']
    new_file = mdata['datFile']
    '''TODO: catch io exceptions'''
    os.rename(old_file, new_file)
    movedFiles = [[new_file, old_file]]
        
    
    if 'cfgFileOrig' in mdata:
        old_cfg = mdata['cfgFileOrig']
        new_cfg = mdata['cfgFile']
        os.rename(old_cfg, new_cfg)
        movedFiles.append([new_cfg, old_cfg])
    
    return movedFiles


def moveBack(movedFiles):
    for pair in movedFiles:
        os.rename(pair[0], pair[1])

 
def importLegacyData(datFiles, commonMdata={}):
    '''Build a list, so we can work with lists only'''
    datFileList = []
    if type(datFiles) is list:
        datFileList.extend(datFiles)
    else:
        datFileList.append(datFiles)
    
    '''Build a list of spec objects'''
    specMap = {'ms': mSpec, 'pes': peSpec, 'pfs': pfSpec}
    specList = []
    movedFiles =[]
    failedImports = []
    '''TODO: adapt for more db'''
    with Db('casi') as db:
        for datFile in datFileList:
            #print 'Importing: '+datFile+' with ', commonMdata
            try:
                mi = LegacyData(datFile, commonMdata)
            except:
                failedImports.append([datFile, 'LegacyData creation failed'])
                #raise
                continue
            if not db.tableHasSha1(mi.mdata.data('specType'), mi.mdata.data('sha1')):
                if fileStoragePossible(mi.mdata.data()):
                    #print os.path.basename(datFile) + '''ready to convert ...
                    #'''
                    try:
                        moved = archive(mi.mdata.data())
                        movedFiles.extend(moved)
                        # init spec obj
                        mdata = mi.mdata.data()
                        ydata = {'rawIntensity': mi.data}
                        xdata = {'idx': np.arange(1,len(ydata['rawIntensity'])+1)}
                        spec = specMap[mdata['specType']](mdata, xdata, ydata)
                        spec.commitPickle()
                        
                    except:
                        '''TODO: add error reason'''
                        failedImports.append([datFile, 'An error occurred during: moving raw data or creating spec or committing pickle'])
                        #raise
                    else:
                        spec.mdata.rm('datFileOrig')
                        spec.mdata.rm('cfgFileOrig')
                        specList.append(spec)
                else:
                    #print 'some files already exist'
                    failedImports.append([datFile, 'Some raw files were already imported'])
            else:
                #print os.path.basename(datFile)+': Db has already sha1 entry'
                failedImports.append([datFile, 'Db has already entry with this sha1'])
                
        try:
            db.add(specList)
        except:
            # remove all files in our data dir, from this import
            moveBack(movedFiles)
            for spec in specList:
                os.remove(spec.mdata.data('pickleFile'))
            raise
        print 'Number of files to import: ', len(datFiles)
        print 'Number of Spectra to import: ', len(specList)
        print 'Number of files to move: ', len(movedFiles)
        print 'Number of failed imports: ', len(failedImports)
     
    return failedImports
    

            
def loadPickle(pickleFile):
    specMap = {'ms': mSpec, 'pes': peSpec, 'pfs': pfSpec}
    with open(pickleFile, 'rb') as f:
            mdata, xdata, ydata = pickle.load(f)
    if mdata['clusterBaseUnit'] == 'Pt' and mdata['specType'] == 'pes':
        spectrum = ptSpec(mdata, xdata, ydata)
    elif mdata['clusterBaseUnit'] in ['H2O', 'D2O'] and mdata['specType'] == 'pes':
        spectrum = waterSpec(mdata, xdata, ydata)
    else:
        spectrum = specMap[mdata['specType']](mdata, xdata, ydata)
    
    return spectrum





    
    
def load(loads):
    '''Make a list, so we can work only with lists'''
    loadList = []
    if type(loads) is list:
        loadList.extend(loads)
    else:
        loadList.append(loads)
        
    pickleSpecs = []
    legacyDataSpecs = []
    for item in loadList:
        if type(item) is str: # should be path to pickle file
            spec = loadPickle(item)
            pickleSpecs.append(spec)
        else:
            spec = loadLegacyData(item)
            legacyDataSpecs.append(spec)
    
    if len(legacyDataSpecs) > 0:
        Db.add(legacyDataSpecs)
        
    return pickleSpecs.extend(legacyDataSpecs)

    
    
    
    
    
    
    
    