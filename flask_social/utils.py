# -*- coding: utf-8 -*-
"""
    flask.ext.social.utils
    ~~~~~~~~~~~~~~~~~~~~~~

    This module contains the Flask-Social utils

    :copyright: (c) 2012 by Matt Wright.
    :license: MIT, see LICENSE for more details.
"""
import collections

from importlib import import_module

from flask import current_app, url_for, request, abort


def get_provider_or_404(provider_id):
    try:
        return current_app.extensions['social'].providers[provider_id]
    except KeyError:
        abort(404)


def config_value(key, app=None):
    app = app or current_app
    return app.config['SOCIAL_' + key.upper()]


def get_authorize_callback(endpoint, provider_id):
    """Get a qualified URL for the provider to return to upon authorization

    param: endpoint: Absolute path to append to the application's host
    """
    endpoint_prefix = config_value('BLUEPRINT_NAME')
    url = url_for(endpoint_prefix + '.' + endpoint, provider_id=provider_id)
    return request.url_root[:-1] + url


def get_connection_values_from_oauth_response(provider, oauth_response):
    if oauth_response is None:
        return None

    module = import_module(provider.module)

    return module.get_connection_values(
        oauth_response,
        consumer_key=provider.consumer_key,
        consumer_secret=provider.consumer_secret)

def get_token_pair_from_oauth_response(provider, oauth_response):
    module = import_module(provider.module)
    return module.get_token_pair_from_response(oauth_response)

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


def update_recursive(d, u):
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = update_recursive(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d
