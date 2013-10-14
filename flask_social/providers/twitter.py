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

config = {
    'id': 'twitter',
    'name': 'Twitter',
    'install': 'pip install python-twitter',
    'module': 'flask_social.providers.twitter',
    'base_url': 'http://api.twitter.com/1/',
    'request_token_url': 'https://api.twitter.com/oauth/request_token',
    'access_token_url': 'https://api.twitter.com/oauth/access_token',
    'authorize_url': 'https://api.twitter.com/oauth/authenticate'
}


def get_api(connection, **kwargs):
    return twitter.Api(consumer_key=kwargs.get('consumer_key'),
                       consumer_secret=kwargs.get('consumer_secret'),
                       access_token_key=connection.access_token,
                       access_token_secret=connection.secret)


def get_provider_user_id(response, **kwargs):
    return response['user_id'] if response else None


def get_connection_values(response=None, **kwargs):
    if not response:
        return None

    api = twitter.Api(consumer_key=kwargs.get('consumer_key'),
                      consumer_secret=kwargs.get('consumer_secret'),
                      access_token_key=response['oauth_token'],
                      access_token_secret=response['oauth_token_secret'])

    user = api.VerifyCredentials()

    return dict(
        provider_id=config['id'],
        provider_user_id=str(user.id),
        access_token=response['oauth_token'],
        secret=response['oauth_token_secret'],
        display_name='@%s' % user.screen_name,
        full_name = user.name,
        profile_url="http://twitter.com/%s" % user.screen_name,
        image_url=user.profile_image_url
    )
