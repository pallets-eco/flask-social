# -*- coding: utf-8 -*-
"""
    flask.ext.social.datastore
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains an abstracted social connection datastore.

    :copyright: (c) 2012 by Matt Wright.
    :license: MIT, see LICENSE for more details.
"""

from flask_security.datastore import SQLAlchemyDatastore, MongoEngineDatastore


class ConnectionDatastore(object):
    """Abstracted oauth connection datastore. Always extend this class and
    implement parent methods

    :param db: An instance of a configured databse manager from a Flask
               extension such as Flask-SQLAlchemy or Flask-MongoEngine"""

    def __init__(self, connection_model):
        self.connection_model = connection_model

    def find_connection(self, **kwargs):
        raise NotImplementedError

    def find_connections(self, **kwargs):
        raise NotImplementedError

    def create_connection(self, **kwargs):
        return self.put(self.connection_model(**kwargs))

    def delete_connection(self, **kwargs):
        """Remove a single connection to a provider for the specified user
        """
        conn = self.find_connection(**kwargs)
        if not conn:
            return False
        self.delete(conn)
        return True

    def delete_connections(self, **kwargs):
        """Remove a single connection to a provider for the specified user
        """
        rv = False
        for c in self.find_connections(**kwargs):
            self.delete(c)
            rv = True
        return rv


class SQLAlchemyConnectionDatastore(SQLAlchemyDatastore, ConnectionDatastore):
    """A SQLAlchemy datastore implementation for Flask-Social."""

    def __init__(self, db, connection_model):
        SQLAlchemyDatastore.__init__(self, db)
        ConnectionDatastore.__init__(self, connection_model)

    def _query(self, **kwargs):
        return self.connection_model.query.filter_by(**kwargs)

    def find_connection(self, **kwargs):
        return self._query(**kwargs).first()

    def find_connections(self, **kwargs):
        return self._query(**kwargs)


class MongoEngineConnectionDatastore(MongoEngineDatastore, ConnectionDatastore):
    """A MongoEngine datastore implementation for Flask-Social."""

    def __init__(self, db, connection_model):
        MongoEngineDatastore.__init__(self, db)
        ConnectionDatastore.__init__(self, connection_model)

    def _query(self, **kwargs):
        return self.connection_model.objects(**kwargs)

    def find_connection(self, **kwargs):
        return self._query(**kwargs).first()

    def find_connections(self, **kwargs):
        return self._query(**kwargs)
