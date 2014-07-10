# -*- coding: utf-8 -*-
"""
    flask.ext.social.providers.vk
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains the Flask-Social vkontakte code

    :copyright: (c) 2014 by Sergey Nuzhdin.
    :license: MIT, see LICENSE for more details.
"""

from __future__ import absolute_import

import vkontakte

config = {
    'id': 'vk',
    'name': 'VK',
    'install': 'pip install vkontakte',
    'module': 'flask_social.providers.vk',
    'base_url': 'https://api.vk.com/method/',
    'request_token_url': None,
    'access_token_url': 'https://oauth.vk.com/access_token',
    'authorize_url': 'https://oauth.vk.com/authorize',
}


def get_api(connection, **kwargs):
    return vkontakte.API(
        api_id=kwargs.get('consumer_key'),
        api_secret=kwargs.get('consumer_secret')
    )


def get_provider_user_id(response, **kwargs):
    return str(response['user_id']) if response else None


def get_connection_values(response, **kwargs):
    if not response:
        return None

    access_token = response['access_token']
    vk = vkontakte.API(token=access_token)
    profile = vk.getProfiles(
        uids=response['user_id'],
        fields='first_name,last_name,photo_100,screen_name')[0]

    profile_url = "http://vk.com/id%s" % response['user_id']
    fullname = u'%s %s' % (profile['first_name'], profile['last_name'])
    return dict(
        provider_id=config['id'],
        provider_user_id=str(profile['uid']),
        access_token=access_token,
        secret=None,
        display_name=profile.get('screen_name', fullname),
        full_name=fullname,
        profile_url=profile_url,
        image_url=profile.get('photo_100'),
        email='',
    )


def get_token_pair_from_response(response):
    return dict(
        access_token=response.get('access_token', None),
        secret=None,
    )
