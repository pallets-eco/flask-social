# -*- coding: utf-8 -*-
"""
    flask.ext.social
    ~~~~~~~~~~~~~~~~

    Flask-Social is a Flask extension that aims to add simple OAuth provider
    integration for Flask-Security

    :copyright: (c) 2012 by Matt Wright.
    :license: MIT, see LICENSE for more details.
"""

from .core import Social
from .datastore import SQLAlchemyConnectionDatastore, \
     MongoEngineConnectionDatastore
from .signals import social_connection_created, social_connection_failed, \
     social_connection_removed, social_login_failed, social_login_completed
