# -*- coding: utf-8 -*-
"""
    flask.ext.social
    ~~~~~~~~~~~~~~~~
    
    Flask-Social is a Flask extension that aims to add simple OAuth provider 
    integration for Flask-Security

    :copyright: (c) 2012 by Matt Wright.
    :license: MIT, see LICENSE for more details.
"""

try:
    import twitter
except ImportError:
    pass

try:
    import facebook
except ImportError:
    pass

from flask.ext.security import (user_datastore, login_manager, 
    get_post_login_redirect, current_user, login_user, login_required, 
    Security, BadCredentialsError, User, get_class_by_name)

from flask import (Blueprint, redirect, flash, session, 
                   request, abort, current_app)

from flask.signals import Namespace
from flask.ext.oauth import OAuth

from werkzeug.local import LocalProxy
from werkzeug.utils import import_string

_signals = Namespace()

URL_PREFIX_KEY =             'SOCIAL_URL_PREFIX'
APP_URL_KEY =                'SOCIAL_APP_URL'
CONNECTION_DATASTORE_KEY =   'SOCIAL_CONNECTION_DATASTORE'
CONNECT_ALLOW_REDIRECT_KEY = 'SOCIAL_CONNECT_ALLOW_REDIRECT'
CONNECT_DENY_REDIRECT_KEY =  'SOCIAL_CONNECT_DENY_REDIRECT'
FLASH_MESSAGES_KEY =         'SOCIAL_FLASH_MESSAGES'

POST_OAUTH_CONNECT_SESSION_KEY = 'post_oauth_connect_url'
POST_OAUTH_LOGIN_SESSION_KEY = 'post_oauth_login_url' 

connection_datastore = LocalProxy(lambda: getattr(
    current_app, current_app.config[CONNECTION_DATASTORE_KEY]))
        
default_config = {
    URL_PREFIX_KEY:             None,
    APP_URL_KEY:                'http://127.0.0.1:5000',
    CONNECTION_DATASTORE_KEY:   'connection_datastore',
    CONNECT_ALLOW_REDIRECT_KEY: '/profile',
    CONNECT_DENY_REDIRECT_KEY:  '/profile',
    FLASH_MESSAGES_KEY:         True
}

default_provider_config = {
    'twitter': {
        'id': 'twitter',
        'display_name': 'Twitter',
        'install': 'pip install python-twitter',
        'login_handler': 'flask.ext.social.TwitterLoginHandler',
        'connect_handler': 'flask.ext.social.TwitterConnectHandler',
        'connection_factory': 'flask.ext.social.TwitterConnectionFactory',
        'oauth': {
            'base_url': 'http://api.twitter.com/1/',
            'request_token_url': 'https://api.twitter.com/oauth/request_token',
            'access_token_url': 'https://api.twitter.com/oauth/access_token',
            'authorize_url': 'https://api.twitter.com/oauth/authenticate',
        },
    },
    'facebook': {
        'id': 'facebook',
        'display_name': 'Facebook',
        'install': 'pip install http://github.com/pythonforfacebook/facebook-sdk/tarball/master',
        'login_handler': 'flask.ext.social.FacebookLoginHandler',
        'connect_handler': 'flask.ext.social.FacebookConnectHandler',
        'connection_factory': 'flask.ext.social.FacebookConnectionFactory',
        'oauth': {
            'base_url': 'https://graph.facebook.com/',
            'request_token_url': None,
            'access_token_url': '/oauth/access_token',
            'authorize_url': 'https://www.facebook.com/dialog/oauth',
        },
    }
}

def get_display_name(provider_id):
    """Get the display name of the provider
    
    param: provider_id: The provider ID
    param: config: The option config context
    """
    config = current_app.config['SOCIAL_%s' % provider_id.upper()]
    return config['display_name']

def get_authorize_callback(endpoint):
    """Get a qualified URL for the provider to return to upon authorization
    
    param: endpoint: Absolute path to append to the application's host
    """
    return '%s%s' % (current_app.config[APP_URL_KEY], endpoint)

def get_remote_app(provider_id):
    """Get the configured instance of the provider API
    
    param: provider_id: The ID of the provider to retrive
    """
    return getattr(current_app.social, provider_id)

class ConnectionNotFoundError(Exception): 
    """Raised whenever there is an attempt to find a connection and the
    connection is unable to be found
    """
    
class ConnectionExistsError(Exception):
    """Raised whenever there is an attempt to save a connection and the
    connection already exists
    """ 

Connection = None

            

def _login_handler(provider_id, provider_user_id, oauth_response):
    """Shared method to handle the signin process 
    """
    if current_user.is_authenticated():
        return redirect("/")
    
    display_name = get_display_name(provider_id)
    
    current_app.logger.debug('Attempting login via %s with provider user '
                     '%s' % (display_name, provider_user_id))
    try:
        method = connection_datastore.get_connection_by_provider_user_id
        connection = method(provider_id, provider_user_id)
        user = user_datastore.with_id(connection.user_id)
        
        if login_user(user):
            redirect_url = session.pop(POST_OAUTH_LOGIN_SESSION_KEY, 
                                       get_post_login_redirect())
            
            current_app.logger.debug('User logged in via %s. Redirecting to '
                                     '%s' % (display_name, redirect_url))
                
            return redirect(redirect_url)
        
        else: 
            current_app.logger.info('Inactive local user attempted '
                                    'login via %s.' % display_name)
            do_flash("Inactive user", "error")
        
    except ConnectionNotFoundError:
        current_app.logger.info('Login attempt via %s failed because '
                                'connection was not found.' % display_name)
        
        msg = '%s account not associated with an existing user' % display_name
        do_flash(msg, 'error')
    
    """    
    except Exception, e:
        current_app.logger.error('Unexpected error signing in '
                                 'via %s: %s' % (display_name, e))
    """    
    social_login_failed.send(current_app._get_current_object(), 
                             provider_id=provider_id, 
                             oauth_response=oauth_response)
    
    return redirect(login_manager.login_view)


def _connect_handler(connection_values, provider_id):
    """Shared method to handle the connection process
    
    :param connection_values: A dictionary containing the connection values
    :param provider_id: The provider ID the connection shoudl be made to
    """
    display_name = get_display_name(provider_id)
    try:
        connection = connection_datastore.save_connection(**connection_values)
        current_app.logger.debug('Connection to %s established '
                                 'for %s' % (display_name, current_user))
        
        social_connection_created.send(current_app._get_current_object(), 
                                       user=current_user, 
                                       connection=connection)
        
        do_flash("Connection established to %s" % display_name, 'success')
        
    except ConnectionExistsError, e:
        current_app.logger.debug('Connection to %s exists already '
                                 'for %s' % (display_name, current_user))
        
        do_flash("A connection is already established with %s "
              "to your account" % display_name, 'notice')
        
    except Exception, e:
        current_app.logger.error('Unexpected error connecting %s account for ' 
                                 'user. Reason: %s' % (display_name, e))
        
        do_flash("Could not make connection to %s. "
              "Please try again later." % display_name, 'error')
    
    redirect_url = session.pop(POST_OAUTH_CONNECT_SESSION_KEY, 
                               current_app.config[CONNECT_ALLOW_REDIRECT_KEY])
    return redirect(redirect_url)


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
        
    def _get_current_user_primary_connection(self):
        return self._get_primary_connection(current_user.get_id())
    
    def _get_primary_connection(self, user_id):
        return connection_datastore.get_primary_connection(
                user_id, self.provider_id)
    
    def _get_specific_connection(self, user_id, provider_user_id):
        return connection_datastore.get_connection(user_id, 
                self.provider_id, provider_user_id)
    
    def _create_api(self, connection):
        raise NotImplementedError("create_api method not implemented")
    
    def get_connection(self, user_id=None, provider_user_id=None):
        """Get a connection to the provider for the specified local user
        and the specified provider user
        
        :param user_id: The local user ID
        :param provider_user_id: The provider user ID
        """
        if user_id == None and provider_user_id == None:
            connection = self._get_current_user_primary_connection()
        if user_id != None and provider_user_id == None:
            connection = self._get_primary_connection(user_id)
        if user_id != None and provider_user_id != None:
            connection = self._get_specific_connection(user_id, 
                                                       provider_user_id)
        
        def as_dict(model):
            rv = {}
            for key in ('user_id', 'provider_id', 'provider_user_id',
                        'access_token', 'secret', 'display_name', 
                        'profile_url', 'image_url'):
                rv[key] = getattr(model, key)
            return rv
        
        return dict(api=self._create_api(connection), 
                    **as_dict(connection))
    
    def __call__(self, **kwargs):
        try:
            return self.get_connection(**kwargs)
        except ConnectionNotFoundError:
            return None


class FacebookConnectionFactory(ConnectionFactory):
    """The `FacebookConnectionFactory` class creates `Connection` instances for
    accounts connected to Facebook. The API instance for Facebook connections
    are instances of the `Facebook Python libary <https://github.com/pythonforfacebook/facebook-sdk>`_.
    """
    def __init__(self, **kwargs):
        super(FacebookConnectionFactory, self).__init__('facebook')
        
    def _create_api(self, connection):
        return facebook.GraphAPI(getattr(connection, 'access_token'))


class TwitterConnectionFactory(ConnectionFactory):
    """The `TwitterConnectionFactory` class creates `Connection` instances for
    accounts connected to Twitter. The API instance for Twitter connections
    are instance of the `python-twitter library <http://code.google.com/p/python-twitter/>`_
    """
    def __init__(self, consumer_key, consumer_secret, **kwargs):
        super(TwitterConnectionFactory, self).__init__('twitter')
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        
    def _create_api(self, connection):
        return twitter.Api(consumer_key=self.consumer_key,
                           consumer_secret=self.consumer_secret, 
                           access_token_key=getattr(connection, 'access_token'), 
                           access_token_secret=getattr(connection, 'secret'))


class OAuthHandler(object):
    """The `OAuthHandler` class is a base class for classes that handle OAuth
    interactions. See `LoginHandler` and `ConnectHandler`
    """
    def __init__(self, provider_id):
        self.provider_id = provider_id

      
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
        raise NotImplementedError("get_provider_user_id")
    
    def __call__(self, response):
        display_name = get_display_name(self.provider_id)
        
        current_app.logger.debug('Received login response from '
                                 '%s. %s' % (display_name, response))
        
        if response is None:
            do_flash("Access was denied to your % account" % display_name, 'error')
            return redirect(login_manager.login_view)
        
        return _login_handler(self.provider_id, 
                              self.get_provider_user_id(response), 
                              response)

   
class TwitterLoginHandler(LoginHandler):
    """The `TwitterLoginHandler` class handles the authorization response from 
    Twitter. The Twitter account's user ID is passed with the authorization 
    response and an extra API call is not necessary.
    """ 
    def __init__(self, **kwargs):
        super(TwitterLoginHandler, self).__init__('twitter')
        
    def get_provider_user_id(self, response):
        return response['user_id'] if response != None else None
    
    
class FacebookLoginHandler(LoginHandler):
    """The `FacebookLoginHandler` class handles the authorization response from
    Facebook. The Facebook account's user ID is not passed in the response, 
    thus it must be retrieved with an API call.
    """
    def __init__(self, **kwargs):
        super(FacebookLoginHandler, self).__init__('facebook')
        
    def get_provider_user_id(self, response):
        if response != None:
            graph = facebook.GraphAPI(response['access_token'])
            profile = graph.get_object("me")
            return profile['id']
        return None


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
        raise NotImplementedError("get_connection_values")
    
    def __call__(self, response):
        display_name = get_display_name(self.provider_id)
        
        current_app.logger.debug('Received connect response from '
                                 '%s. %s' % (display_name, response))
        
        if response is None:
            do_flash("Access was denied by %s" % display_name, 'error')
            return redirect(current_app.config[CONNECT_DENY_REDIRECT_KEY])
        
        return _connect_handler(self.get_connection_values(response), 
                                self.provider_id)
    
        
class TwitterConnectHandler(ConnectHandler):
    """The `TwitterConnectHandler` class handles the connection procedure 
    after a user authorizes a connection from Twitter. The connection values
    are all retrieved from the response, no extra API calls are necessary.
    """
    def __init__(self, **kwargs):
        super(TwitterConnectHandler, self).__init__('twitter')
        self.consumer_key = kwargs['consumer_key']
        self.consumer_secret = kwargs['consumer_secret']
        
    def get_connection_values(self, response=None):
        if not response:
            return None
        
        api = twitter.Api(consumer_key=self.consumer_key,
                          consumer_secret=self.consumer_secret, 
                          access_token_key=response['oauth_token'], 
                          access_token_secret=response['oauth_token_secret'])
        
        user = api.VerifyCredentials()
        
        return dict(
            user_id = current_user.get_id(),
            provider_id = self.provider_id,
            provider_user_id = str(user.id),
            access_token = response['oauth_token'],
            secret = response['oauth_token_secret'],
            display_name = '@%s' % user.screen_name,
            profile_url = "http://twitter.com/%s" % user.screen_name,
            image_url = user.profile_image_url
        )
        
        
class FacebookConnectHandler(ConnectHandler):
    """The `FacebookConnectHandler` class handles the connection procedure 
    after a user authorizes a connection from Facebook. The Facebook acount's 
    user ID is retrieved via an API call, otherwise the token is provided by 
    the response from Facebook.
    """
    def __init__(self, **kwargs):
        super(FacebookConnectHandler, self).__init__('facebook')
        
    def get_connection_values(self, response):
        if not response:
            return None
        
        access_token = response['access_token']
        graph = facebook.GraphAPI(access_token)
        profile = graph.get_object("me")
        profile_url = "http://facebook.com/profile.php?id=%s" % profile['id']
        image_url = "http://graph.facebook.com/%s/picture" % profile['id']
        
        return dict(
            user_id = current_user.get_id(),
            provider_id = self.provider_id,
            provider_user_id = profile['id'],
            access_token = access_token,
            secret = None,
            display_name = profile['username'],
            profile_url = profile_url,
            image_url = image_url
        )


def _configure_provider(app, blueprint, oauth, config):
    """
    Configures and registers a service provider connection Factory with the 
    main application. The connection factory is accessible via:
    
        from flask import current_app as app
        app.social.<provider_id>
    """
    provider_id = config['id']
    o_config = config['oauth']
    
    try:
        o_config['consumer_key']
        o_config['consumer_secret']
    except KeyError:
        raise Exception('consumer_key and/or consumer_secret not found '
                        'for provider %s' % config['display_name'])
    
    service_provider = oauth.remote_app(provider_id, **o_config)
    
    def get_handler(clazz_name, config):
        return get_class_by_name(clazz_name)(**config)
    
    connect_handler = get_handler(config['connect_handler'], o_config)
    login_handler = get_handler(config['login_handler'], o_config)
    
    Factory = get_class_by_name(config['connection_factory'])
    
    setattr(service_provider, 'get_connection', Factory(**o_config))
    setattr(app.social, provider_id, service_provider)
    
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
        return connect_handler(response)
    
    @blueprint.route('/login/%s' % provider_id, methods=['GET'], 
                     endpoint='login_%s_callback' % provider_id)
    @service_provider.authorized_handler
    def login_callback(response):
        """The route which the provider should redirect to after a user
        attempts to login with their account with the provider
        """
        return login_handler(response)
    
        
class Social(object):
    """The `Social` extension adds integration with various service providers to 
    your application. Currently Twitter and Facebook are supported. When 
    properly configured, Social will add endpoints to your app that allows for 
    users to connect their accounts with a service provider and eventually
    login via these accounts as well.
    
    To start the process of connecting a service provider account with a local
    user account perform an HTTP POST to /connect/<provider_id>. This endpoint
    requires that the user be logged in already. This will initiate the OAuth
    flow with the provider. If the user authorizes access the provider should 
    perform an HTTP GET on the same URL. Social will then attempt to store a 
    connection to the account using the response values. Once the connection is 
    made you can retrieve a `Connection` instance for the current user via::
        
        from flask import current_app
        connection = current_app.social.<provider_id>.get_connection()
        connection.api.some_api_method()
        
    Replace <provider_id> with the provider you wish to get a connection to. 
    The above example also illustrates a hypothetical API call. A connection
    includes a configured instance of the provider's API and you can perform
    any API calls the connection's OAuth token allows.
    
    To start the process of a logging in a user through their provider account,
    perform an HTTP POST to /login/<provider_id>. This will initiate the OAuth
    flow with the provider. If the user authorizes access or has already
    authorized access the provider should perform an HTTP GET on the previously
    mentioned URL. Social will attempt to handle the login by checking if a
    connection between the provider account and a local user account. If one
    exists the user is automatically logged in. If a connection does not exist
    the user is redirected to the login view specified by the Auth module.
    
    Additionally, other endpoints are included to help manage connections.
    
    Delete all connections for the logged in user to a provider:
    
        [DELETE] /connect/<provider_id>
    
    Delete a specific connection to a service provider for the logged in user:
    
        [DELETE] /connect/<provider_id>/<provider_user_id>
    """
    def __init__(self, app=None, datastore=None):
        self.init_app(app, datastore)
        
    def init_app(self, app, datastore):
        """Initialize the application with the Social module
        
        :param app: The Flask application
        :param datastore: Connection datastore instance
        """
        from flask.ext import social as s
        s.SocialConnection = datastore.get_models()
        
        blueprint = Blueprint('social', __name__)
        
        configured = {}
        
        for key, value in default_config.items():
            configured[key] = app.config.get(key, value)
        
        app.config.update(configured)
        
        # Set the datastore
        setattr(app, app.config[CONNECTION_DATASTORE_KEY], datastore)
        
        # get service provider configurations
        provider_configs = []
        
        for provider, provider_config in default_provider_config.items():
            provider_key = 'SOCIAL_%s' % provider.upper()
            
            if provider_key in app.config:
                d_config = provider_config.copy()
                
                try:
                    __import__(d_config['id'])
                except ImportError:
                    app.logger.error(
                        'Could not import %s API module. Please install via:\n' 
                        '%s' % (d_config['display_name'], d_config['install']))
                    
                d_oauth_config = d_config['oauth'].copy()
                
                d_config.update(app.config[provider_key])
                d_oauth_config.update(app.config[provider_key]['oauth'])
                d_config['oauth'] = d_oauth_config
                
                app.config[provider_key] = d_config
                provider_configs.append(d_config)
                
        app.oauth = OAuth()
        app.social = self
        
        @blueprint.route('/login/<provider_id>', methods=['POST'])
        def login(provider_id):
            """Starts the provider login OAuth flow"""
            
            if current_user.is_authenticated():
                return redirect(request.referrer or '/')
            
            callback_url = get_authorize_callback('/login/%s' % provider_id)
            display_name = get_display_name(provider_id)
            
            current_app.logger.debug('Starting login via %s account. Callback '
                'URL = %s' % (display_name, callback_url))
            
            post_login = request.form.get('next', get_post_login_redirect())
            session['post_oauth_login_url'] = post_login
            
            return get_remote_app(provider_id).authorize(callback_url)
        
        @blueprint.route('/connect/<provider_id>', methods=['POST'])
        @login_required
        def connect(provider_id):
            """Starts the provider connection OAuth flow"""
            
            callback_url = get_authorize_callback('/connect/%s' % provider_id)
            
            ctx = dict(display_name=get_display_name(provider_id),
                       current_user=current_user,
                       callback_url=callback_url)
            
            current_app.logger.debug('Starting process of connecting '
                '%(display_name)s ccount to user account %(current_user)s. '
                'Callback URL = %(callback_url)s' % ctx)
            
            allow_view = current_app.config[CONNECT_ALLOW_REDIRECT_KEY]
            post_connect = request.form.get('next', allow_view)
            session[POST_OAUTH_CONNECT_SESSION_KEY] = post_connect
             
            return get_remote_app(provider_id).authorize(callback_url)
        
        @blueprint.route('/connect/<provider_id>', methods=['DELETE'])
        @login_required
        def remove_all_connections(provider_id):
            """Remove all connections for the authenticated user to the
            specified provider
            """
            display_name = get_display_name(provider_id)
            ctx = dict(provider=display_name,  user=current_user)
            
            try:
                method = connection_datastore.remove_all_connections
                method(current_user.get_id(), provider_id)
                
                current_app.logger.debug('Removed all connections to '
                                         '%(provider)s for %(user)s' % ctx)
                
                do_flash("All connections to %s removed" % display_name, 'info')
            except: 
                current_app.logger.error('Unable to remove all connections to '
                                         '%(provider)s for %(user)s' % ctx)
                
                msg = "Unable to remove connection to %(provider)s" % ctx
                do_flash(msg, 'error')
                
            return redirect(request.referrer)
            
        @blueprint.route('/connect/<provider_id>/<provider_user_id>', 
                         methods=['DELETE'])
        @login_required
        def remove_connection(provider_id, provider_user_id):
            """Remove a specific connection for the authenticated user to the
            specified provider
            """
            display_name = get_display_name(provider_id)
            ctx = dict(provider=display_name,  
                       user=current_user,
                       provider_user_id = provider_user_id)
            
            try:
                connection_datastore.remove_connection(current_user.get_id(), 
                    provider_id, provider_user_id)
                
                current_app.logger.debug('Removed connection to %(provider)s '
                    'account %(provider_user_id)s for %(user)s' % ctx)
                
                do_flash("Connection to %(provider)s removed" % ctx, 'info')
            except ConnectionNotFoundError:
                current_app.logger.error(
                    'Unable to remove connection to %(provider)s account '
                    '%(provider_user_id)s for %(user)s' % ctx)
                
                do_flash("Unabled to remove connection to %(provider)s" % ctx,
                      'error')
                
            return redirect(request.referrer)
        
        # Configure the URL handlers for each fo the configured providers
        for provider_config in provider_configs:
            _configure_provider(app, 
                                blueprint, 
                                app.oauth, 
                                provider_config)
            
        url_prefix = app.config[URL_PREFIX_KEY]
        app.register_blueprint(blueprint, url_prefix=url_prefix)
        

def do_flash(message, category):
    if current_app.config[FLASH_MESSAGES_KEY]:
        flash(message, category)
        
# Signals
social_connection_created = _signals.signal("connection-created")
social_login_failed = _signals.signal("login-failed")
