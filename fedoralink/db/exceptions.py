class RepositoryException(Exception):
    def __init__(self, msg, cause=None, url=None, code=None, hdrs=None):
        super().__init__(msg)
        self.cause = cause
        self.url = url
        self.code = code
        self.hdrs = hdrs