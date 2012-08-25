# -*- coding: utf-8 -*-
"""
    flask.ext.social.core
    ~~~~~~~~~~~~~~~~~~~~~

    This module contains the Flask-Social core

    :copyright: (c) 2012 by Matt Wright.
    :license: MIT, see LICENSE for more details.
"""

from flask import current_app, redirect
from flask.ext.security import current_user
from flask.ext.oauth import OAuth
from werkzeug.local import LocalProxy

from flask.ext.security.utils import get_url, do_flash

from .utils import get_display_name, config_value, get_config, \
     get_default_provider_names, get_class_from_string
from .views import create_blueprint, login_handler, connect_handler

_security = LocalProxy(lambda: current_app.extensions['security'])

_social = LocalProxy(lambda: current_app.extensions['social'])

_datastore = LocalProxy(lambda: _social.datastore)

_logger = LocalProxy(lambda: current_app.logger)

default_config = {
    'SOCIAL_BLUEPRINT_NAME': 'flask_social',
    'SOCIAL_URL_PREFIX': None,
    'SOCIAL_CONNECT_ALLOW_VIEW': '/',
    'SOCIAL_CONNECT_DENY_VIEW': '/',
    'SOCIAL_POST_OAUTH_CONNECT_SESSION_KEY': 'post_oauth_connect_url',
    'SOCIAL_POST_OAUTH_LOGIN_SESSION_KEY': 'post_oauth_login_url'
}


class Provider(object):
    def __init__(self, id, remote_app, connection_factory,
                 login_handler, connect_handler):
        self.id = id
        self.remote_app = remote_app
        self.connection_factory = connection_factory
        self.get_connection = connection_factory
        self.login_handler = login_handler
        self.connect_handler = connect_handler
        self.tokengetter = remote_app.tokengetter
        self.authorized_handler = remote_app.authorized_handler
        self.authorize = remote_app.authorize

    def __str__(self):
        return '<Provider name=%s>' % self.remote_app.name


class ConnectionFactory(object):
    """The ConnectionFactory class creates `Connection` instances for the
    specified provider from values stored in the connection repository. This
    class should be extended whenever adding a new service provider to an
    application.
    """
    def __init__(self, provider_id):
        """Creates an instance of a `ConnectionFactory` for the specified
        provider

        :param provider_id: The provider ID
        """
        self.provider_id = provider_id

    def get_api(self, connection):
        raise NotImplementedError

    def get_connection(self, user_id=None, provider_user_id=None):
        """Get a connection to the provider for the specified local user
        and the specified provider user

        :param user_id: The local user ID
        :param provider_user_id: The provider user ID
        """

        query_args = dict(user_id=user_id or current_user.get_id(),
                          provider_id=self.provider_id)

        if provider_user_id:
            query_args.set('provider_user_id', provider_user_id)

        connection = _datastore.find_connection(**query_args)

        if connection is not None:
            setattr(connection, 'api', self.get_api(connection))

        return connection

    def __call__(self, **kwargs):
        return self.get_connection(**kwargs)


class OAuthHandler(object):
    """The `OAuthHandler` class is a base class for classes that handle OAuth
    interactions. See `LoginHandler` and `ConnectHandler`
    """
    def __init__(self, provider_id, callback=None):
        self.provider_id = provider_id
        self.callback = callback


class LoginHandler(OAuthHandler):
    """ A `LoginHandler` handles the login procedure after receiving
    authorization from the service provider. The goal of a `LoginHandler` is
    to retrieve the user ID of the account that granted access to the local
    application. This ID is then used to find a connection within the local
    application to the provider. If a connection is found, the local user is
    retrieved from the user service and logged in autmoatically.
    """
    def get_provider_user_id(self, response):
        """Gets the provider user ID from the OAuth reponse.
        :param response: The OAuth response in the form of a dictionary
        """
        raise NotImplementedError('get_provider_user_id')

    def __call__(self, response):
        display_name = get_display_name(self.provider_id)

        _logger.debug('Received login response from '
                      '%s: %s' % (display_name, response))

        if response is None:
            do_flash('Access was denied to your %s '
                     'account' % display_name, 'error')
            return redirect(_security.login_manager.login_view)

        kwargs = dict(oauth_response=response,
                      provider_id=self.provider_id,
                      provider_user_id=self.get_provider_user_id(response))

        return self.callback(**kwargs)


class ConnectHandler(OAuthHandler):
    """The `ConnectionHandler` class handles the connection procedure after
    receiving authorization from the service provider. The goal of a
    `ConnectHandler` is to retrieve the connection values that will be
    persisted by the connection service.
    """
    def get_connection_values(self, response):
        """Get the connection values to persist using values from the OAuth
        response

        :param response: The OAuth response as a dictionary of values
        """
        raise NotImplementedError('get_connection_values')

    def __call__(self, response, user_id=None):
        display_name = get_display_name(self.provider_id)

        _logger.debug('Received connect response from '
                      '%s. %s' % (display_name, response))

        if response is None:
            do_flash('Access was denied by %s' % display_name, 'error')
            return redirect(get_url(config_value('CONNECT_DENY_VIEW')))

        cv = self.get_connection_values(response)
        return self.callback(cv, user_id)


def _get_state(app, datastore, oauth, providers, **kwargs):
    for key, value in get_config(app).items():
        kwargs[key.lower()] = value

    kwargs.update(dict(
        app=app,
        datastore=datastore,
        oauth=oauth,
        providers=providers))

    return _SocialState(**kwargs)


class _SocialState(object):

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key.lower(), value)


def _get_handler(clazz_name, config, callback):
    return get_class_from_string(clazz_name)(callback=callback, **config)


def _get_token():
    # Social doesn't use the builtin remote method calls feature of the
    # Flask-OAuth extension so we don't need to return a token. This does,
    # however, need to be configured
    return None


def _create_provider(config, oauth):
    provider_id = config['id']
    o_config = config['oauth']

    remote_app = oauth.remote_app(provider_id, **o_config)

    cf_class_name = config['connection_factory']
    ConnectionFactoryClass = get_class_from_string(cf_class_name)

    cf = ConnectionFactoryClass(**o_config)
    lh = _get_handler(config['login_handler'], o_config, login_handler)
    ch = _get_handler(config['connect_handler'], o_config, connect_handler)

    service_provider = Provider(provider_id, remote_app, cf, lh, ch)
    service_provider.tokengetter(_get_token)
    return service_provider


class Social(object):

    def __init__(self, app=None, datastore=None):
        self.app = app
        self.datastore = datastore
        self.oauth = OAuth()

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

        default_provider_names = get_default_provider_names()

        provider_configs = []

        # Look for providers in config
        for key in app.config.keys():
            if key.startswith('SOCIAL_') and key not in default_config:
                provider_id = key.replace('SOCIAL_', '').lower()

                if provider_id not in default_provider_names:
                    # Custom provider, grab the whole config
                    provider_configs.append(app.config.get(key))
                    continue

                # Default provider, update with defaults
                co = 'flask_social.providers.%s::default_config' % provider_id

                d_config = get_class_from_string(co).copy()
                d_oauth_config = d_config['oauth'].copy()

                d_config.update(app.config[key])
                d_oauth_config.update(app.config[key]['oauth'])
                d_config['oauth'] = d_oauth_config

                app.config[key] = d_config

                provider_configs.append(d_config)

        providers = dict()

        for p in provider_configs:
            provider = _create_provider(p, self.oauth)
            providers[provider.id] = provider

        state = _get_state(app, datastore, self.oauth, providers)
        app.register_blueprint(create_blueprint(state, __name__))
        app.extensions['social'] = state

        return state

    def __getattr__(self, name):
        return getattr(self._state, name, None)
