import re
import time
import os.path
from prettytable import from_db_cursor


# TODO: move formatting stuff to config or make it more generic
def print_answer(db_query_fetch, spec_type):
    def format_RecTime(unixtime):
        return time.strftime('%d.%m.%Y  %H:%M', time.localtime(unixtime))
    
    def format_DatFile(datfile):
        return os.path.basename(datfile)
    
    def print_head_pes():
        print('Idx'.rjust(6),
              'id'.ljust(16+3),
              'element'.ljust(7+3),
              'size'.ljust(4+3),
              'waveLength'.ljust(10+3),
              'temp'.ljust(4+3),
              'recTime'.ljust(19),
              'datFile'.ljust(16),
              'tags')
        
    def print_data_pes(row):
        print(('%s  '%idx).rjust(6),
              row['shortId'].ljust(16+3),
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
              'id'.ljust(16+3),
              'element'.ljust(7+3),
              'recTime'.ljust(19),
              'datFile'.ljust(28+3),
              'tags')
        
    def print_data_ms(row):
        print(('%s  '%idx).rjust(6),
              row['shortId'].ljust(16+3),
              row['clusterBaseUnit'].ljust(7+3),    
              format_RecTime(row['recTime']).ljust(19),
              format_DatFile(row['datFile']).ljust(28+3),
              end=" "
              )            
        
    def print_head_generic():
        print('Idx'.rjust(6),
              'id'.ljust(16+3),
              'recTime'.ljust(19),
              'datFile'.ljust(16),
              'tags')               
     
    def print_data_generic(row):
        print(('%s  '%idx).rjust(6), 
              row['shortId'].ljust(16+3),  
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
    
    
    printHead[spec_type]()
    
    idx=0
    for row in db_query_fetch:
        # sqlite3.Row expects a str and not a unicode as key
        printData[spec_type](row)
        if row['tags'] is None:
            print('')
        else:
            #print("row['tags']: ", row['tags'])
            tag_list = list(row['tags'])
            tag_list.sort()
            print('<|>'.join(tag_list))
        idx += 1
                

def print_answer_simple(db_query_fetch, fields=['shortId', 'clusterBaseUnit', 'clusterBaseUnitNumber',
                                                'waveLength', 'trapTemp', 'recTime','tags']):
    pt = from_db_cursor(db_query_fetch)
    print(pt.get_string(fields=fields))
    
    
    
def parseFilenameForDate(filename):
    '''
    ###############################################
    #
    # If a String starts with a date of YYYYmmdd
    # return year month day
    #
    ###############################################
    '''
    potential_date_str = filename[0:10]
    
    dividers = {'_','-','.'}
    
    divided_date_regs = []
    
    # American Dates
    for d in dividers:
        divided_date_regs.append('^(19|20)\d{2}['+d+']{1}(0[1-9]|1[012])['+d+']{1}(0[1-9]|[12][0-9]|3[01])')
    
    date_reg = '^(19|20)\d{2}(0[1-9]|1[012])(0[1-9]|[12][0-9]|3[01])'
    
    ret=False
    
    for reg in divided_date_regs:
        match = re.match(reg, potential_date_str)
#        print(match)
        if match is not None:
#            print("This string starts with a date")
            year = potential_date_str[0:4]
            month = potential_date_str[5:7]
            day = potential_date_str[8:10]
            ret=True
            
            
    match = re.match(date_reg, potential_date_str)
#    print(match)
    if match is not None:
#        print("This string starts with a date")
        year = potential_date_str[0:4]
        month = potential_date_str[4:6]
        day = potential_date_str[6:8]
        ret=True
        
    return [year,month,day] if ret else False ;
        
def checkStringForDate(filename):
    return parseFilenameForDate(filename)

def convertToUnixTime(string):
    if parseFilenameForDate(string) is not False:
            year,month,day = parseFilenameForDate(string)
    else:
        raise ValueError("Couldn't add to database: "+string+"is not a valid recTime")        
    startDate = '%s %s %s' % (day, month, year)
    return time.mktime(time.strptime(startDate, '%d %m %Y'))