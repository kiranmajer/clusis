import sqlite3
import os
#import calendar
import time
#import config


class Db(object):
    def __init__(self, dbName, cfg):
        #print('__init__: Init Db instance.')
        #self.__dbName = dbName
        self.__cfg = cfg
        self.__dbProps = cfg.db[dbName]
        dbFileName = '{}_v{}.db'.format(dbName, self.__dbProps['version'])
        #dbFileName = '{}.db'.format(dbName)
        self.__dbFile = os.path.join(self.__dbProps['path'], dbFileName)
        'TODO: into config?'        
#        sqlite3.register_adapter(time.struct_time, self.__timeAdapter)
#        sqlite3.register_converter(str('TIME'), self.__timeConverter)               
        self.__db = sqlite3.connect(self.__dbFile, detect_types=sqlite3.PARSE_DECLTYPES)
        #print('Db connection open')
        self.__db.row_factory = sqlite3.Row
        
    def __del__(self):
        self.__db.close()
        #print('__del__: Db connection closed.')
        
    def __enter__(self):
        #print('__enter__: Entering Db instance of {}.'.format(self.__dbFile))
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.__db.close()
        #print('__exit__: Db connection closed.')        
        
    
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
            values = []
            for key in keys:
                if key is 'shortId':
                    values.append(spec.short_id)
                elif key not in spec.mdata.data().keys():
                    spec.mdata.add({key: None})
                    values.append(None)
                elif key in spec.mdata.data().keys():
                    values.append(spec.mdata.data(key))
                else:
                    raise ValueError('key "{}" not in mdata.'.format(key))
            if specType in list(valueList.keys()):
                valueList[specType].append(tuple(values))
            else:
                valueList[specType] = []
                valueList[specType].append(tuple(values))
                
        db_cursor = self.__db.cursor()
        #print('cursor created')
        for specType,values in valueList.items():
            if update:
                sql = 'INSERT OR REPLACE INTO ' + specType + " VALUES (" + "?,"*(len(self.__dbProps['layout'][specType])-1) + "?)"
                #print('Adding with sql string:\n', sql, values)
            else:
                sql = 'INSERT INTO ' + specType + " VALUES (" + "?,"*(len(self.__dbProps['layout'][specType])-1) + "?)"
            db_cursor.executemany(sql, tuple(values))
            
                   
        db_cursor.close()
        #print('cursor closed')
        #del db_cursor
        self.__db.commit()
        
        return valueList
    
    
    def remove(self, sha1, tablename):
        sql = 'DELETE FROM {} WHERE sha1 IS "{}"'.format(tablename, sha1)
        db_cursor = self.__db.cursor()
        db_cursor.execute(sql)
        db_cursor.close()
        self.__db.commit()
        del db_cursor
                

    def table_has_sha1(self, tableName, sha1):
        sql = "SELECT EXISTS (SELECT 1 FROM %s WHERE sha1 IS ?)" % tableName
        db_cursor = self.__db.cursor()
        hasSha1 = db_cursor.execute(sql, (sha1,)).fetchone()[0]
        db_cursor.close()
        del db_cursor
        
        return hasSha1
    
    

        

    def query(self, specType, clusterBaseUnit=None, clusterBaseUnitNumber=None, clusterBaseUnitNumberRange=None,
              recTime=None, recTimeRange=None, inTags=None, notInTags=None, datFileName=None, waveLength=None,
              trapTemp=None, trapTempRange=None, hide_trash=True, order_by='recTime'):
        

        
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
            if len(number_list) > 1:
                numbersQuery = '('
                for n in number_list[:-1]:
                    numbersQuery += '{} IS {} OR '.format(key, n)
                numbersQuery += '{} IS {}) AND '.format(key, number_list[-1])
            else:
                numbersQuery = '{} IS {} AND '.format(key, number_list[0])  
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
            if n_times > 1:
                timesQuery += '('
            for t in times:
                dayStart = time.mktime(time.strptime(t, '%d.%m.%Y'))
                dayEnd = dayStart + 86400
                timesQuery+='recTime BETWEEN %s AND %s '%(dayStart, dayEnd)
                processed_times += 1
                if processed_times < n_times:
                    timesQuery += 'OR '
            if n_times > 1:
                timesQuery += ') AND '
            else:
                timesQuery += 'AND '
            
            return timesQuery
        
        def sqlformat_RecTimeRange(recTimeRange, key):
            'TODO: check if t0<t1'
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
                # tuples are treated as non-truncated tag queries
                if isinstance(t, tuple):
                    tagsQuery+='tags GLOB "*|>{}<|*" AND '.format(t[0])
                else:
                    tagsQuery+='tags GLOB "*{}*" AND '.format(t)
            return tagsQuery
                
        def sqlformat_NotInTags(notInTags, key):
            tags = []
            tagsQuery = ''
            if type(notInTags) is list:
                tags.extend(notInTags)
            else:
                tags.append(notInTags)
            for t in tags:
                # tuples are treated as non-truncated tag queries
                if isinstance(t, tuple):
                    tagsQuery+='tags NOT GLOB "*|>{}<|*" AND '.format(t[0])
                else:
                    tagsQuery+='tags NOT GLOB "*{}*" AND '.format(t)
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
            #print(refWaves)
            if type(waveLength) is list:
                waves.extend(waveLength)
            else:
                waves.append(waveLength)
            for w in waves:
                if w not in refWaves:
                    raise ValueError( 'waveLength must be one of: %s.'%', '.join([str(i) for i in refWaves]) )
            if len(waves) > 1:
                wavesQuery = '('
                for i in waves[:-1]:
                    wavesQuery+='waveLength IS "{}" OR '.format(i)
                wavesQuery += 'waveLength IS "{}") AND '.format(waves[-1])
            else:
                wavesQuery = 'waveLength IS "{}" AND '.format(waves[0])
            return wavesQuery
        
        if hide_trash:
            if type(notInTags) is list:
                notInTags.append('trash')
            elif type(notInTags) is str:
                notInTags =[notInTags, 'trash']
            else:
                notInTags = ['trash']
                
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
        
        # TODO: move to config
        # build order part
        if order_by in ['recTime', 'trapTemp']:
            pes_order = ' ORDER BY clusterBaseUnit, clusterBaseUnitNumber, {}, datFile'.format(order_by)
        else:
            raise ValueError('oder_by must be "recTime" or "trapTemp"')
        
        orderResults = {'pes': pes_order,
                        'ms': ' ORDER BY clusterBaseUnit, recTime, datFile',
                        'tof': ' ORDER BY clusterBaseUnit, recTime, datFile',
                        'generic': ' ORDER BY recTime, datFile'}
        sql += orderResults[specType]
        

        print('Querying with: ', sql)
        
        db_cursor = self.__db.cursor()
        fetch = db_cursor.execute(sql).fetchall()
        db_cursor.close()
        del db_cursor
        
        # TODO: move fromating stuff to config or make it more generic
        def print_answer(fetch):
            def format_RecTime(unixtime):
                return time.strftime('%d.%m.%Y  %H:%M', time.localtime(unixtime))
            
            def format_DatFile(datfile):
                return os.path.basename(datfile)
            
            def print_head_pes():
                print('Idx'.rjust(6),
                      'element'.ljust(7+3),
                      'size'.ljust(4+3),
                      'waveLength'.ljust(10+3),
                      'temp'.ljust(4+3),
                      'recTime'.ljust(19),
                      'datFile'.ljust(16),
                      'tags')
                
            def print_data_pes(row):
                print(('%s  '%idx).rjust(6),
                      row['clusterBaseUnit'].ljust(7+3),
                      str(row['clusterBaseUnitNumber']).ljust(4+3),
                      str(round(row['waveLength']*1e9, 1)).ljust(10+3),
                      str(row['trapTemp']).ljust(4+3),
                      format_RecTime(row['recTime']).ljust(19),
                      format_DatFile(row['datFile']).ljust(16),
                      end=" "
                      )                
                
            def print_head_ms():
                print('Idx'.rjust(6),
                      'element'.ljust(7+3),
                      'recTime'.ljust(19),
                      'datFile'.ljust(28+3),
                      'tags')
                
            def print_data_ms(row):
                print(('%s  '%idx).rjust(6),
                      row['clusterBaseUnit'].ljust(7+3),    
                      format_RecTime(row['recTime']).ljust(19),
                      format_DatFile(row['datFile']).ljust(28+3),
                      end=" "
                      )            
                
            def print_head_generic():
                print('Idx'.rjust(6),
                      'recTime'.ljust(19),
                      'datFile'.ljust(16),
                      'tags')               
             
            def print_data_generic(row):
                print(('%s  '%idx).rjust(6),   
                      format_RecTime(row['recTime']).ljust(19),
                      format_DatFile(row['datFile']).ljust(16),
                      end=" "
                      )                
            
            printHead = {'pes': print_head_pes,
                         'ms': print_head_ms,
                         'tof': print_head_ms,
                         'generic': print_head_generic}
                           
            printData = {'pes': print_data_pes,
                         'ms': print_data_ms,
                         'tof': print_data_ms,
                         'generic': print_data_generic}
            
            
            printHead[specType]()
            
            idx=0
            for row in fetch:
                # sqlite3.Row expects a str and not a unicode as key
                printData[specType](row)
                if row['tags'] is None:
                    print('')
                else:
                    #print("row['tags']: ", row['tags'])
                    tag_list = list(row['tags'])
                    tag_list.sort()
                    print('<|>'.join(tag_list))
                idx += 1
                
        print_answer(fetch)
        
        return fetch
        

