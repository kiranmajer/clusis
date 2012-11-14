from __future__ import unicode_literals
import sqlite3
import os
#import calendar
import time
#import config


class Db(object):
    def __init__(self, dbName, cfg):
        print '__init__: Init Db instance.'
        self.__dbName = dbName
        dbFileName = '%s.db' % dbName
        self.__cfg = cfg
        self.__dbProps = cfg.db[dbName]
        self.__dbFile = os.path.join(self.__dbProps['path'], dbFileName)
        'TODO: into config?'        
#        sqlite3.register_adapter(time.struct_time, self.__timeAdapter)
#        sqlite3.register_converter(str('TIME'), self.__timeConverter)               
        self.__db = sqlite3.connect(self.__dbFile, detect_types=sqlite3.PARSE_DECLTYPES)
        print 'Db connection open'
        self.__db.row_factory = sqlite3.Row
        
    def __del__(self):
        self.__db.close()
        print '__del__: Db connection closed.'
        
    def __enter__(self):
        print '__enter__: Entering Db instance.'
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.__db.close()
        print '__exit__: Db connection closed.'        
        
    
#    def __timeAdapter(self, stime):
#        return calendar.timegm(stime)
#    
#    def __timeConverter(self, utime):
#        return time.gmtime(utime)
    
        
    def createTable(self, specType):
        
        sql = "CREATE TABLE IF NOT EXISTS " + specType + " (" + "%s, "*(len(self.__dbProps['layout'][specType])-1) + "%s)"
        tableHead = [' '.join(entry) for entry in self.__dbProps['layout'][specType]]
        sql = sql % tuple(tableHead)
        
        db_cursor = self.__db.cursor()
        db_cursor.execute(sql)
        db_cursor.close()
        del db_cursor


    def add(self, spectra, update=False):
        '''Make a list, so we can work only with lists'''
        specList = []
        if type(spectra) is list:
            specList.extend(spectra)
        else:
            specList.append(spectra)
        '''Dictionary with specType as keys, containing a list of entries'''
        valueList = {}
        for spec in specList:
            specType = spec.mdata.data('specType')
            keys = [item[0] for item in self.__dbProps['layout'][specType]]
            values = [spec.mdata.data(key) for key in keys]
            if specType in valueList.keys():
                valueList[specType].append(tuple(values))
            else:
                valueList[specType] = []
                valueList[specType].append(tuple(values))
                
        db_cursor = self.__db.cursor()
        print 'cursor created'
        for specType,values in valueList.iteritems():
            if update:
                sql = 'INSERT OR REPLACE INTO ' + specType + " VALUES (" + "?,"*(len(self.__dbProps['layout'][specType])-1) + "?)"
            else:
                sql = 'INSERT INTO ' + specType + " VALUES (" + "?,"*(len(self.__dbProps['layout'][specType])-1) + "?)"
            db_cursor.executemany(sql, tuple(values))
            
                   
        db_cursor.close()
        print 'cursor closed'
        #del db_cursor
        self.__db.commit()
        
        return valueList
        

    def tableHasSha1(self, tableName, sha1):
        sql = "SELECT EXISTS (SELECT 1 FROM %s WHERE sha1 IS ?)" % tableName
        db_cursor = self.__db.cursor()
        hasSha1 = db_cursor.execute(sql, (sha1,)).fetchone()[0]
        db_cursor.close()
        del db_cursor
        
        return hasSha1


    def query(self, specType, clusterBaseUnit=None, clusterBaseUnitNumber=None, clusterBaseUnitNumberRange=None,
              recTime=None, recTimeRange=None, inTags=None, notInTags=None, datFileName=None, waveLength=None):

        
        def prepClusterBaseUnit(clusterBaseUnit):
            if type(clusterBaseUnit) is str:
                return 'clusterBaseUnit IS "%s" AND '%clusterBaseUnit
            else:
                raise ValueError('clusterBaseUnit must be a string. Got "%s" instead'%clusterBaseUnit)
            
        def prepClusterBaseUnitNumber(clusterBaseUnitNumber):
            numbers = []
            numbersQuery = ''
            if type(clusterBaseUnitNumber) is list:
                numbers.extend(clusterBaseUnitNumber)
            else:
                numbers.append(clusterBaseUnitNumber)
            for i in numbers:
                if type(i) is int and i > 0:
                    numbersQuery+='clusterBaseUnitNumber IS "%s" AND '%i
                else:
                    raise ValueError('clusterBaseUnitNumber must be an int > 0. Got "%s" instead'%i)
            return numbersQuery
        
        def prepClusterBaseUnitNumberRange(clusterBaseUnitNumberRange):
            if type(clusterBaseUnitNumberRange) is list and len(clusterBaseUnitNumberRange) == 2 \
            and clusterBaseUnitNumberRange[0] is int and clusterBaseUnitNumberRange[1] is int:
                return 'clusterBaseUnitNumber BETWEEN %S AND %s AND '%tuple(clusterBaseUnitNumberRange)
            else:
                raise ValueError('Not a valid range.')
            
        def prepRecTime(recTime):
            times = []
            timesQuery = ''
            if type(recTime) is list:
                times.extend(recTime)
            else:
                times.append(recTime)
            for t in times:
                dayStart = time.mktime(time.strptime(t, '%d.%m.%Y'))
                dayEnd = dayStart + 86400
                timesQuery+='recTime BETWEEN %s AND %s AND '%(dayStart, dayEnd)
            
            return timesQuery
        
        def prepRecTimeRange(recTimeRange):
            '''TODO: check if t0<t1'''
            if type(recTimeRange) is list and len(recTimeRange) == 2:
                startTime = time.mktime(time.strptime(recTimeRange[0], '%d.%m.%Y'))
                endTime = time.mktime(time.strptime(recTimeRange[1], '%d.%m.%Y')) + 86400
                return 'recTime BETWEEN %s AND %s AND '%(startTime, endTime)
            else:
                raise ValueError('Not a valid time range.')
            
        def prepInTags(inTags):
            tags = []
            tagsQuery = ''
            if type(inTags) is list:
                tags.extend(inTags)
            else:
                tags.append(inTags)
            for t in tags:
                tagsQuery+='tags GLOB "*%s*" AND '%(t,)
            return tagsQuery
                
        def prepNotInTags(notInTags):
            tags = []
            tagsQuery = ''
            if type(inTags) is list:
                tags.extend(notInTags)
            else:
                tags.append(notInTags)
            for t in tags:
                tagsQuery+='tags NOT GLOB "*%s*" AND '%(t,)
            return tagsQuery
            
        def prepDatFileName(datFileName):
            dats = []
            datsQuery = ''
            if type(datFileName) is list:
                dats.extend(datFileName)
            elif type(datFileName) is str:
                dats.append(datFileName)
            else:
                raise ValueError('datFileName must be a list or a str.')
            for f in dats:
                datsQuery+='datFile GLOB "*%s*" AND '%f
            return datsQuery
        
        def prepWaveLength(waveLength):
            waves = []
            wavesQuery = ''
            'TODO: adapt for variable machine type.'
            refWaves = self.__cfg.mdataReference['casi']['waveLength'][0]
            print refWaves
            if type(waveLength) is list:
                waves.extend(waveLength)
            else:
                waves.append(waveLength)
            for i in waves:
                if type(i) is float and i in refWaves:
                    wavesQuery+='waveLength IS "%s" AND '%i
                else:
                    raise ValueError( 'waveLength must be one of: %s.'%', '.join([str(i) for i in refWaves]) )
            return wavesQuery
        
        
                
        q = {'clusterBaseUnit': [prepClusterBaseUnit, clusterBaseUnit, 'clusterBaseUnit'],
             'clusterBaseUnitNumber': [prepClusterBaseUnitNumber, clusterBaseUnitNumber, 'clusterBaseUnitNumber'],
             'clusterBaseUnitNumberRange': [prepClusterBaseUnitNumberRange, clusterBaseUnitNumberRange, 'clusterBaseUnitNumber'],
             'recTime': [prepRecTime, recTime, 'recTime'],
             'recTimeRange': [prepRecTimeRange, recTimeRange, 'recTime'],
             'inTags': [prepInTags, inTags, 'tags'],
             'notInTags': [prepNotInTags, notInTags, 'tags'],
             'datFileName': [prepDatFileName, datFileName, 'datFile'],
             'waveLength': [prepWaveLength, waveLength, 'waveLength']
             }
        #print 'we start with: ', q
            
        # build select part
        sql = "SELECT * "
        whereItems = []
        for v in q.itervalues():
            #print 'processing: ', k, v
            if v[1] is not None:
                whereItems.append(v[0](v[1]))
        if len(whereItems) == 0:
            raise ValueError('Nothing to query.')
        sql = sql.rstrip(', ')
        # build from part
        if specType in self.__dbProps['layout'].keys():
            sql+=' FROM %s '%specType
        else:
            raise ValueError('Unknown specType: %s'%specType)
        # build where part
        sql+='WHERE '
        for i in whereItems:
            sql+=i
        sql=sql.rstrip(' AND ')
        # build order part
        sql+=' ORDER BY clusterBaseUnit, clusterBaseUnitNumber'
        

        print 'Querying with: ', sql
        
        db_cursor = self.__db.cursor()
        fetch = db_cursor.execute(sql).fetchall()
        db_cursor.close()
        del db_cursor
        
        def printAnswer(fetch):
            def formatRecTime(unixtime):
                return time.strftime('%d.%m.%Y', time.localtime(unixtime))
            
            def formatDatFile(datfile):
                return os.path.basename(datfile)
            
            print 'Idx'.rjust(6),
            print 'element'.ljust(7+3),
            print 'size'.ljust(4+3),
            print 'waveLength'.ljust(10+3),
            print 'recTime'.ljust(12),
            print 'datFile'.ljust(16),
            print 'tags'
            idx=0
            for row in fetch:
                # sqlite3.Row expects a str and not a unicode as key
                print ('%s  '%idx).rjust(6),
                print row[str('clusterBaseUnit')].ljust(7+3),
                print str(row[str('clusterBaseUnitNumber')]).ljust(4+3),
                print str(row[str('waveLength')]*1e9).ljust(10+3),
                print formatRecTime(row[str('recTime')]).ljust(12),
                print formatDatFile(row[str('datFile')]).ljust(16),
                print '<|>'.join(row[str('tags')])
                idx+=1
                
        printAnswer(fetch)
        
        return fetch
        









#
#
#class Cursor(object):
#    """Simple wrapper, allows to open a cursor with the 'with'-statement."""
#
#    def __init__(self, connection):
#        self.connection = connection
#
#    def __enter__(self):
#        self.cursor = self.connection.cursor()
#        return self.cursor
#
#    def __exit__(self, value, traceback):
#        self.cursor.close()
#        
#
#class DatabaseConnector(object):
#    """    """
#
#    def __enter__(self, db_path='/home/kiran/python/ClusterBib_old/rawdata',
#                  db_filename='spectra.db'):
#        self.db_file = os.path.join(db_path, db_filename)
#        if not os.path.exists(self.db_file):
#            self.create_pes_table()
#            self.create_ms_table()
#        self.connection = sqlite3.connect(self.db_file)
#        self.connection.row_factory = sqlite3.Row
#        return self
#
#    def __exit__(self, type, value, traceback):
#        self.connection.close()
#        
#    def create_table(self, tablename):
#        sql_query = 'CREATE TABLE IF NOT EXISTS' + tablename
#        sql = sql_query + ", ".join([" ".join([key, value[0]]) for key, value in db_map.iteritems()]) + ')'
#        
#
#    def create_pes_table(self):
#        sql = """CREATE TABLE IF NOT EXISTS pes (
#        clusterBaseUnit TEXT,
#        clusterBaseUnitNumber INTEGER,
#        clusterDopant TEXT,
#        clusterDopantNumber TEXT,
#        pickleFile TEXT UNIQUE,
#        datFile TEXT,
#        tags TEXT,
#        waveLength REAL,
#        recordingTime TEXT UNIQUE
#        )"""
#        connection = sqlite3.connect(self.db_file)
#        with Cursor(connection) as cursor:
#            cursor.execute(sql)
#        connection.close()
#
#
#    def create_ms_table(self):
#        sql = """CREATE TABLE IF NOT EXISTS ms (
#        clusterBaseUnit TEXT,
#        clusterBaseUnitNumberStart INTEGER,
#        clusterBaseUnitNumberEnd INTEGER,
#        clusterDopant TEXT,
#        clusterDopantNumber TEXT,
#        pickleFile TEXT UNIQUE,
#        datFile TEXT,
#        tags TEXT,
#        recordingTime TEXT UNIQUE
#        )"""
#        connection = sqlite3.connect(self.db_file)
#        with Cursor(connection) as cursor:
#            cursor.execute(sql)
#        connection.close()
#
#
#    def prep_sql_query(self, spectrum_sets):
#        def keepit(item):
#            return item
#        sql_key_dict={
#                      'clusterBaseUnit': keepit,
#                      'clusterBaseUnitNumber': keepit,
#                      'clusterDopant': keepit,
#                      'clusterDopantNumber': keepit,
#                      'pickleFile': keepit,
#                      'datFile': keepit,
#                      'tags':str,
#                      'waveLength': keepit,
#                      'recordingTime':calendar.timegm
#                      }
#        return {key: value(spectrum_sets.data[key]) for key,value in 
#                sql_key_dict.iteritems()}
#        
#
#    def prep_sql_query_ms(self, spectrum_sets):
#        def keepit(item):
#            return item
#        sql_key_dict={
#                      'clusterBaseUnit': keepit,
#                      'clusterBaseUnitNumberStart': keepit,
#                      'clusterBaseUnitNumberEnd': keepit,
#                      'clusterDopant': keepit,
#                      'clusterDopantNumber': keepit,
#                      'pickleFile': keepit,
#                      'datFile': keepit,
#                      'tags':str,
#                      'recordingTime':calendar.timegm
#                      }
#        return {key: value(spectrum_sets.data[key]) for key,value in 
#                sql_key_dict.iteritems()}
#
#
#
#    def insert_spectra(self, spectrum_sets):
#        sql = """INSERT OR IGNORE INTO pes (
#        clusterBaseUnit,
#        clusterBaseUnitNumber,
#        clusterDopant,
#        clusterDopantNumber,
#        pickleFile,
#        datFile,
#        tags,
#        waveLength,
#        recordingTime
#        ) VALUES (
#        :clusterBaseUnit,
#        :clusterBaseUnitNumber,
#        :clusterDopant,
#        :clusterDopantNumber,
#        :pickleFile,
#        :datFile,
#        :tags,
#        :waveLength,
#        :recordingTime        
#        )"""
#        sql_query = [self.prep_sql_query(set) for set in spectrum_sets]
#        with Cursor(self.connection) as cursor:
#            cursor.executemany(sql, sql_query)
#        self.connection.commit()
#        
#    
#    def insert_ms(self, spectrum_sets):
#        sql = """INSERT OR IGNORE INTO ms (
#        clusterBaseUnit,
#        clusterBaseUnitNumberStart,
#        clusterBaseUnitNumberEnd,
#        clusterDopant,
#        clusterDopantNumber,
#        pickleFile,
#        datFile,
#        tags,
#        recordingTime
#        ) VALUES (
#        :clusterBaseUnit,
#        :clusterBaseUnitNumberStart,
#        :clusterBaseUnitNumberEnd,
#        :clusterDopant,
#        :clusterDopantNumber,
#        :pickleFile,
#        :datFile,
#        :tags,
#        :recordingTime        
#        )"""
#        sql_query = [self.prep_sql_query_ms(set) for set in spectrum_sets]
#        with Cursor(self.connection) as cursor:
#            cursor.executemany(sql, sql_query)
#        self.connection.commit()    
#    
#        
#    def get_picklefile_from_datfile(self,datFileName, specType='pes'):
#        sql = "SELECT pickleFile from " + specType + " WHERE datFile LIKE ?"
#        with Cursor(self.connection) as cursor:
#            return cursor.execute(sql, ('%'+datFileName+'%', )).fetchall()
#        
#    def sql_query(self, query):
#        with Cursor(self.connection) as cursor:
#            return cursor.execute(query).fetchall()
#        
#        
#        
#if __name__ == "__main__":
#    connection = sqlite3.connect('../rawdata/spectra.db')
#    cursor = connection.cursor()
#    cursor.execute("""CREATE TABLE pes (clusterBaseUnit TEXT, clusterBaseUnitNumber INTEGER, pickleFile TEXT, pickleFileDir TEXT)""")
#    sql = "INSERT INTO pes VALUES (:clusterBaseUnit, :clusterBaseUnitNumber, :pickleFile, :pickleFileDir)"
#    cursor.execute(sql, na38.data)
#    cursor.execute(sql, k38.data)
#    connection.commit()
#    cursor.execute("""SELECT pickleFile, pickleFileDir from pes WHERE clusterBaseUnit='Na' AND clusterBaseUnitNumber = '38'""")
#    cursor.fetchall()
