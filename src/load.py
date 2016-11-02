from spec import *
from spec_3f import *
# from legacyData import LegacyData not necessary for data other than CASI data
from rawData_3f import RawData_3f
from shutil import copy2
from traceback import print_tb
from sys import exc_info
from glob import glob
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
    'TODO: catch io exceptions'
    if not os.path.exists(new_file):
        os.rename(old_file, new_file)
        movedFiles = [[new_file, old_file]]
    else:
        raise ValueError('Archive contains already a file with this file name.')
        
    
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


def ls(rootdir, suffix='.csv', recursive=False):
    '''
    Populates a list with the full path of all files recursively found
    under rootdir with corresponding suffix.
     
    Returns: list.
    '''
    fileList = []
    rootdir = os.path.abspath(rootdir)
    if os.path.exists(rootdir):
        if recursive:
            for root, subFolders, files in os.walk(rootdir):
                for f in files:
                    if f.endswith(suffix) and root.find('selection') == -1: #skip selection folders since they contain doublets
                        fileList.append(os.path.join(root,f))
        else:
            fileList = glob(rootdir + '/*' + suffix)
    else: raise IOError(2, 'No such file or directory: ' + rootdir)
            
    return fileList


 
def import_LegacyData(cfg, datFiles, spectype=None, commonMdata={}, prefer_filename_mdata=False):
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
        print('\n######################')
        print('Importing: '+datFile+' with ', commonMdata)
        try:
            mi = LegacyData(datFile, cfg, spectype, commonMdata, prefer_filename_mdata=prefer_filename_mdata)
        except Exception as e:
            print('LegacyData creation failed:', e)
            failedImports.append([datFile, 'LegacyData creation failed: {}'.format(e)])
            print('Traceback:')
            print_tb(exc_info()[2])
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
    

def import_rawdata_3f(cfg, datFiles, spectype=None, commonMdata={},
                      channel_map={'ch1': 'rawVoltageSpec', 'ch2': 'rawVoltageRamp'}):
    '''Build a list, so we can work with lists only'''
    datFileList = []
    if type(datFiles) is list:
        datFileList.extend(datFiles)
    else:
        datFileList.append(datFiles)
    
    '''Build a list of spec objects'''
    typeclass_map = {'spec': Spec,
                     'specM': SpecM,
                     'specTof': SpecTof}
    specList = []
    movedFiles =[]
    failedImports = []
    sha1ToImport = []
    "TODO: adapt for more db"
    #with Db('casi', cfg) as db:
    db = Db('3f', cfg)
    for datFile in datFileList:
        print('\n######################')
        print('Importing: '+datFile+' with ', commonMdata)
        try:
            mi = RawData_3f(datFile, cfg, spectype, commonMdata)
        except Exception as e:
            print('LegacyData creation failed:', e)
            failedImports.append([datFile, 'LegacyData creation failed: {}'.format(e)])
            print('Traceback:')
            print_tb(exc_info()[2])
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
                        ydata = {channel_map['ch1']: mi.data_ch1}
                        ydata[channel_map['ch2']] = mi.data_ch2
                        xdata = {'idx': np.arange(0,len(ydata['rawVoltageSpec']))} # intensity for [i,i+1] will be displayed at i+0.5
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
                     'specPf': SpecPf,
                     }
    with open(pickleFile, 'rb') as f:
            mdata, xdata, ydata = pickle.load(f)
    
    # testing for correct mdata version
    mdata_converted = False
    if mdata['mdataVersion'] < cfg.mdata_version:
        if mdata['mdataVersion'] == 0.1:
            print('Old mdata version detected: 0.1.') 
            mdata = cfg.convert_mdata_v0p1_to_v0p2(mdata)
            
        if mdata['mdataVersion'] == 0.2:
            print('Old mdata version detected: 0.2.') 
            mdata = cfg.convert_mdata_v0p2_to_v0p3(mdata)
        
        mdata_converted = True
        
    spectrum = typeclass_map[mdata['specTypeClass']](mdata, xdata, ydata, cfg)
    if mdata_converted:
        spectrum.commit()
    
    return spectrum


def load_pickle_3f(cfg, pickleFile):
    if not os.path.isabs(pickleFile):
        pickleFile = os.path.join(cfg.path['base'], pickleFile)
    typeclass_map = {'spec': Spec,
                     'specM': SpecM,
                     'specTof': SpecTof,
                     }
    with open(pickleFile, 'rb') as f:
            mdata, xdata, ydata = pickle.load(f)
    
    # testing for correct mdata version
    mdata_converted = False
    if mdata['mdataVersion'] < cfg.mdata_version:
        raise ValueError('mdata converter missing!')
#         if mdata['mdataVersion'] == 0.1:
#             print('Old mdata version detected: 0.1.') 
#             mdata = cfg.convert_mdata_v0p1_to_v0p2(mdata)
#             
#         if mdata['mdataVersion'] == 0.2:
#             print('Old mdata version detected: 0.2.') 
#             mdata = cfg.convert_mdata_v0p2_to_v0p3(mdata)
        
        mdata_converted = True
        
    spectrum = typeclass_map[mdata['specTypeClass']](mdata, xdata, ydata, cfg)
    if mdata_converted:
        spectrum.commit()
    
    return spectrum


def import_cludb_dir(cfg, import_dir):
    '''Imports data from cludb dir structure: Import spectra from their pickle files
    into database; copy archive data (*.dat, *.cfg) to current archive dir.
    '''
    if not os.path.isabs(import_dir):
        import_dir = os.path.abspath(import_dir)
    # simple check for correct dir structure
    import_archive = os.path.join(import_dir, 'archive')
    import_data = os.path.join(import_dir, 'data')
    #import_db = os.path.join(import_dir,)
    if not os.path.isdir(import_archive) or not os.path.isdir(import_data):
        raise ValueError('"{}" does not seem to be a valid cludb dir.'.format(import_dir)) 
    # get pickle files for import
    pickle_list =  ls(import_data, suffix='.pickle', recursive=True)
    # process spectra
    for pfile in pickle_list:
        cs = load_pickle(cfg, pfile)
        cs.commit(update=False)
        for key in ['datFile', 'cfgFile']:
            if key in cs.mdata.data().keys():
                old_file = os.path.join(import_dir, cs.mdata.data(key))
                new_file = os.path.join(cfg.path['base'], cs.mdata.data(key))
                if not os.path.exists(os.path.dirname(new_file)):
                    os.makedirs(os.path.dirname(new_file))
                print('Copying {} to {} ...'.format(old_file, new_file))
                copy2(old_file, new_file)
                
    
def export_speclist(speclist, export_base_dir, export_dir='export'):
    if not os.path.isabs(export_base_dir):
        export_base_dir = os.path.abspath(export_base_dir)
    export_dir = os.path.join(export_base_dir, export_dir)
    try:
        os.makedirs(export_dir)
    except FileExistsError:
        print('Dir exists.')
    except:
        raise ValueError('Could not create dir at "{}".'.format(export_dir))
    if os.listdir(export_dir):
        raise ValueError('Export dir is not empty.')
    for s in speclist.dbanswer:
        cs = load_pickle(speclist.cfg, s['pickleFile'])
        for k in ['pickleFile', 'datFile', 'cfgFile']:
            if k in cs.mdata.data().keys():
                old_file = os.path.join(speclist.cfg.path['base'], cs.mdata.data(k))
                new_file = os.path.join(export_dir, os.path.basename(cs.mdata.data(k)))
                print('Copying {} to {} ...'.format(old_file, new_file))
                copy2(old_file, new_file)    


def import_export_speclist(cfg, export_dir):
    export_dir = os.path.abspath(export_dir)
    db = Db('casi', cfg)
    failedImports = []
    successfulImports = []
    filelist = ls(export_dir, suffix='.pickle', recursive=True)
    for pfile in filelist:
        print('Importing {} ...'.format(os.path.basename(pfile)))
        cs = load_pickle(cfg, pfile)
        laststep_successful = True
        if not db.table_has_sha1(cs.mdata.data('specType'), cs.mdata.data('sha1')):
            moved = []
            for k in ['datFile', 'cfgFile']:
                if k in cs.mdata.data().keys():
                    old_file = os.path.join(export_dir, os.path.basename(cs.mdata.data(k)))
                    if os.path.isfile(old_file):
                        new_file = os.path.join(cfg.path['base'], cs.mdata.data(k))
                        if not os.path.isdir(os.path.dirname(new_file)):
                            os.makedirs(os.path.dirname(new_file))
                        os.rename(old_file, new_file)
                        moved.append([old_file, new_file])
                    else:
                        laststep_successful = False
                        print('Import failed: Raw file is missing: ', old_file)
                        failedImports.append([pfile, 'Raw file is missing: ' + old_file])
                        for moved_file in moved:
                            os.rename(moved_file[1], moved_file[0])
                        break
            if laststep_successful:
                try:
                    cs.commit(update=False)
                except:
                    print('Import failed: Adding spec to db failed.')
                    failedImports.append([pfile, 'Adding spec to db failed.'])
                    for moved_file in moved:
                        os.rename(moved_file[1], moved_file[0])
                os.remove(pfile)
                successfulImports.append(pfile)
                print('Import successful.')
                        
        else:
            print('Import failed: Db has already entry with this sha1.')
            failedImports.append([pfile, 'Db has already entry with this sha1.'])
        del cs
    
    print('')
    print('Import stats:')
    print('Number of files to imports: ', len(filelist))
    print('Sucessful imports: ', len(successfulImports))    
    print('Failed imports: ', len(failedImports))
    if len(failedImports) > 0:
        for entry in failedImports:
            print(os.path.basename(entry[0]), ':  ', entry[1])
    
    
    
    
    
    
    
