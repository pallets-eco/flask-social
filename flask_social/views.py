
from flask import Blueprint, current_app, redirect, request, session
from flask.ext.security import current_user, login_required
from flask.ext.security.utils import get_post_login_redirect

from flask_social import exceptions
from flask_social.signals import social_connection_removed
from flask_social.utils import do_flash, config_value, get_display_name, \
     get_authorize_callback, get_remote_app


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


def connect(provider_id):
    """Starts the provider connection OAuth flow"""
    callback_url = get_authorize_callback('/connect/%s' % provider_id)

    ctx = dict(display_name=get_display_name(provider_id),
               current_user=current_user,
               callback_url=callback_url)

    current_app.logger.debug('Starting process of connecting '
        '%(display_name)s account to user account %(current_user)s. '
        'Callback URL = %(callback_url)s' % ctx)

    allow_view = config_value('CONNECT_ALLOW_REDIRECT')
    pc = request.form.get('next', allow_view)
    session[config_value('POST_OAUTH_CONNECT_SESSION_KEY')] = pc

    return get_remote_app(provider_id).authorize(callback_url)


def remove_all_connections(provider_id):
    """Remove all connections for the authenticated user to the
    specified provider
    """
    display_name = get_display_name(provider_id)
    ctx = dict(provider=display_name, user=current_user)

    try:
        current_app.social.datastore.remove_all_connections(
            current_user.get_id(), provider_id)

        social_connection_removed.send(
            current_app._get_current_object(),
            user=current_user._get_current_object(),
            provider_id=provider_id)

        current_app.logger.debug('Removed all connections to '
                                 '%(provider)s for %(user)s' % ctx)

        do_flash("All connections to %s removed" % display_name, 'info')
    except:
        current_app.logger.error('Unable to remove all connections to '
                                 '%(provider)s for %(user)s' % ctx)

        msg = "Unable to remove connection to %(provider)s" % ctx
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
        current_app.social.datastore.remove_connection(
            current_user.get_id(),
            provider_id,
            provider_user_id)

        social_connection_removed.send(
            current_app._get_current_object(),
            user=current_user._get_current_object(),
            provider_id=provider_id)

        current_app.logger.debug('Removed connection to %(provider)s '
            'account %(provider_user_id)s for %(user)s' % ctx)

        do_flash("Connection to %(provider)s removed" % ctx, 'info')

    except exceptions.ConnectionNotFoundError:
        current_app.logger.error(
            'Unable to remove connection to %(provider)s account '
            '%(provider_user_id)s for %(user)s' % ctx)

        do_flash("Unabled to remove connection to %(provider)s" % ctx,
              'error')

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
