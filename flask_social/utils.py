# -*- coding: utf-8 -*-
"""
    flask.ext.social.utils
    ~~~~~~~~~~~~~~~~~~~~~~

    This module contains the Flask-Social utils

    :copyright: (c) 2012 by Matt Wright.
    :license: MIT, see LICENSE for more details.
"""

import os
import pkgutil
from importlib import import_module

from flask import current_app, url_for, request


def get_class_from_string(clazz_name):
    """Get a reference to a class by its configuration key name."""
    cv = clazz_name.split('::')
    cm = import_module(cv[0])
    return getattr(cm, cv[1])


def config_value(key, app=None):
    app = app or current_app
    return app.config['SOCIAL_' + key.upper()]


def get_display_name(provider_id):
    """Get the display name of the provider

    param: provider_id: The provider ID
    param: config: The option config context
    """
    config = current_app.config['SOCIAL_%s' % provider_id.upper()]
    return config['display_name']


def get_authorize_callback(endpoint, provider_id):
    """Get a qualified URL for the provider to return to upon authorization

    param: endpoint: Absolute path to append to the application's host
    """
    url = url_for('flask_social.' + endpoint, provider_id=provider_id)
    return request.url_root[:-1] + url


def get_remote_app(provider_id):
    """Get the configured instance of the provider API

    param: provider_id: The ID of the provider to retrive
    """
    return current_app.extensions['social'].providers[provider_id]


def get_default_provider_names():
    from flask_social import providers
    pkg = os.path.dirname(providers.__file__)
    return [name for _, name, _ in pkgutil.iter_modules([pkg])]


def get_config(app):
    """Conveniently get the social configuration for the specified
    application without the annoying 'SOCIAL_' prefix.

    :param app: The application to inspect
    """
    items = app.config.items()
    prefix = 'SOCIAL_'

    def strip_prefix(tup):
        return (tup[0].replace(prefix, ''), tup[1])

    return dict([strip_prefix(i) for i in items if i[0].startswith(prefix)])
