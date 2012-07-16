
from flask import current_app, redirect
from flask.ext.security import current_user

from flask_social import exceptions
from flask_social.utils import get_display_name, do_flash, config_value


class Provider(object):
    def __init__(self, remote_app, connection_factory,
                 login_handler, connect_handler):
        self.remote_app = remote_app
        self.connection_factory = connection_factory
        self.login_handler = login_handler
        self.connect_handler = connect_handler

    def get_connection(self, *args, **kwargs):
        return self.connection_factory(*args, **kwargs)

    def login_handler(self, *args, **kwargs):
        return self.login_handler(*args, **kwargs)

    def connect_handler(self, *args, **kwargs):
        return self.connect_handler(*args, **kwargs)

    def tokengetter(self, *args, **kwargs):
        return self.remote_app.tokengetter(*args, **kwargs)

    def authorized_handler(self, *args, **kwargs):
        return self.remote_app.authorized_handler(*args, **kwargs)

    def authorize(self, *args, **kwargs):
        return self.remote_app.authorize(*args, **kwargs)

    def __str__(self):
        return '<Provider name=%s>' % self.remote_app.name


class ConnectionFactory(object):
    """The ConnectionFactory class creates `Connection` instances for the
    specified provider from values stored in the connection repository. This
    class should be extended whenever adding a new service provider to an
    application.
    """
    def __init__(self, provider_id):
        """Creates an instance of a `ConnectionFactory` for the specified
        provider

        :param provider_id: The provider ID
        """
        self.provider_id = provider_id

    def _get_current_user_primary_connection(self):
        return self._get_primary_connection(current_user.get_id())

    def _get_primary_connection(self, user_id):
        return current_app.social.datastore.get_primary_connection(
            user_id, self.provider_id)

    def _get_specific_connection(self, user_id, provider_user_id):
        return current_app.social.datastore.get_connection(user_id,
            self.provider_id, provider_user_id)

    def _create_api(self, connection):
        raise NotImplementedError("create_api method not implemented")

    def get_connection(self, user_id=None, provider_user_id=None):
        """Get a connection to the provider for the specified local user
        and the specified provider user

        :param user_id: The local user ID
        :param provider_user_id: The provider user ID
        """
        if user_id == None and provider_user_id == None:
            connection = self._get_current_user_primary_connection()
        if user_id != None and provider_user_id == None:
            connection = self._get_primary_connection(user_id)
        if user_id != None and provider_user_id != None:
            connection = self._get_specific_connection(user_id,
                                                       provider_user_id)

        def as_dict(model):
            rv = {}
            for key in ('user_id', 'provider_id', 'provider_user_id',
                        'access_token', 'secret', 'display_name',
                        'profile_url', 'image_url'):
                rv[key] = getattr(model, key)
            return rv

        return dict(api=self._create_api(connection),
                    **as_dict(connection))

    def __call__(self, **kwargs):
        try:
            return self.get_connection(**kwargs)
        except exceptions.ConnectionNotFoundError:
            return None


class OAuthHandler(object):
    """The `OAuthHandler` class is a base class for classes that handle OAuth
    interactions. See `LoginHandler` and `ConnectHandler`
    """
    def __init__(self, provider_id, callback=None):
        self.provider_id = provider_id
        self.callback = callback
        print callback


class LoginHandler(OAuthHandler):
    """ A `LoginHandler` handles the login procedure after receiving
    authorization from the service provider. The goal of a `LoginHandler` is
    to retrieve the user ID of the account that granted access to the local
    application. This ID is then used to find a connection within the local
    application to the provider. If a connection is found, the local user is
    retrieved from the user service and logged in autmoatically.
    """
    def get_provider_user_id(self, response):
        """Gets the provider user ID from the OAuth reponse.
        :param response: The OAuth response in the form of a dictionary
        """
        raise NotImplementedError("get_provider_user_id")

    def __call__(self, response):
        display_name = get_display_name(self.provider_id)

        current_app.logger.debug('Received login response from '
                                 '%s: %s' % (display_name, response))

        if response is None:
            do_flash("Access was denied to your %s "
                     "account" % display_name, 'error')

            return redirect(current_app.security.login_manager.login_view)

        uid = self.get_provider_user_id(response)

        return self.callback(self.provider_id, uid, response)


class ConnectHandler(OAuthHandler):
    """The `ConnectionHandler` class handles the connection procedure after
    receiving authorization from the service provider. The goal of a
    `ConnectHandler` is to retrieve the connection values that will be
    persisted by the connection service.
    """
    def get_connection_values(self, response):
        """Get the connection values to persist using values from the OAuth
        response

        :param response: The OAuth response as a dictionary of values
        """
        raise NotImplementedError("get_connection_values")

    def __call__(self, response, user_id=None):
        display_name = get_display_name(self.provider_id)

        current_app.logger.debug('Received connect response from '
                                 '%s. %s' % (display_name, response))

        if response is None:
            do_flash("Access was denied by %s" % display_name, 'error')
            return redirect(config_value('CONNECT_DENY_REDIRECT'))

        cv = self.get_connection_values(response)

        return self.callback(cv, user_id)
