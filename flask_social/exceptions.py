# -*- coding: utf-8 -*-
"""
    flask.ext.social.exceptions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains the Flask-Social exceptions

    :copyright: (c) 2012 by Matt Wright.
    :license: MIT, see LICENSE for more details.
"""

class ConnectionNotFoundError(Exception):
    """Raised whenever there is an attempt to find a connection and the
    connection is unable to be found
    """


class ConnectionExistsError(Exception):
    """Raised whenever there is an attempt to save a connection and the
    connection already exists
    """
