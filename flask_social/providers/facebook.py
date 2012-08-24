# -*- coding: utf-8 -*-
"""
    flask.ext.social.providers.facebook
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains the Flask-Social facebook code

    :copyright: (c) 2012 by Matt Wright.
    :license: MIT, see LICENSE for more details.
"""

from __future__ import absolute_import

import facebook

from flask_social.core import ConnectionFactory, ConnectHandler, LoginHandler


default_config = {
    'id': 'facebook',
    'display_name': 'Facebook',
    'install': 'pip install http://github.com/pythonforfacebook/facebook-sdk/tarball/master',
    'login_handler': 'flask.ext.social.providers.facebook::FacebookLoginHandler',
    'connect_handler': 'flask.ext.social.providers.facebook::FacebookConnectHandler',
    'connection_factory': 'flask.ext.social.providers.facebook::FacebookConnectionFactory',
    'oauth': {
        'base_url': 'https://graph.facebook.com/',
        'request_token_url': None,
        'access_token_url': '/oauth/access_token',
        'authorize_url': 'https://www.facebook.com/dialog/oauth',
    },
}


class FacebookConnectionFactory(ConnectionFactory):
    """The `FacebookConnectionFactory` class creates `Connection` instances for
    accounts connected to Facebook. The API instance for Facebook connections
    are instances of the `Facebook Python libary <https://github.com/pythonforfacebook/facebook-sdk>`_.
    """
    def __init__(self, **kwargs):
        super(FacebookConnectionFactory, self).__init__('facebook')

    def get_api(self, connection):
        return facebook.GraphAPI(getattr(connection, 'access_token'))


class FacebookLoginHandler(LoginHandler):
    """The `FacebookLoginHandler` class handles the authorization response from
    Facebook. The Facebook account's user ID is not passed in the response,
    thus it must be retrieved with an API call.
    """
    def __init__(self, **kwargs):
        super(FacebookLoginHandler, self).__init__('facebook',
                                                  kwargs.get('callback'))

    def get_provider_user_id(self, response):
        if response:
            graph = facebook.GraphAPI(response['access_token'])
            profile = graph.get_object("me")
            return profile['id']
        return None


class FacebookConnectHandler(ConnectHandler):
    """The `FacebookConnectHandler` class handles the connection procedure
    after a user authorizes a connection from Facebook. The Facebook acount's
    user ID is retrieved via an API call, otherwise the token is provided by
    the response from Facebook.
    """
    def __init__(self, **kwargs):
        super(FacebookConnectHandler, self).__init__('facebook',
                                                     kwargs.get('callback'))

    def get_connection_values(self, response):
        if not response:
            return None

        access_token = response['access_token']
        graph = facebook.GraphAPI(access_token)
        profile = graph.get_object("me")
        profile_url = "http://facebook.com/profile.php?id=%s" % profile['id']
        image_url = "http://graph.facebook.com/%s/picture" % profile['id']

        return dict(
            provider_id=self.provider_id,
            provider_user_id=profile['id'],
            access_token=access_token,
            secret=None,
            display_name=profile['username'],
            profile_url=profile_url,
            image_url=image_url
        )
