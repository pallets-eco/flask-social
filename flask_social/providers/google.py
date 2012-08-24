# -*- coding: utf-8 -*-
"""
    flask.ext.social.providers.google
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains the Flask-Social google code

    :copyright: (c) 2012 by Matt Wright.
    :license: MIT, see LICENSE for more details.
"""

from __future__ import absolute_import

import httplib2
import oauth2client.client as googleoauth
import apiclient.discovery as googleapi

from flask_social.core import ConnectionFactory, ConnectHandler, LoginHandler


default_config = {
    'id': 'google',
    'display_name': 'Google',
    'install': 'pip install google-api-python-client',
    'login_handler': 'flask.ext.social.providers.google::GoogleLoginHandler',
    'connect_handler': 'flask.ext.social.providers.google::GoogleConnectHandler',
    'connection_factory': 'flask.ext.social.providers.google::GoogleConnectionFactory',
    'oauth': {
        'base_url': 'https://www.google.com/accounts/',
        'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
        'access_token_url': 'https://accounts.google.com/o/oauth2/token',
        'access_token_method': 'POST',
        'access_token_params': {
            'grant_type': 'authorization_code'
        },
        'request_token_url': None,
        'request_token_params': {
            'response_type': 'code'
        },
    }
}


class GoogleConnectionFactory(ConnectionFactory):
    """The `GoogleConnectionFactory` class creates `Connection` instances for
    accounts connected to google. The API instance for google connections
    are instances of the `google library <http://code.google.com/p/google-api-python-client/>`_
    """
    def __init__(self, consumer_key, consumer_secret, **kwargs):
        super(GoogleConnectionFactory, self).__init__('google')
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

    def get_api(self, connection):
        credentials = googleoauth.AccessTokenCredentials(
            access_token=getattr(connection, 'access_token'),
            user_agent=''
        )

        http = httplib2.Http()
        http = credentials.authorize(http)
        return googleapi.build('plus', 'v1', http=http)


class GoogleLoginHandler(LoginHandler):
    """The `GoogleLoginHandler` class handles the authorization response from
    google. The google account's user ID is not passed in the response,
    thus it must be retrieved with an API call.
    """
    def __init__(self, **kwargs):
        super(GoogleLoginHandler, self).__init__('google',
                                                  kwargs.get('callback'))

    def get_provider_user_id(self, response):
        if response:
            credentials = googleoauth.AccessTokenCredentials(
                access_token=response['access_token'],
                user_agent=''
            )

            http = httplib2.Http()
            http = credentials.authorize(http)
            api = googleapi.build('plus', 'v1', http=http)
            profile = api.people().get(userId='me').execute()
            return profile['id']
        return None


class GoogleConnectHandler(ConnectHandler):
    """The `GoogleConnectHandler` class handles the connection procedure
    after a user authorizes a connection from google. The google acount's
    user ID is retrieved via an API call, otherwise the token is provided by
    the response from google.
    """
    def __init__(self, **kwargs):
        super(GoogleConnectHandler, self).__init__('google',
                                                   kwargs.get('callback'))

    def get_connection_values(self, response):
        if not response:
            return None

        access_token = response['access_token']

        credentials = googleoauth.AccessTokenCredentials(
            access_token=access_token,
            user_agent=''
        )

        http = httplib2.Http()
        http = credentials.authorize(http)
        api = googleapi.build('plus', 'v1', http=http)
        profile = api.people().get(userId='me').execute()

        return dict(
            provider_id=self.provider_id,
            provider_user_id=profile['id'],
            access_token=access_token,
            secret=None,
            display_name=profile['displayName'],
            profile_url=profile['url'],
            image_url=profile['image']['url']
        )
