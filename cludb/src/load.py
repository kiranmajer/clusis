from spec import *
from legacyData import LegacyData
#import config
#import mdata
#import pickle
#import os
#import numpy as np


#def sha1Unique(mdata):
#    return db.tableHas(mdata['specType'], ['sha1', mdata['sha1']])

def is_filestorage_possible(mdata):
    paths = [mdata['datFile'], mdata['pickleFile']]
    if 'cfgFile' in mdata.keys():
        paths.append(mdata['cfgFile'])
    
    try:
        for p in paths:
            if os.path.exists(p):
                raise ValueError('Import error: %s already exists' % p)
    except:
        filestoragepossible = False
        raise
    else:
        filestoragepossible = True
    finally:
        return filestoragepossible
    
def abs_path(cfg, p):
    if not os.path.isabs(p):
        p = os.path.join(cfg.path['base'], p)
        
    return p


def archive(cfg, mdata):
    """Move raw data file(s) *.dat (and *.cfg) to raw data archive.
    Update mdata with file location.
    """
    old_file = abs_path(cfg, mdata['datFileOrig'])
    new_file = abs_path(cfg, mdata['datFile'])
    if not os.path.exists(os.path.dirname(new_file)):
        os.makedirs(os.path.dirname(new_file))
    '''TODO: catch io exceptions'''
    os.rename(old_file, new_file)
    movedFiles = [[new_file, old_file]]
        
    
    if 'cfgFileOrig' in mdata and mdata['specTypeClass'] not in ['spec']:
        old_cfg = abs_path(cfg, mdata['cfgFileOrig'])
        new_cfg = abs_path(cfg, mdata['cfgFile'])
        if not os.path.exists(os.path.dirname(new_cfg)):
            os.makedirs(os.path.dirname(new_cfg))
        os.rename(old_cfg, new_cfg)
        movedFiles.append([new_cfg, old_cfg])
    
    return movedFiles


def move_back(movedFiles):
    for pair in movedFiles:
        os.rename(pair[0], pair[1])


def ls_recursive(rootdir, suffix='.dat'):
    '''
    Populates a list with the full path of all files recursively found
    under rootdir with corresponding suffix.
     
    Returns: list.
    '''
    fileList = []
    rootdir = os.path.abspath(rootdir)
    if os.path.exists(rootdir):
        for root, subFolders, files in os.walk(rootdir):
            for f in files:
                if f.endswith(suffix) and root.find('selection') == -1: #skip selection folders since they contain doublets
                    fileList.append(os.path.join(root,f))
    else: raise IOError(2, 'No such file or directory: ' + rootdir)
            
    return fileList

 
def import_LegacyData(cfg, datFiles, spectype=None, commonMdata={}):
    '''Build a list, so we can work with lists only'''
    datFileList = []
    if type(datFiles) is list:
        datFileList.extend(datFiles)
    else:
        datFileList.append(datFiles)
    
    '''Build a list of spec objects'''
    typeclass_map = {'spec': Spec,
                     'specMs': SpecMs,
                     'specPe': SpecPe,
                     'specPePt': SpecPePt,
                     'specPeWater': SpecPeWater,
                     'specPf': SpecPf}
    specList = []
    movedFiles =[]
    failedImports = []
    sha1ToImport = []
    "TODO: adapt for more db"
    #with Db('casi', cfg) as db:
    db = Db('casi', cfg)
    for datFile in datFileList:
        print('Importing: '+datFile+' with ', commonMdata)
        try:
            mi = LegacyData(datFile, cfg, spectype, commonMdata)
        except Exception as e:
            print('LegacyData creation failed:', e)
            failedImports.append([datFile, 'LegacyData creation failed: {}'.format(e)])
            #raise
            continue
        if not db.table_has_sha1(mi.mdata.data('specType'), mi.mdata.data('sha1')) and mi.mdata.data('sha1') not in sha1ToImport:
            '''TODO: handle special files with identical sha1 (e.g. "flat line"-spectra).
            It might be interesting to have them in the db. Allow fake sha1 = sha1+unix 
            time stamp?'''
            if is_filestorage_possible(mi.mdata.data()):
                print(os.path.basename(datFile), '''ready to convert ...
                ''')
                try:
                    moved = archive(cfg, mi.metadata) # ! use metadata dict here since it has '...FileOrig' entries
                except Exception as e:
                    print('%s: Failed to archive raw data:'%datFile, e)
                    failedImports.append([datFile, 'Import error: Archive failed: %s.'%e])
                else:
                    try:                    
                        # init spec obj
                        mdata = mi.mdata.data()
                        ydata = {'rawIntensity': mi.data}
                        xdata = {'idx': np.arange(0,len(ydata['rawIntensity']))+1/2} # intensity for [i,i+1] will be displayed at i+0.5
                        spec = typeclass_map[mdata['specTypeClass']](mdata, xdata, ydata, cfg)
                        spec._commit_pickle()
                    except Exception as e:
                        print('%s failed to import:'%datFile, e)
                        failedImports.append([datFile, 'Import error: %s.'%e])
                        move_back(moved)
                        raise
                    else:
                        movedFiles.extend(moved)
                        spec._commit_pickle()
                        specList.append(spec)
                        sha1ToImport.append(mi.mdata.data('sha1'))
            else:
                #print 'some files already exist'
                failedImports.append([datFile, 'Some raw files were already imported'])
        else:
            #print os.path.basename(datFile)+': Db has already sha1 entry'
            failedImports.append([datFile, 'Db or earlier import has already entry with this sha1'])
            
    try:
        print('Starting db import ....')
        db.add(specList)
    except Exception as e:
        print('Db population failed:', e)
        # remove all files in our data dir, from this import
        move_back(movedFiles)
        for spec in specList:
            pickleFile = os.path.join(cfg.path['base'], spec.mdata.data('pickleFile'))
            os.remove(pickleFile)
        raise
    
    del db
        
    print('Number of files to import: ', len(datFiles))
    print('Number of Spectra to import: ', len(specList))
    print('Number of files to move: ', len(movedFiles))
    print('Number of failed imports: ', len(failedImports))
     
    return failedImports
    

            
def load_pickle(cfg, pickleFile):
    if not os.path.isabs(pickleFile):
        pickleFile = os.path.join(cfg.path['base'], pickleFile)
    typeclass_map = {'spec': Spec,
                 'specMs': SpecMs,
                 'specPe': SpecPe,
                 'specPePt': SpecPePt,
                 'specPeWater': SpecPeWater,
                 'specPf': SpecPf}
    with open(pickleFile, 'rb') as f:
            mdata, xdata, ydata = pickle.load(f)
#    if mdata['clusterBaseUnit'] == 'Pt' and mdata['specType'] == 'pes':
#        spectrum = SpecPePt(mdata, xdata, ydata, cfg)
#    elif mdata['clusterBaseUnit'] in ['H2O', 'D2O'] and mdata['specType'] == 'pes':
#        spectrum = SpecPeWater(mdata, xdata, ydata, cfg)
#    else:
    spectrum = typeclass_map[mdata['specTypeClass']](mdata, xdata, ydata, cfg)
    
    return spectrum





    
    
#def load(loads):
#    '''Make a list, so we can work only with lists'''
#    loadList = []
#    if type(loads) is list:
#        loadList.extend(loads)
#    else:
#        loadList.append(loads)
#        
#    pickleSpecs = []
#    legacyDataSpecs = []
#    for item in loadList:
#        if type(item) is str: # should be path to pickle file
#            spec = load_pickle(item)
#            pickleSpecs.append(spec)
#        else:
#            spec = loadLegacyData(item)
#            legacyDataSpecs.append(spec)
#    
#    if len(legacyDataSpecs) > 0:
#        Db.add(legacyDataSpecs)
#        
#    return pickleSpecs.extend(legacyDataSpecs)
#
#    
    
    
    
    
    
    
    