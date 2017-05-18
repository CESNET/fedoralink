class DatabaseCursor(object):
    def __init__(self, connection):
        self.connection = connection
        self.current_query = None
        self.current_params = None
        self.scanner = None
        self.lastrowid = None

    def close(self):
        self.connection.disconnect()

    def execute(self, query, params=None):
        self.current_query = query
        self.current_params = params
        self.scanner = self.connection.execute(query, params)

    def executemany(self, sql, params):
        """ Repeatedly executes a SQL statement. """
        raise NotImplementedError('Not yet implemented')

    def fetchall(self):
        """ Fetches all rows from the resultset. """
        ret = []
        while True:
            r = self.fetchone()
            if not r:
                break
            ret.append(r)
        return ret

    def fetchmany(self, n):
        """ Fetches several rows from the resultset. """
        ret = []
        for i in range(n):
            try:
                ret.append(next(self.scanner))
            except StopIteration:
                break
        return ret

    def fetchone(self):
        try:
            return [next(self.scanner)]
        except StopIteration:
            return None

    def __iter__(self):
        return self

    def __next__(self):
        return self.fetchmany(1)[0]
