# -*- coding: utf-8 -*-
"""
    flask.ext.social.views
    ~~~~~~~~~~~~~~~~~~~~~~

    This module contains the Flask-Social views

    :copyright: (c) 2012 by Matt Wright.
    :license: MIT, see LICENSE for more details.
"""

from flask import Blueprint, current_app, redirect, request, session, \
     after_this_request
from flask.ext.security import current_user, login_required
from flask.ext.security.utils import get_post_login_redirect, login_user, \
     get_url, anonymous_user_required, do_flash
from werkzeug.local import LocalProxy

from .signals import social_connection_removed, \
     social_connection_created, social_connection_failed, \
     social_login_completed, social_login_failed
from .utils import config_value, get_display_name, get_authorize_callback, \
     get_remote_app


# Convenient references
_security = LocalProxy(lambda: current_app.extensions['security'])

_social = LocalProxy(lambda: current_app.extensions['social'])

_datastore = LocalProxy(lambda: _social.datastore)

_logger = LocalProxy(lambda: current_app.logger)


def _commit(response=None):
    _datastore.commit()
    return response


@anonymous_user_required
def login(provider_id):
    """Starts the provider login OAuth flow"""

    callback_url = get_authorize_callback('login', provider_id)
    post_login = request.form.get('next', get_post_login_redirect())
    session['post_oauth_login_url'] = post_login
    remote_app = get_remote_app(provider_id)
    print remote_app
    return remote_app.authorize(callback_url)


@anonymous_user_required
def login_handler(**kwargs):
    """Shared method to handle the signin process"""

    provider_id = kwargs['provider_id']
    oauth_response = kwargs.pop('oauth_response')
    display_name = get_display_name(provider_id)
    connection = _datastore.find_connection(**kwargs)

    if connection:
        user = connection.user
        login_user(user)
        key = _social.post_oauth_login_session_key
        redirect_url = session.pop(key, get_post_login_redirect())

        social_login_completed.send(current_app._get_current_object(),
                                    provider_id=provider_id, user=user)

        return redirect(redirect_url)

    social_login_failed.send(current_app._get_current_object(),
                             provider_id=provider_id,
                             oauth_response=oauth_response)

    next = get_url(_security.login_manager.login_view)
    msg = '%s account not associated with an existing user' % display_name
    do_flash(msg, 'error')
    return redirect(next)


@login_required
def connect(provider_id):
    """Starts the provider connection OAuth flow"""
    callback_url = get_authorize_callback('connect', provider_id)
    allow_view = get_url(config_value('CONNECT_ALLOW_VIEW'))
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
    connection = _datastore.find_connection(**cv)

    if connection is None:
        after_this_request(_commit)
        connection = _datastore.create_connection(**cv)
        msg = ('Connection established to %s' % display_name, 'success')
        social_connection_created.send(current_app._get_current_object(),
                                       user=current_user._get_current_object(),
                                       connection=connection)
    else:
        msg = ('A connection is already established with %s '
               'to your account' % display_name, 'notice')
        social_connection_failed.send(current_app._get_current_object(),
                                      user=current_user._get_current_object())

    redirect_url = session.pop(config_value('POST_OAUTH_CONNECT_SESSION_KEY'),
                               get_url(config_value('CONNECT_ALLOW_VIEW')))

    do_flash(*msg)
    return redirect(redirect_url)

@login_required
def remove_all_connections(provider_id):
    """Remove all connections for the authenticated user to the
    specified provider
    """
    display_name = get_display_name(provider_id)
    ctx = dict(provider=display_name, user=current_user)

    deleted = _datastore.delete_connections(user_id=current_user.get_id(),
                                            provider_id=provider_id)
    if deleted:
        after_this_request(_commit)
        msg = ('All connections to %s removed' % display_name, 'info')
        social_connection_removed.send(current_app._get_current_object(),
                                       user=current_user._get_current_object(),
                                       provider_id=provider_id)
    else:
        msg = ('Unable to remove connection to %(provider)s' % ctx, 'error')

    do_flash(*msg)
    return redirect(request.referrer)


@login_required
def remove_connection(provider_id, provider_user_id):
    """Remove a specific connection for the authenticated user to the
    specified provider
    """
    display_name = get_display_name(provider_id)

    ctx = dict(provider=display_name, user=current_user,
               provider_user_id=provider_user_id)

    deleted = _datastore.delete_connection(user_id=current_user.get_id(),
                                           provider_id=provider_id,
                                           provider_user_id=provider_user_id)

    if deleted:
        after_this_request(_commit)
        msg = ('Connection to %(provider)s removed' % ctx, 'info')
        social_connection_removed.send(current_app._get_current_object(),
                                       user=current_user._get_current_object(),
                                       provider_id=provider_id)
    else:
        msg = ('Unabled to remove connection to %(provider)s' % ctx, 'error')

    do_flash(*msg)
    return redirect(request.referrer)


def configure_provider(provider, blueprint, oauth):
    """Configures and registers a service provider connection Factory with the
    main application.
    """
    provider_id = provider.id

    @blueprint.route('/connect/%s' % provider_id, methods=['GET'],
                     endpoint='connect_%s_callback' % provider_id)
    @login_required
    @provider.authorized_handler
    def connect_callback(response):
        """The route which the provider should redirect to after a user
        attempts to connect their account with the provider with their local
        application account
        """
        return provider.connect_handler(response)

    @blueprint.route('/login/%s' % provider_id, methods=['GET'],
                     endpoint='login_%s_callback' % provider_id)
    @provider.authorized_handler
    def login_callback(response):
        """The route which the provider should redirect to after a user
        attempts to login with their account with the provider
        """
        return provider.login_handler(response)


def create_blueprint(state, import_name):
    bp = Blueprint(state.blueprint_name, import_name,
                   url_prefix=state.url_prefix,
                   template_folder='templates')

    bp.route('/login/<provider_id>',
             methods=['POST'])(login)

    bp.route('/connect/<provider_id>',
             methods=['POST'])(connect)

    bp.route('/connect/<provider_id>',
             methods=['DELETE'])(remove_all_connections)

    bp.route('/connect/<provider_id>/<provider_user_id>',
             methods=['DELETE'])(remove_connection)

    for key, provider in state.providers.items():
        configure_provider(provider, bp, state.oauth)

    return bp
