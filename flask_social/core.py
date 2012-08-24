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

from flask.ext.security import login_required

from .utils import get_display_name, do_flash, config_value, \
     get_default_provider_names, get_class_from_string
from .views import create_blueprint, login_handler, connect_handler

_security = LocalProxy(lambda: current_app.extensions['security'])

_social = LocalProxy(lambda: current_app.extensions['social'])

_datastore = LocalProxy(lambda: _social.datastore)

_logger = LocalProxy(lambda: current_app.logger)

default_config = {
    'SOCIAL_URL_PREFIX': '/social',
    'SOCIAL_APP_URL': 'http://127.0.0.1:5000',
    'SOCIAL_CONNECT_ALLOW_REDIRECT': '/profile',
    'SOCIAL_CONNECT_DENY_REDIRECT': '/profile',
    'SOCIAL_FLASH_MESSAGES': True,
    'SOCIAL_POST_OAUTH_CONNECT_SESSION_KEY': 'post_oauth_connect_url',
    'SOCIAL_POST_OAUTH_LOGIN_SESSION_KEY': 'post_oauth_login_url'
}


class Provider(object):
    def __init__(self, remote_app, connection_factory,
                 login_handler, connect_handler):
        self.remote_app = remote_app
        self.connection_factory = connection_factory
        self.login_handler = login_handler
        self.connect_handler = connect_handler

    def get_connection(self, *args, **kwargs):
        rv = self.connection_factory(*args, **kwargs)
        return rv

    def tokengetter(self, *args, **kwargs):
        return self.remote_app.tokengetter(*args, **kwargs)

    def authorized_handler(self, *args, **kwargs):
        return self.remote_app.authorized_handler(*args, **kwargs)

    def authorize(self, *args, **kwargs):
        return self.remote_app.authorize(*args, **kwargs)

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

    def _create_api(self, connection):
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
            setattr(connection, 'api', self._create_api(connection))

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

        uid = self.get_provider_user_id(response)

        return self.callback(self.provider_id, uid, response)


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

            return redirect(config_value('CONNECT_DENY_REDIRECT'))

        cv = self.get_connection_values(response)

        return self.callback(cv, user_id)


class _SocialState(object):

    def __init__(self, app, datastore, oauth, providers):
        self.app = app
        self.datastore = datastore
        self.oauth = oauth

        for key, value in providers.items():
            setattr(self, key, value)


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

        # Configure the URL handlers for each fo the configured providers
        blueprint = create_blueprint(app, 'flask_social', __name__,
            url_prefix=config_value('URL_PREFIX', app=app))

        providers = {}

        for pc in provider_configs:
            pid, p = configure_provider(app, blueprint, self.oauth, pc)
            providers[pid] = p
            app.logger.debug('Registered social provider: %s' % p)

        app.register_blueprint(blueprint)

        state = self._get_state(app, datastore or self.datastore,
                                self.oauth, providers,)

        if not hasattr(app, 'extensions'):
            app.extensions = {}

        app.extensions['social'] = state

        return state

    def _get_state(self, app, datastore, oauth, providers):
        assert app is not None
        assert datastore is not None
        assert oauth is not None
        assert providers is not None

        return _SocialState(app, datastore, oauth, providers)

    def __getattr__(self, name):
        return getattr(self._state, name, None)


def configure_provider(app, blueprint, oauth, config):
    """Configures and registers a service provider connection Factory with the
    main application.
    """
    provider_id = config['id']
    o_config = config['oauth']

    try:
        o_config['consumer_key']
        o_config['consumer_secret']
    except KeyError:
        raise Exception('consumer_key and/or consumer_secret not found '
                        'for provider %s' % config['display_name'])

    remote_app = oauth.remote_app(provider_id, **o_config)

    def get_handler(clazz_name, config, callback):
        return get_class_from_string(clazz_name)(callback=callback, **config)

    cf_class_name = config['connection_factory']
    ConnectionFactoryClass = get_class_from_string(cf_class_name)

    cf = ConnectionFactoryClass(**o_config)
    lh = get_handler(config['login_handler'], o_config, login_handler)
    ch = get_handler(config['connect_handler'], o_config, connect_handler)

    service_provider = Provider(remote_app, cf, lh, ch)

    @service_provider.tokengetter
    def get_token():
        # Social doesn't use the builtin remote method calls feature of the
        # Flask-OAuth extension so we don't need to return a token. This does,
        # however, need to be configured
        return None

    @blueprint.route('/connect/%s' % provider_id, methods=['GET'],
                     endpoint='connect_%s_callback' % provider_id)
    @login_required
    @service_provider.authorized_handler
    def connect_callback(response):
        """The route which the provider should redirect to after a user
        attempts to connect their account with the provider with their local
        application account
        """
        return getattr(_social, provider_id).connect_handler(response)

    @blueprint.route('/login/%s' % provider_id, methods=['GET'],
                     endpoint='login_%s_callback' % provider_id)
    @service_provider.authorized_handler
    def login_callback(response):
        """The route which the provider should redirect to after a user
        attempts to login with their account with the provider
        """
        return getattr(_social, provider_id).login_handler(response)

    return provider_id, service_provider
