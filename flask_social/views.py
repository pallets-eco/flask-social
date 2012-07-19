# -*- coding: utf-8 -*-
"""
    flask.ext.social.views
    ~~~~~~~~~~~~~~~~~~~~~~

    This module contains the Flask-Social views

    :copyright: (c) 2012 by Matt Wright.
    :license: MIT, see LICENSE for more details.
"""

from flask import Blueprint, current_app, redirect, request, session
from flask.ext.security import current_user, login_required
from flask.ext.security.utils import get_post_login_redirect
from flask.ext.security.views import _do_login as login_user
from werkzeug.local import LocalProxy

from flask_social import exceptions
from flask_social.signals import social_connection_removed, \
     social_connection_created, social_connection_failed, \
     social_login_completed, social_login_failed
from flask_social.utils import do_flash, config_value, get_display_name, \
     get_authorize_callback, get_remote_app


# Convenient references
_security = LocalProxy(lambda: current_app.extensions['security'])

_social = LocalProxy(lambda: current_app.extensions['social'])

_datastore = LocalProxy(lambda: _social.datastore)

_logger = LocalProxy(lambda: current_app.logger)


def login(provider_id):
    """Starts the provider login OAuth flow"""

    if current_user.is_authenticated():
        return redirect(request.referrer or '/')

    callback_url = get_authorize_callback('/login/%s' % provider_id)
    display_name = get_display_name(provider_id)

    _logger.debug('Starting login via %s account. Callback '
                  'URL = %s' % (display_name, callback_url))

    post_login = request.form.get('next', get_post_login_redirect())
    session['post_oauth_login_url'] = post_login

    return get_remote_app(provider_id).authorize(callback_url)


def login_handler(provider_id, provider_user_id, oauth_response):
    """Shared method to handle the signin process"""

    if current_user.is_authenticated():
        return redirect('/')

    display_name = get_display_name(provider_id)

    _logger.debug('Attempting login via %s with provider user '
                  '%s' % (display_name, provider_user_id))

    try:
        fn = _datastore.get_connection_by_provider_user_id
        connection = fn(provider_id, provider_user_id)

        user = _security.datastore.with_id(connection.user_id)

        if login_user(user):
            key = config_value('POST_OAUTH_LOGIN_SESSION_KEY')
            redirect_url = session.pop(key, get_post_login_redirect())

            _logger.debug('User logged in via %s. Redirecting to '
                          '%s' % (display_name, redirect_url))

            social_login_completed.send(current_app._get_current_object(),
                                        provider_id=provider_id, user=user)

            return redirect(redirect_url)

        else:
            _logger.info('Inactive local user attempted '
                         'login via %s.' % display_name)

            do_flash('Inactive user", "error')

    except exceptions.ConnectionNotFoundError:
        _logger.info('Login attempt via %s failed because '
                     'connection was not found.' % display_name)

        msg = '%s account not associated with an existing user' % display_name

        do_flash(msg, 'error')

    except Exception, e:
        _logger.error('Unexpected error signing in '
                      'via %s: %s' % (display_name, e))

    social_login_failed.send(current_app._get_current_object(),
                             provider_id=provider_id,
                             oauth_response=oauth_response)

    return redirect(_security.login_manager.login_view)


def connect(provider_id):
    """Starts the provider connection OAuth flow"""
    callback_url = get_authorize_callback('/connect/%s' % provider_id)

    ctx = dict(display_name=get_display_name(provider_id),
               current_user=current_user,
               callback_url=callback_url)

    _logger.debug('Starting process of connecting '
                  '%(display_name)s account to user account %(current_user)s. '
                  'Callback URL = %(callback_url)s' % ctx)

    allow_view = config_value('CONNECT_ALLOW_REDIRECT')
    pc = request.form.get('next', allow_view)
    session[config_value('POST_OAUTH_CONNECT_SESSION_KEY')] = pc

    return get_remote_app(provider_id).authorize(callback_url)


def connect_handler(cv, user_id=None):
    """Shared method to handle the connection process

    :param connection_values: A dictionary containing the connection values
    :param provider_id: The provider ID the connection shoudl be made to
    """
    provider_id = cv['provider_id']
    display_name = get_display_name(provider_id)
    cv['user_id'] = user_id or current_user.get_id()

    try:
        connection = _datastore.save_connection(**cv)

        _logger.debug('Connection to %s established '
                      'for %s' % (display_name, current_user))

        social_connection_created.send(current_app._get_current_object(),
                                       user=current_user._get_current_object(),
                                       connection=connection)

        do_flash('Connection established to %s' % display_name, 'success')

    except exceptions.ConnectionExistsError, e:
        _logger.debug('Connection to %s exists already '
                      'for %s' % (display_name, current_user))

        do_flash('A connection is already established with %s '
                 'to your account' % display_name, 'notice')

    except Exception, e:
        _logger.error('Unexpected error connecting %s account for '
                      'user. Reason: %s' % (display_name, e))

        social_connection_failed.send(current_app._get_current_object(),
                                      user=current_user._get_current_object(),
                                      error=e)

        do_flash('Could not make connection to %s. '
                 'Please try again later.' % display_name, 'error')

    redirect_url = session.pop(config_value('POST_OAUTH_CONNECT_SESSION_KEY'),
                               config_value('CONNECT_ALLOW_REDIRECT'))

    return redirect(redirect_url)


def remove_all_connections(provider_id):
    """Remove all connections for the authenticated user to the
    specified provider
    """
    display_name = get_display_name(provider_id)

    ctx = dict(provider=display_name, user=current_user)

    try:
        _datastore.remove_all_connections(current_user.get_id(), provider_id)

        social_connection_removed.send(current_app._get_current_object(),
                                       user=current_user._get_current_object(),
                                       provider_id=provider_id)

        _logger.debug('Removed all connections to '
                      '%(provider)s for %(user)s' % ctx)

        do_flash('All connections to %s removed' % display_name, 'info')

    except:
        _logger.error('Unable to remove all connections to '
                      '%(provider)s for %(user)s' % ctx)

        msg = 'Unable to remove connection to %(provider)s' % ctx

        do_flash(msg, 'error')

    return redirect(request.referrer)


def remove_connection(provider_id, provider_user_id):
    """Remove a specific connection for the authenticated user to the
    specified provider
    """
    display_name = get_display_name(provider_id)

    ctx = dict(provider=display_name,
               user=current_user,
               provider_user_id=provider_user_id)

    try:
        _datastore.remove_connection(current_user.get_id(),
                                     provider_id, provider_user_id)

        social_connection_removed.send(current_app._get_current_object(),
                                       user=current_user._get_current_object(),
                                       provider_id=provider_id)

        _logger.debug('Removed connection to %(provider)s '
                      'account %(provider_user_id)s for %(user)s' % ctx)

        do_flash('Connection to %(provider)s removed' % ctx, 'info')

    except exceptions.ConnectionNotFoundError:
        _logger.error('Unable to remove connection to %(provider)s account '
                      '%(provider_user_id)s for %(user)s' % ctx)

        do_flash('Unabled to remove connection to %(provider)s' % ctx, 'error')

    return redirect(request.referrer)


def create_blueprint(app, name, import_name, **kwargs):
    bp = Blueprint(name, import_name, **kwargs)

    bp.route('/login/<provider_id>',
             methods=['POST'])(login)

    bp.route('/connect/<provider_id>',
             methods=['POST'])(login_required(connect))

    bp.route('/connect/<provider_id>',
             methods=['DELETE'])(login_required(remove_all_connections))

    bp.route('/connect/<provider_id>/<provider_user_id>',
             methods=['DELETE'])(login_required(remove_connection))

    return bp
