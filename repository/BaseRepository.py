import pymysql

from model.Object import Object


class BaseRepository:
    def __init__(self, table: str):
        self.host = 'localhost'
        self.user = 'assistiverobotadm'
        self.password = 'remember'
        self.db = 'assistive_robot'
        self.con = None
        self.cur = None
        self.table = table

    def connect(self):
        """ Connect to MySQL database """
        self.con = pymysql.connect(host=self.host,
                                   user=self.user,
                                   password=self.password,
                                   db=self.db,
                                   cursorclass=pymysql.cursors.DictCursor)
        self.cur = self.con.cursor()

    def close_connection(self):
        """ Close database connection """
        self.con.close()

    def execute(self, query: str, value: str = None):
        """ Execute sql query """
        self.cur.execute(query, value)
        return self.cur.fetchall()

    def __save(self):
        """ Commit change in database """
        self.con.commit()
        self.cur.fetchone()

    def __get_last_row_id(self):
        """ Get cursor last row id """
        return self.cur.lastrowid

    def __read(self, **kwargs) -> str:
        """ Generates SQL for a SELECT statement matching the kwargs passed. """
        query = list()
        query.append("SELECT * FROM %s " % self.table)
        if kwargs:
            query.append("WHERE " + " AND ".join("%s = '%s'" % (k, v) for k, v in kwargs.items()))
        query.append(";")
        return "".join(query)

    def __insert(self, **kwargs):
        """ insert rows into objects table
            given the key-value pairs in kwargs """
        filtered = {k: v for k, v in kwargs.items() if v is not None}
        keys = ["%s" % k for k in filtered]
        values = ["'%s'" % v for v in filtered.values()]
        sql = list()
        sql.append("INSERT INTO %s (" % self.table)
        sql.append(", ".join(keys))
        sql.append(") VALUES (")
        sql.append(", ".join(values))
        sql.append(");")
        return "".join(sql)

    def __insert_on_duplicate_update(self, **kwargs):
        """ update/insert rows into objects table (update if the row already exists)
            given the key-value pairs in kwargs """
        keys = ["%s" % k for k in kwargs]
        values = ["'%s'" % v for v in kwargs.values()]
        sql = list()
        sql.append("INSERT INTO %s (" % self.table)
        sql.append(", ".join(keys))
        sql.append(") VALUES (")
        sql.append(", ".join(values))
        sql.append(") ON DUPLICATE KEY UPDATE ")
        sql.append(", ".join("%s = '%s'" % (k, v) for k, v in kwargs.items()))
        sql.append(";")
        return "".join(sql)

    def __get_result(self, query: str):
        """ Return result from database. """
        self.connect()
        result = self.execute(query)
        self.close_connection()
        if len(result) == 1:
            return Object(result[0])
        elif len(result) > 1:
            return [Object(obj) for obj in result]
        else:
            return None

    def find_all(self):
        query = self.__read()
        return self.__get_result(query)

    def find_by(self, **kwargs):
        query = self.__read(**kwargs)
        return self.__get_result(query)

    def insert(self, **kwargs) -> int:
        query = self.__insert(**kwargs)
        self.connect()
        self.execute(query)
        self.__save()
        print('saved')
        row_id = self.__get_last_row_id()
        self.close_connection()
        return row_id

    def update(self, **kwargs):
        query = self.__insert_on_duplicate_update(**kwargs)
        self.connect()
        self.execute(query)
        self.__save()
        self.close_connection()