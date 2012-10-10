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

config = {
    'id': 'foursquare',
    'name': 'foursquare',
    'install': 'pip install foursquare',
    'module': 'flask.ext.social.providers.foursquare',
    'base_url': 'https://api.foursquare.com/v2/',
    'request_token_url': None,
    'access_token_url': 'https://foursquare.com/oauth2/access_token',
    'authorize_url': 'https://foursquare.com/oauth2/authenticate',
    'access_token_params': {
        'grant_type': 'authorization_code'
    },
    'request_token_params': {
        'response_type': 'code'
    }
}


def get_api(connection, **kwargs):
    return foursquare.Foursquare(
            access_token=getattr(connection, 'access_token'))


def get_provider_user_id(response, **kwargs):
    if response:
        api = foursquare.Foursquare(
            access_token=getattr(response, 'access_token'))
        return api.users()['user']['id']
    return None


def get_connection_values(response, **kwargs):
    if not response:
        return None

    access_token = response['access_token']
    api = foursquare.Foursquare(access_token=access_token)
    user = api.users()['user']
    profile_url = 'http://www.foursquare.com/user/' + user['id']
    image_url = user['photo']

    return dict(
        provider_id=config['id'],
        provider_user_id=user['id'],
        access_token=access_token,
        secret=None,
        display_name=profile_url.split('/')[-1:][0],
        profile_url=profile_url,
        image_url=image_url
    )
