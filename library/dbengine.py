from library import mrecords as records
import re
from babel.numbers import parse_decimal, NumberFormatError

schema_re = re.compile(r'\((.+)\)')
num_re = re.compile(r'[-+]?\d*\.\d+|\d+')

agg_ops = ['', 'MAX', 'MIN', 'COUNT', 'SUM', 'AVG']
cond_ops = ['=', '>', '<', 'OP']


class DBEngine:

    def __init__(self, fdb):
        # sqlite:///D:\COMPUTER_DEPARTMENT\\3RD_YEAR\Tesi\Seq2sql\Seq2SQL--Natural-Language-sentences-to-SQL-Queries-master\data\\test.db
        self.db = records.Database('sqlite:///'+fdb)
        self.conn = self.db.get_connection()

    def execute_query(self, table_id, query, *args, **kwargs):
        return self.execute(table_id, query.sel_index, query.agg_index, query.conditions, *args, **kwargs)

    def execute(self, table_id, select_index, aggregation_index, conditions, lower=True):
        if not table_id.startswith('table'):
            table_id = 'table_{}'.format(table_id.replace('-', '_'))
        # print(table_id)
        # print(self.db.get_table_names())
        q = 'SELECT sql from sqlite_master WHERE name = ' +"'"+str(table_id)+ "'"
        # q = 'SELECT col0 FROM ' + str(table_id) + ' WHERE col1 = 25'
        # q = 'PRAGMA table_info({})'.format(table_id) 
        table_info = self.conn.query(q).all(as_dict=True)[
            0]
        # print(table_info)
        table_info = table_info['sql'].replace('\n', '')
        schema_str = schema_re.findall(table_info)[0]
        schema = {}
        for tup in schema_str.split(', '):
            c, t = tup.split()
            schema[c] = t
        select = 'col{}'.format(select_index)
        agg = agg_ops[aggregation_index]
        if agg:
            select = '{}({})'.format(agg, select)
        where_clause = []
        where_map = {}
        for col_index, op, val in conditions:
            if lower and (isinstance(val, str) or isinstance(val, bytes)):
                val = val.lower()
            if schema['col{}'.format(col_index)] == 'real' and not isinstance(val, (int, float)):
                try:
                    # print (val)
                    val = float(parse_decimal(val, locale='en_US'))
                except NumberFormatError as e:
                    val = float(num_re.findall(val)[0])
            where_clause.append('col{} {} :col{}'.format(col_index, cond_ops[op], col_index))
            where_map["col"+str(col_index)] = val
        where_str = ''
        if where_clause:
            where_str = 'WHERE ' + ' AND '.join(where_clause)
        query = 'SELECT {} AS result FROM {} {}'.format(select, table_id, where_str)
        # print(where_map)
        # query = 'SELECT '+ str(select) + ' AS result FROM '+ str(table_id) +' '+ str(where_str) +' '+ str(list(where_map.values())[0])
        out = self.conn.query(query,fetchall=True,**where_map)
        # print('-------------------------')
        # print(out)
        # print('-------------------------')
        # out = out.fetchall()
        return [o.result for o in out]
