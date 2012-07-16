

class ConnectionNotFoundError(Exception):
    """Raised whenever there is an attempt to find a connection and the
    connection is unable to be found
    """


class ConnectionExistsError(Exception):
    """Raised whenever there is an attempt to save a connection and the
    connection already exists
    """
