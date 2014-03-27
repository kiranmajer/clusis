import sqlite3
import os
#import calendar
import time
#import config


class Db(object):
    def __init__(self, dbName, cfg):
        print('__init__: Init Db instance.')
        self.__dbName = dbName
        dbFileName = '%s.db' % dbName
        self.__cfg = cfg
        self.__dbProps = cfg.db[dbName]
        self.__dbFile = os.path.join(self.__dbProps['path'], dbFileName)
        'TODO: into config?'        
#        sqlite3.register_adapter(time.struct_time, self.__timeAdapter)
#        sqlite3.register_converter(str('TIME'), self.__timeConverter)               
        self.__db = sqlite3.connect(self.__dbFile, detect_types=sqlite3.PARSE_DECLTYPES)
        print('Db connection open')
        self.__db.row_factory = sqlite3.Row
        
    def __del__(self):
        self.__db.close()
        print('__del__: Db connection closed.')
        
    def __enter__(self):
        print('__enter__: Entering Db instance.')
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.__db.close()
        print('__exit__: Db connection closed.')        
        
    
#    def __timeAdapter(self, stime):
#        return calendar.timegm(stime)
#    
#    def __timeConverter(self, utime):
#        return time.gmtime(utime)
    
        
    def create_table(self, specType):
        
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
            for key in keys:
                if key not in spec.mdata.data().keys():
                    spec.mdata.add({key: None})
            values = [spec.mdata.data(key) for key in keys]
            if specType in list(valueList.keys()):
                valueList[specType].append(tuple(values))
            else:
                valueList[specType] = []
                valueList[specType].append(tuple(values))
                
        db_cursor = self.__db.cursor()
        print('cursor created')
        for specType,values in valueList.items():
            if update:
                sql = 'INSERT OR REPLACE INTO ' + specType + " VALUES (" + "?,"*(len(self.__dbProps['layout'][specType])-1) + "?)"
            else:
                sql = 'INSERT INTO ' + specType + " VALUES (" + "?,"*(len(self.__dbProps['layout'][specType])-1) + "?)"
            db_cursor.executemany(sql, tuple(values))
            
                   
        db_cursor.close()
        print('cursor closed')
        #del db_cursor
        self.__db.commit()
        
        return valueList
        

    def table_has_sha1(self, tableName, sha1):
        sql = "SELECT EXISTS (SELECT 1 FROM %s WHERE sha1 IS ?)" % tableName
        db_cursor = self.__db.cursor()
        hasSha1 = db_cursor.execute(sql, (sha1,)).fetchone()[0]
        db_cursor.close()
        del db_cursor
        
        return hasSha1
    
    
    def rebuild_db(self, spectra):
        '''
        Basically already implemented over add. Integrate scan pickle dir, build spec list, add.
        clear tables?
        check for missing entries? -> consistency check: each table entry has corresponding pickleFile'''
        pass
        

    def query(self, specType, clusterBaseUnit=None, clusterBaseUnitNumber=None, clusterBaseUnitNumberRange=None,
              recTime=None, recTimeRange=None, inTags=None, notInTags=None, datFileName=None, waveLength=None,
              trapTemp=None, trapTempRange=None):

        
        def sqlformat_ClusterBaseUnit(clusterBaseUnit, key):
            if type(clusterBaseUnit) is str:
                return 'clusterBaseUnit IS "%s" AND '%clusterBaseUnit
            else:
                raise ValueError('clusterBaseUnit must be a string. Got "%s" instead'%clusterBaseUnit)
            
        def sqlformat_number(numbers, key):
            number_list = []
            numbersQuery = ''
            if type(numbers) is list:
                number_list.extend(numbers)
            else:
                number_list.append(numbers)
            for i in number_list:
                numbersQuery+='{} IS {} AND '.format(key, i)
            return numbersQuery
        
        def sqlformat_number_range(number_range, key):
            if type(number_range) is list and len(number_range) == 2 and number_range[0] <= number_range[1]:
                return '{} BETWEEN {} AND {} AND '.format(key, number_range[0], number_range[1])
            else:
                raise ValueError('Not a valid range.')
            
        def sqlformat_RecTime(recTime, key):
            times = []
            timesQuery = ''
            if type(recTime) is list:
                times.extend(recTime)
            else:
                times.append(recTime)
            n_times = len(times)
            processed_times = 0
            for t in times:
                dayStart = time.mktime(time.strptime(t, '%d.%m.%Y'))
                dayEnd = dayStart + 86400
                timesQuery+='recTime BETWEEN %s AND %s '%(dayStart, dayEnd)
                processed_times += 1
                if processed_times < n_times:
                    timesQuery += 'OR '
                
            timesQuery += 'AND '
            
            return timesQuery
        
        def sqlformat_RecTimeRange(recTimeRange, key):
            '''TODO: check if t0<t1'''
            if type(recTimeRange) is list and len(recTimeRange) == 2:
                startTime = time.mktime(time.strptime(recTimeRange[0], '%d.%m.%Y'))
                endTime = time.mktime(time.strptime(recTimeRange[1], '%d.%m.%Y')) + 86400
                return 'recTime BETWEEN %s AND %s AND '%(startTime, endTime)
            else:
                raise ValueError('Not a valid time range.')
            
        def sqlformat_InTags(inTags, key):
            tags = []
            tagsQuery = ''
            if type(inTags) is list:
                tags.extend(inTags)
            else:
                tags.append(inTags)
            for t in tags:
                tagsQuery+='tags GLOB "*%s*" AND '%(t,)
            return tagsQuery
                
        def sqlformat_NotInTags(notInTags, key):
            tags = []
            tagsQuery = ''
            if type(notInTags) is list:
                tags.extend(notInTags)
            else:
                tags.append(notInTags)
            for t in tags:
                tagsQuery+='tags NOT GLOB "*%s*" AND '%(t,)
            return tagsQuery
            
        def sqlformat_DatFileName(datFileName, key):
            dats = []
            datsQuery = ''
            if type(datFileName) is list:
                dats.extend(datFileName)
            elif type(datFileName) is str:
                dats.append(datFileName)
            else:
                raise ValueError('datFileName must be a list or a str.')
            if len(dats) > 1:
                datsQuery = '('
                for f in dats[:-1]:
                    datsQuery+='datFile GLOB "*%s*" OR '%f
                datsQuery += 'datFile GLOB "*{}*") AND '.format(dats[-1])
            else:
                datsQuery = 'datFile GLOB "*{}*" AND '.format(dats[0])
            return datsQuery
        
        def sqlformat_WaveLength(waveLength, key):
            waves = []
            wavesQuery = ''
            'TODO: adapt for variable machine type.'
            refWaves = self.__cfg.wavelengths
            print(refWaves)
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
        
        
                
        q = {'clusterBaseUnit': [sqlformat_ClusterBaseUnit, clusterBaseUnit, 'clusterBaseUnit'],
             'clusterBaseUnitNumber': [sqlformat_number, clusterBaseUnitNumber, 'clusterBaseUnitNumber'],
             'clusterBaseUnitNumberRange': [sqlformat_number_range, clusterBaseUnitNumberRange, 'clusterBaseUnitNumber'],
             'recTime': [sqlformat_RecTime, recTime, 'recTime'],
             'recTimeRange': [sqlformat_RecTimeRange, recTimeRange, 'recTime'],
             'inTags': [sqlformat_InTags, inTags, 'tags'],
             'notInTags': [sqlformat_NotInTags, notInTags, 'tags'],
             'datFileName': [sqlformat_DatFileName, datFileName, 'datFile'],
             'waveLength': [sqlformat_WaveLength, waveLength, 'waveLength'],
             'trapTemp': [sqlformat_number, trapTemp, 'trapTemp'],
             'trapTempRange': [sqlformat_number_range, trapTempRange, 'trapTemp']
             }
        #print 'we start with: ', q
            
        # build select part
        sql = "SELECT * "
        #if len(whereItems) == 0:
        #    raise ValueError('Nothing to query.')
        #sql = sql.rstrip(', ')
        
        # build from part
        if specType in list(self.__dbProps['layout'].keys()):
            sql += ' FROM %s '%specType
        else:
            raise ValueError('Unknown specType: %s'%specType)
        
        # build where part
        whereItems = []
        for v in q.values():
            #print 'processing: ', k, v
            if v[1] is not None:
                whereItems.append(v[0](v[1], v[2]))
        if len(whereItems) > 0:
            sql += 'WHERE '
            for i in whereItems:
                sql += i
            sql = sql.rstrip(' AND ')
        
        # build order part
        orderResults = {'pes': ' ORDER BY clusterBaseUnit, clusterBaseUnitNumber, recTime, datFile',
                        'ms': ' ORDER BY clusterBaseUnit, recTime, datFile',
                        'generic': ' ORDER BY recTime, datFile'}
        sql += orderResults[specType]
        

        print('Querying with: ', sql)
        
        db_cursor = self.__db.cursor()
        fetch = db_cursor.execute(sql).fetchall()
        db_cursor.close()
        del db_cursor
        
        def print_answer(fetch):
            def format_RecTime(unixtime):
                return time.strftime('%d.%m.%Y', time.localtime(unixtime))
            
            def format_DatFile(datfile):
                return os.path.basename(datfile)
            
            def print_head_pes():
                print('Idx'.rjust(6),
                      'element'.ljust(7+3),
                      'size'.ljust(4+3),
                      'waveLength'.ljust(10+3),
                      'temp'.ljust(4+3),
                      'recTime'.ljust(12),
                      'datFile'.ljust(16),
                      'tags')
                
            def print_data_pes(row):
                print(('%s  '%idx).rjust(6),
                      row['clusterBaseUnit'].ljust(7+3),
                      str(row['clusterBaseUnitNumber']).ljust(4+3),
                      str(round(row['waveLength']*1e9, 1)).ljust(10+3),
                      str(row['trapTemp']).ljust(4+3),
                      format_RecTime(row['recTime']).ljust(12),
                      format_DatFile(row['datFile']).ljust(16),
                      end=" "
                      )                
                
            def print_head_ms():
                print('Idx'.rjust(6),
                      'recTime'.ljust(12),
                      'datFile'.ljust(16),
                      'tags')
                
            def print_data_ms(row):
                print(('%s  '%idx).rjust(6),
                      row['clusterBaseUnit'].ljust(7+3),    
                      format_RecTime(row['recTime']).ljust(12),
                      format_DatFile(row['datFile']).ljust(16),
                      end=" "
                      )            
                
            def print_head_generic():
                print('Idx'.rjust(6),
                      'recTime'.ljust(12),
                      'datFile'.ljust(16),
                      'tags')               
             
            def print_data_generic(row):
                print(('%s  '%idx).rjust(6),   
                      format_RecTime(row['recTime']).ljust(12),
                      format_DatFile(row['datFile']).ljust(16),
                      end=" "
                      )                
            
            printHead = {'pes': print_head_pes,
                         'ms': print_head_ms,
                         'generic': print_head_generic}
                           
            printData = {'pes': print_data_pes,
                         'ms': print_data_ms,
                         'generic': print_data_generic}
            
            
            printHead[specType]()
            
            idx=0
            for row in fetch:
                # sqlite3.Row expects a str and not a unicode as key
                printData[specType](row)
                if row['tags'] is None:
                    print('')
                else:
                    print('<|>'.join(row['tags']))
                idx += 1
                
        print_answer(fetch)
        
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
