# -*- coding: utf-8 -*-
"""
    flask.ext.social.providers.twitter
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains the Flask-Social twitter code

    :copyright: (c) 2012 by Matt Wright.
    :license: MIT, see LICENSE for more details.
"""

from __future__ import absolute_import

import twitter

from flask_social.core import ConnectionFactory, ConnectHandler, LoginHandler


default_config = {
    'id': 'twitter',
    'display_name': 'Twitter',
    'install': 'pip install python-twitter',
    'login_handler': 'flask.ext.social.providers.twitter::TwitterLoginHandler',
    'connect_handler': 'flask.ext.social.providers.twitter::TwitterConnectHandler',
    'connection_factory': 'flask.ext.social.providers.twitter::TwitterConnectionFactory',
    'oauth': {
        'base_url': 'http://api.twitter.com/1/',
        'request_token_url': 'https://api.twitter.com/oauth/request_token',
        'access_token_url': 'https://api.twitter.com/oauth/access_token',
        'authorize_url': 'https://api.twitter.com/oauth/authenticate',
    },
}


class TwitterConnectionFactory(ConnectionFactory):
    """The `TwitterConnectionFactory` class creates `Connection` instances for
    accounts connected to Twitter. The API instance for Twitter connections
    are instances of the `python-twitter library <http://code.google.com/p/python-twitter/>`_
    """
    def __init__(self, consumer_key, consumer_secret, **kwargs):
        super(TwitterConnectionFactory, self).__init__('twitter')
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

    def get_api(self, connection):
        return twitter.Api(consumer_key=self.consumer_key,
                           consumer_secret=self.consumer_secret,
                           access_token_key=getattr(connection, 'access_token'),
                           access_token_secret=getattr(connection, 'secret'))


class TwitterLoginHandler(LoginHandler):
    """The `TwitterLoginHandler` class handles the authorization response from
    Twitter. The Twitter account's user ID is passed with the authorization
    response and an extra API call is not necessary.
    """
    def __init__(self, **kwargs):
        super(TwitterLoginHandler, self).__init__('twitter',
                                                  kwargs.get('callback'))

    def get_provider_user_id(self, response):
        return response['user_id'] if response else None


class TwitterConnectHandler(ConnectHandler):
    """The `TwitterConnectHandler` class handles the connection procedure
    after a user authorizes a connection from Twitter. The connection values
    are all retrieved from the response, no extra API calls are necessary.
    """
    def __init__(self, **kwargs):
        super(TwitterConnectHandler, self).__init__('twitter',
                                                    kwargs.get('callback'))
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
            provider_id=self.provider_id,
            provider_user_id=str(user.id),
            access_token=response['oauth_token'],
            secret=response['oauth_token_secret'],
            display_name='@%s' % user.screen_name,
            profile_url="http://twitter.com/%s" % user.screen_name,
            image_url=user.profile_image_url
        )
