# -*- coding: utf-8 -*-
"""
    flask.ext.social.utils
    ~~~~~~~~~~~~~~~~~~~~~~

    This module contains the Flask-Social utils

    :copyright: (c) 2012 by Matt Wright.
    :license: MIT, see LICENSE for more details.
"""

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
    url = url_for('flask_social.' + endpoint, provider_id=provider_id)
    return request.url_root[:-1] + url


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


class RecursiveDictionary(dict):
    """RecursiveDictionary provides the methods rec_update and iter_rec_update
    that can be used to update member dictionaries rather than overwriting
    them."""
    def rec_update(self, other, **third):
        """Recursively update the dictionary with the contents of other and
        third like dict.update() does - but don't overwrite sub-dictionaries.

        Example:
        >>> d = RecursiveDictionary({'foo': {'bar': 42}})
        >>> d.rec_update({'foo': {'baz': 36}})
        >>> d
        {'foo': {'baz': 36, 'bar': 42}}
        """
        try:
            iterator = other.iteritems()
        except AttributeError:
            iterator = other
        self.iter_rec_update(iterator)
        self.iter_rec_update(third.iteritems())

    def iter_rec_update(self, iterator):
        for (key, value) in iterator:
            if key in self and \
               isinstance(self[key], dict) and isinstance(value, dict):
                self[key] = RecursiveDictionary(self[key])
                self[key].rec_update(value)
            else:
                self[key] = value
