import re
import time

#def parseFilename(filename):
#    
#    return parseFilenameForData(filename)

    
    
    
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