# -*- coding: utf-8 -*-
"""
    flask.ext.social.core
    ~~~~~~~~~~~~~~~~~~~~~

    This module contains the Flask-Social core

    :copyright: (c) 2012 by Matt Wright.
    :license: MIT, see LICENSE for more details.
"""
from importlib import import_module

from flask import current_app
from flask_oauthlib.client import OAuthRemoteApp as BaseRemoteApp
from flask.ext.security import current_user
from werkzeug.local import LocalProxy

from .utils import get_config, update_recursive
from .views import create_blueprint

_security = LocalProxy(lambda: current_app.extensions['security'])

_social = LocalProxy(lambda: current_app.extensions['social'])

_datastore = LocalProxy(lambda: _social.datastore)

_logger = LocalProxy(lambda: current_app.logger)

default_config = {
    'SOCIAL_BLUEPRINT_NAME': 'social',
    'SOCIAL_URL_PREFIX': None,
    'SOCIAL_CONNECT_ALLOW_VIEW': '/',
    'SOCIAL_CONNECT_DENY_VIEW': '/',
    'SOCIAL_POST_OAUTH_CONNECT_SESSION_KEY': 'post_oauth_connect_url',
    'SOCIAL_POST_OAUTH_LOGIN_SESSION_KEY': 'post_oauth_login_url',
    'SOCIAL_APP_URL': 'http://localhost'
}


class OAuthRemoteApp(BaseRemoteApp):

    def __init__(self, id, module, install, *args, **kwargs):
        BaseRemoteApp.__init__(self, None, **kwargs)
        self.id = id
        self.module = module

    def get_connection(self):
        return _social.datastore.find_connection(provider_id=self.id,
                                                 user_id=current_user.id)

    def get_api(self):
        module = import_module(self.module)
        connection = self.get_connection()
        if connection is None:
            return None
        return module.get_api(connection=connection,
                              consumer_key=self.consumer_key,
                              consumer_secret=self.consumer_secret)


def _get_state(app, datastore, providers, **kwargs):
    config = get_config(app)

    for key in providers.keys():
        config.pop(key.upper())

    for key, value in config.items():
        kwargs[key.lower()] = value

    kwargs.update(dict(
        app=app,
        datastore=datastore,
        providers=providers))

    return _SocialState(**kwargs)


class _SocialState(object):

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key.lower(), value)

    def __getattr__(self, name):
        try:
            return self.providers[name]
        except KeyError:
            msg = "'_SocialState' object has no attribute '%s'" % name
            raise AttributeError(msg)


def _get_token():
    # Social doesn't use the builtin remote method calls feature of the
    # Flask-OAuth extension so we don't need to return a token. This does,
    # however, need to be configured
    return None


class Social(object):

    def __init__(self, app=None, datastore=None):
        self.app = app
        self.datastore = datastore

        if app is not None and datastore is not None:
            self._state = self.init_app(app, datastore)

    def init_app(self, app, datastore=None):
        """Initialize the application with the Social extension

        :param app: The Flask application
        :param datastore: Connection datastore instance
        """

        datastore = datastore or self.datastore

        for key, value in default_config.items():
            app.config.setdefault(key, value)

        providers = dict()

        for key, config in app.config.items():
            if not key.startswith('SOCIAL_') or config is None or key in default_config:
                continue

            suffix = key.lower().replace('social_', '')
            default_module_name = 'flask_social.providers.%s' % suffix
            module_name = config.get('module', default_module_name)
            module = import_module(module_name)
            config = update_recursive(module.config, config)

            providers[config['id']] = OAuthRemoteApp(**config)
            providers[config['id']].tokengetter(_get_token)

        state = _get_state(app, datastore, providers)

        app.register_blueprint(create_blueprint(state, __name__))
        app.extensions['social'] = state

        return state

    def __getattr__(self, name):
        return getattr(self._state, name, None)
