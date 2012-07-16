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

social_connection_created = signals.signal("connection-created")

social_connection_failed = signals.signal("connection-failed")

social_connection_removed = signals.signal("connection-removed")

social_login_failed = signals.signal("login-failed")

social_login_completed = signals.signal("login-success")
