# -*- coding: utf-8 -*-
"""
    flask.ext.social.providers.foursquare
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains the Flask-Social foursquare code

    :copyright: (c) 2012 by Matt Wright.
    :license: MIT, see LICENSE for more details.
"""

from __future__ import absolute_import

import foursquare

from flask_social.core import ConnectionFactory, ConnectHandler, LoginHandler


default_config = {
    'id': 'foursquare',
    'display_name': 'foursquare',
    'install': 'pip install foursquare',
    'login_handler': 'flask.ext.social.providers.foursquare::FoursquareLoginHandler',
    'connect_handler': 'flask.ext.social.providers.foursquare::FoursquareConnectHandler',
    'connection_factory': 'flask.ext.social.providers.foursquare::FoursquareConnectionFactory',
    'oauth': {
        'base_url': 'https://api.foursquare.com/v2/',
        'request_token_url': None,
        'access_token_url': 'https://foursquare.com/oauth2/access_token',
        'authorize_url': 'https://foursquare.com/oauth2/authenticate',
        'access_token_params': {
            'grant_type': 'authorization_code'
        },
        'request_token_params': {
            'response_type': 'code'
        },
    }
}


class FoursquareConnectionFactory(ConnectionFactory):
    """The `FoursquareConnectionFactory` class creates `Connection` instances for
    accounts connected to foursquare. The API instance for foursquare connections
    are instances of the `foursquare library <https://github.com/mLewisLogic/foursquare/>`_
    """
    def __init__(self, consumer_key, consumer_secret, **kwargs):
        super(FoursquareConnectionFactory, self).__init__('foursquare')
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

    def get_api(self, connection):
        return foursquare.Foursquare(
                access_token=getattr(connection, 'access_token'))


class FoursquareLoginHandler(LoginHandler):
    """The `FoursquareLoginHandler` class handles the authorization response from
    foursquare. The foursquare account's user ID is not passed in the response,
    thus it must be retrieved with an API call.
    """
    def __init__(self, **kwargs):
        super(FoursquareLoginHandler, self).__init__('foursquare',
                                                  kwargs.get('callback'))

    def get_provider_user_id(self, response):
        if response:
            api = foursquare.Foursquare(
                access_token=getattr(response, 'access_token'))
            return api.users()['user']['id']
        return None


class FoursquareConnectHandler(ConnectHandler):
    """The `FoursquareConnectHandler` class handles the connection procedure
    after a user authorizes a connection from foursquare. The foursquare acount's
    user ID is retrieved via an API call, otherwise the token is provided by
    the response from foursquare.
    """
    def __init__(self, **kwargs):
        super(FoursquareConnectHandler, self).__init__('foursquare',
                                                       kwargs.get('callback'))

    def get_connection_values(self, response):
        if not response:
            return None

        access_token = response['access_token']
        api = foursquare.Foursquare(access_token=access_token)
        user = api.users()['user']
        profile_url = user['canonicalUrl']
        image_url = user['photo']

        return dict(
            provider_id=self.provider_id,
            provider_user_id=user['id'],
            access_token=access_token,
            secret=None,
            display_name=profile_url.split('/')[-1:][0],
            profile_url=profile_url,
            image_url=image_url
        )
