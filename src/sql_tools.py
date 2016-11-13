from datetime import datetime, timezone

def where_builder_string(column_name, likestring):
    return column_name+" LIKE '"+likestring+"'"

def where_builder_integer(column_name, restriction):
    return column_name+" "+restriction
    
    
def where_builder_float(column_name, restriction):
    return column_name+" "+restriction
    
    
    
    '''
############################################
## 
## SQL query builder, builds 
## Select * from <tablename>  <loop: WHERE <limit i>> ORDER BY <ordering>
##
############################################'''
def sql_builder(tablename , WhereRestrictions ):
    
    
    
    
    type_where_builder_map = {
        'TEXT' : where_builder_string,
        'REAL' : where_builder_float,
        'LIST' :  where_builder_string,
        'TEXT UNIQUE' :  where_builder_string
    }

    # build select part
    sql = "SELECT * "

    sql += ' FROM %s '%tablename

    # build where part
    whereItems = []
    #for v in WhereRestictions.values():
    for v in WhereRestrictions:
        #print 'processing: ', k, v
        if v[1] is not None:
            whereItems.append(type_where_builder_map[v]( WhereRestrictions[v][0], WhereRestrictions[v][1]))

    if len(whereItems) > 0:
        sql += 'WHERE '
        for i in whereItems:
            sql += i
            sql += ' AND '
        sql = sql.rstrip(' AND ')

    # build order part
#        if order_by in ['recTime', 'trapTemp']:
#            pes_order = ' ORDER BY clusterBaseUnit, clusterBaseUnitNumber, {}, datFile'.format(order_by)
#        else:
#            raise ValueError('oder_by must be "recTime" or "trapTemp"')
#        
#        orderResults = {'pes': pes_order,
#                        'ms': ' ORDER BY clusterBaseUnit, recTime, datFile',
#                        'generic': ' ORDER BY recTime, datFile'}
#        sql += orderResults[specType]

    return sql



def convertTime(time):
    
    return datetime.fromtimestamp(timestamp, timezone.utc)
    