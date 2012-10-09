# -*- coding: utf-8 -*-
"""
    flask.ext.social.signals
    ~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains the Flask-Social signals

    :copyright: (c) 2012 by Matt Wright.
    :license: MIT, see LICENSE for more details.
"""

import blinker

signals = blinker.Namespace()

connection_created = signals.signal("connection-created")

connection_failed = signals.signal("connection-failed")

connection_removed = signals.signal("connection-removed")

login_failed = signals.signal("login-failed")

login_completed = signals.signal("login-success")
