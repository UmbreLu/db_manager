'''
Simplified sqlite3 library command calls on Python3 by Lucas.
'''



import sqlite3


class Main():

    def __init__(self, database_file):
        self.database = database_file  # set which sqlite database file ops are gonna be executed on
        self.queue = []  # a queue to gather database ops to be executed later at once together
        self.fetchable = 0  # counter to trace which operations have a fetching result (for the Table._call_ method)
        self.result = None
        self.queries_count = 0
        self.op_error = None
        self.error_log = None
        self.results = None
        self.master = self.get_master_table()
        self.table_list = []
        for table in self.get_my_tables():
            try:
                exec('self.{} = table'.format(table.name))
                self.table_list.append("{}".format(table.name))
            except:
                exec('self.{}_ = table'.format(table.name))
                self.table_list.append("{}_".format(table.name))
        
    def __str__(self):
        strg = 'Database overview'
        for table_name in self.table_list:
            strg += '\n{}: '.format(table_name) + ', '.join(eval('self.{}.columns'.format(table_name))) +'.'
        return strg

    
    def get_master_table(self):
        """
        Instatiate the standart sqlite master table for the Main object.
        """
        return Table('sqlite_master', 'name', self, {'type', 'name', 'tbl_name', 'rootpage', 'sql'})

    def get_my_tables(self):
        """
        This method uses the master table to identify all tables and its configurations on the sqlite3 database file.
        """
        qnum = self.master('sql', att={'type': 'table'})  # it's a Table._call_() function call
        if self.run():
            return (self.table_factory(self.get_table_info(result[0])) for result in self.results[qnum])
        else:
            print('An error has occurred when initializing the database.')

    def table_factory(self, table_info: dict):
        return Table(table_info['table_name'], table_info['priority'], self, table_info['columns'])

    @staticmethod
    def get_table_info(create_table_sql: str):
        """
        This static method identifies a table's columns and its priority column given its creation sql statement.
        """
        table_info = {'columns': [], 'priority': 'rowid'}
        bits = create_table_sql.split()
        lowbits = create_table_sql.lower().split()
        rowid = True
        for n, word in enumerate(lowbits):
            if word == 'table':
                table_info['table_name'] = bits[n + 1]
            if word.startswith('('):
                table_info['columns'].append(bits[n].lstrip('('))
            if word.endswith(','):
                table_info['columns'].append(bits[n + 1])
            if word == 'unique':
                table_info['priority'] = table_info['columns'][-1]
            if word == 'without' and lowbits[n] == 'rowid':
                rowid = False
        if rowid:
            table_info['columns'].insert(0, 'rowid')
        return table_info

    def run(self):
        if not self.queue:
            raise Exception('The queue is empty!')
        #for item in self.queue:
            #print(item)
        self.queries_count =+ 1
        self.executemany_aggregate()
        #for item in self.queue:
            #print(item)
        connection = sqlite3.connect(self.database)
        cursor = connection.cursor()
        commit = False
        fetch = []
        while self.queue:
            operation = self.queue.pop(0)
            try:
                if operation.executemany:
                    cursor.executemany(operation.sql, operation.args)
                else:
                    cursor.execute(operation.sql, operation.args)
            except Exception as err:
                print('error occurred')
                connection.close()
                self.error_log = err
                self.op_error = operation
                self.fetchable = 0
                self.queue.clear()
                self.results = fetch
                return False
            else:
                if operation.fetch:
                    if operation.limit:
                        fetch.append(cursor.fetchmany(operation.limit))
                    else:
                        fetch.append(cursor.fetchall())
                if not commit or operation.commit:
                    commit = True
        if commit:
            connection.commit()
        connection.close()
        #print('after non error db op')
        #print(fetch)
        self.fetchable = 0
        self.queue.clear()
        self.results = fetch
        return True
    
    def executemany_aggregate(self):
        """
        Used by run() method to convert multiple sqlite execute() calls into one executemany() if possible.
        """
        if len(self.queue) > 1:
            reference_op = None
            for op in self.queue:
                if not op.fetch:
                    if reference_op:
                        if op.sql == reference_op.sql:
                            if reference_op.executemany:
                                reference_op.args.append(op.args)
                            else:
                                reference_op.args = [reference_op.args, op.args]
                                reference_op.executemany = True
                            op.delete = True
                        else:
                            reference_op = op
                    else:
                        reference_op = op
            self.remove_to_deletes()

    def remove_to_deletes(self):
        """
        Used inside executemany_aggregate() method.
        """
        go = True
        while go:
            go = False
            for op in self.queue:
                if op.delete:
                    self.queue.remove(op)
                    go = True
                    break
    
    def discart(self):
        """
        Used to clear up the query queue (Main().queue) before calling the run() method to abort them.
        """
        self.queue.clear()
        self.fetchable = 0
    
    def get(self, fetch_number: int):
        """
        A method for getting back results without having to manipulate Main.results attribute (works as a getter for single results).
        """
        return self.results[fetch_number]


class Operation():
    """
    The end result of all Table instance method calls. As operations to the database through this plugin are not executed imediately,
    the Operation object is a data structure that represents the operation itself that gets queued to only be executed upon
    a run() call.
    Should only be operated through the Table instance methods and the run() and discart() Main instance methods.
    """
    
    def __init__(self, sql: str, args: tuple, limit: int, fetch: bool, commit: bool, executemany: bool=False, delete: bool=False):
        self.sql = sql
        self.args = args
        self.limit = limit
        self.fetch = fetch
        self.commit = commit
        self.executemany = executemany
        self.delete = delete
    
    def __str__(self):
        if self.executemany:
            return 'executemany ' + self.sql + str(self.args)
        else:
            return 'execute ' + self.sql + ' (' + ', '.join(self.args) + ')'

    def __repr__(self):
        return 'Operation({}, {}, {}, {})'.format(self.sql, self.args, self.fetch, self.commit)



class Table():

    def __init__(self, name:str, priority: str, main: Main, columns: list):
        """
        self.main is the database main object reference to which the table instance bellongs to.
        self.name is the name of the table with will be also used to name the variable containing the table object on the main object.
        self.columns is a list of all columns names of the table in the database as strings.
        self.priority is a string with the name of the most important column in the table, generally the name of the entry item or another unique information.
        """
        self.main = main
        self.name = name
        self.columns = columns
        self.priority = priority  # not necessarily is trully the unique - used as standart column if not specified

    @property
    def user_columns(self):
        """
        Presents the operable columns (removes rowid from the columns list).
        """
        if self.columns[0] == 'rowid':
            return self.columns[1:]
        else:
            return self.columns

    def __call__(self, *columns: str, att=None, limit: int=0, order: str or None=None, desc: bool=False):
        """
        Note that as being a __call__() dunder method, it is called with the table instance as a function.
        This is used to make SELECT queries and is the only table method that retrieves data from de db, as the other ones are just used to modify it.
        In other word, this is the only method that will produce fetch data after a Main.run() call.
        It returns an integer that should be used as index for the results list on the Main database object
        to keep track on the results of the SELECT query after a Main.run() method call.
        """
        args = tuple()
        if all(column in self.columns for column in columns):  # check if all collumn given really exist in the refered table, otherwise raise NameError
            if len(columns) == 0:  # if no column is given, query should return all entries. Note: empty tuples return True for the previous check
                    cols = '*'
            elif len(columns) == 1:
                    cols = columns[0]
            else:
                    cols = ', '.join(columns)
            sql = "SELECT {} FROM {}".format(cols, self.name)
            if att:
                if not isinstance(att, dict):  # check if there was just one att given (should be string) or a dict of columns-arguments pairs
                    sql += " WHERE {}=?".format(self.priority)
                    args = (att,) # args should be a tuple even with only one arg
                else:
                    keys = tuple(att.keys())  # att should be a dict?
                    if all(column in self.columns for column in keys):
                        if len(keys) == 1:
                            sql += ' WHERE ' + keys[0] + '=?'
                        else:
                            sql += ' WHERE ' + '=? AND '.join(keys) + '=?'
                        args = tuple(att[key] for key in keys)
                    else:
                        raise NameError('Column for attribute does not exist in referred table.')
            if order:
                if order in self.columns:
                    sql += ' ORDER BY {}'.format(order)
                else:
                    raise NameError('ORDER column does not exist in referred table.')
                if desc:
                    sql += ' DESC'
            self.main.queue.append(Operation(sql, args, limit, True, False))
            self.main.fetchable += 1
            return self.main.fetchable - 1
        else:
            raise NameError('Requested column query does not exist in referred table.')

    def insert(self, *args: str):
        """
        call sintax:
        <database>.<table>.insert(args)

        add one entry to database
        number of args must match number of columns (except rowid)
        """
        args_quantity = len(self.user_columns)
        assert len(args) == args_quantity, "Arguments should match {} columns in order: {}.".format(self.name, ', '.join(self.user_columns))
        sql = 'INSERT INTO {} VALUES (?{})'.format(self.name, ', ?'*(args_quantity - 1))
        self.main.queue.append(Operation(sql, args, 0, False, True))
    
    def delete(self, arg, column: str=''):
        """
        call sintax:
        <database>.<table>.delete(arg)

        deletes only one specific entry
        accepts a dict as arg for multiple reference info
        """
        if column == '':
            column = self.priority
        if isinstance(arg, dict):
            columns = tuple(arg.keys())
            args = tuple(arg[key] for key in columns)
            self.main.queue.append(Operation('DELETE FROM {} WHERE {}=?'.format(self.name, '=? AND '.join(columns)), args, 0, False, True))
        else:
            self.main.queue.append(Operation('DELETE FROM {} WHERE {}=?'.format(self.name, column), (arg,), 0, False, True))
    
    def update(self, new_info, ref_info, up_column: str='', ref_column: str=''):
        """
        Call sintax:
        <database>.<table>.update(<new_info>, <ref_info>, up_column=<up_column>, ref_column=<ref_column>orblank)

        Output:
        sql: UPDATE <table> SET <up_column>=? WHERE <ref_column>=?
        args: (new_info + ref_info)

        Example:
        call: db.rpg_models.update('a', 'b', up_column='c')
        output: Operation(UPDATE rpg_models SET c=? WHERE model_name=?, ('a', 'b'), False, True)
        """
        sql_1 = 'UPDATE {}'.format(self.name)
        if isinstance(new_info, dict):
            up_columns = tuple(new_info.keys())
            new_info = tuple(new_info[key] for key in up_columns)
            sql_2 = 'SET {}=?'.format('=?, '.join(up_columns))
        else:
            if up_column == '':
                self.main.error_log = 'table update method call should inform up_column when not presenting column-value dictionary'
                return False
            sql_2 = 'SET {}=?'.format(up_column)
            new_info = (new_info,)
        if isinstance(ref_info, dict):
            ref_columns = tuple(ref_info.keys())
            ref_info = tuple(ref_info[key] for key in ref_columns)
            sql_3 = 'WHERE {}=?'.format('=? AND '.join(ref_columns))
        else:
            ref_column = self.priority
            sql_3 = 'WHERE {}=?'.format(ref_column)
            ref_info = (ref_info,)
        self.main.queue.append(Operation(' '.join((sql_1, sql_2, sql_3)), new_info + ref_info, 0, False, True))
        return True
