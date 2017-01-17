'''
Provides generic helper methods for sql related stuff.
'''
import sqlite3

###############################################################################
# Adapters to handle python type <=> sql type conversion
#
def list_adapter(l):
    list_to_text = '<||>'.join(l)
    list_to_text = '|>' + list_to_text + '<|'
    return list_to_text

def list_converter(s):
    '''Not sure why we get byte out while put str in.'''
    text_to_list = s.decode('utf-8')
    text_to_list = text_to_list.lstrip('|>').rstrip('<|').split('<||>')
    return text_to_list

# setup adapters
def setup_sqlite3():
    sqlite3.register_adapter(list, list_adapter)
    sqlite3.register_converter('LIST', list_converter)

# maps python types to sql types
type_map = {str: 'TEXT',
            int: 'INTEGER',
            float: 'REAL',
            list: 'LIST'}


###############################################################################
# Methods to generate/handle db layouts by mdata definitions
#
def generate_table_layout(definition_dict, type_map):
    '''
    Generates a tupel of the form ('column_name SQL_DATA_TYPE', ...)
    which is used by the Db class to create a table.
    '''  
    layout = []
    for k,v in definition_dict.items():
        if isinstance(v['db_included'], str):
            layout.append('{} {}'.format(k, v['db_included']))
        elif v['db_included']:
            layout.append('{} {}'.format(k, type_map[v['mdata_type']]))
    
    return layout