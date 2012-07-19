# -*- coding: utf-8 -*-
"""
    flask.ext.social.datastore
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains an abstracted social connection datastore.

    :copyright: (c) 2012 by Matt Wright.
    :license: MIT, see LICENSE for more details.
"""

from . import exceptions


class ConnectionDatastore(object):
    """Abstracted oauth connection datastore. Always extend this class and
    implement parent methods

    :param db: An instance of a configured databse manager from a Flask
               extension such as Flask-SQLAlchemy or Flask-MongoEngine"""

    def __init__(self, db, connection_model):
        self.db = db
        self.connection_model = connection_model

    def _do_get(self, rv):
        if rv is None:
            raise exceptions.ConnectionNotFoundError()
        return  rv

    def _save_model(self, model, **kwargs):
        raise NotImplementedError(
            "User datastore does not implement _save_model method")

    def remove_connection(self, user_id, provider_id, provider_user_id):
        """Remove a single connection to a provider for the specified user
        """
        raise NotImplementedError("Connection datastore does not implement "
                                  "'remove_connection' method")

    def remove_all_connections(self, user_id, provider_id):
        """Remove all connections to a provider for the specified user
        """
        raise NotImplementedError("Connection datastore does not implement "
                                  "'remove_all_connections' method")

    def _get_connection_by_provider_user_id(self,
                                            provider_id,
                                            provider_user_id):
        raise NotImplementedError("Connection datastore does not implement "
            "'_get_connection_by_provider_user_id' method")

    def get_connection_by_provider_user_id(self,
                                           provider_id,
                                           provider_user_id):
        """Find a connection to a provider for the specified provider user ID

        :param provider_id: the provider ID of which to find a connection to
        :param provider_user_id: the user ID associated with the user's account
                                 with the provider
        """
        return self._do_get(
            self._get_connection_by_provider_user_id(
                provider_id, provider_user_id))

    def _get_primary_connection(self, user_id, provider_id):
        raise NotImplementedError("Connection datastore does not implement "
                                  "'_get_primary_connection' method")

    def get_primary_connection(self, user_id, provider_id):
        """Get the first connection found for the specified provider to
        the currently logged in user.

        :param user_id: the user ID of a user of your application
        :param provider_id: the provider ID of which to find a connection to
        """
        return self._do_get(
            self._get_primary_connection(user_id, provider_id))

    def _get_connection(self, user_id, provider_id, provider_user_id):
        raise NotImplementedError("Connection datastore does not implement "
                                  "'_get_connection' method")

    def get_connection(self, user_id, provider_id, provider_user_id):
        """Get a specific connection for the specified user,  provider, and
        provider user

        :param user_id: the user ID of a user of your application
        :param provider_id: the provider ID of which to find a connection to
        :param provider_user_id: the user ID associated with the user's account
                                 with the provider
        """
        conn = self._get_connection(user_id, provider_id, provider_user_id)
        return self._do_get(conn)

    def save_connection(self, **kwargs):
        """Save a connection between a provider and a local user account

        :param user_id: The user ID of a user of your application
        :param provider_id: The provider ID of which to find a connection to
        :param provider_user_id: The user ID associated with the user's account
                                 with the provider
        :param access_token: The access token supplied by the provider after
                             the user has granted access to the application
        :param secret: The secret token supplied by the provider after the user
                       has granted access to the application. This is usually
                       only supplied by providers who implement OAuth 1.0
        :param display_name: The display name you wish to use locally to
                             represent the provider account. Generally speaking
                             this is set to the account's username.
        :param profile_url: The optional URL to the account's profile
        :param image_url: The optional URL of the account's profile image.
        :param rank: The optional rank value for the connection.
        """
        try:
            self.get_connection(kwargs['user_id'],
                                kwargs['provider_id'],
                                kwargs['provider_user_id'])
            raise exceptions.ConnectionExistsError()

        except exceptions.ConnectionNotFoundError:
            return self._save_model(self.connection_model(**kwargs))


class SQLAlchemyConnectionDatastore(ConnectionDatastore):
    """A SQLAlchemy datastore implementation for Flask-Social.
    Example usage::

        from flask import Flask
        from flask.ext.sqlalchemy import SQLAlchemy

        from flask.ext.social import Social
        from flask.ext.social.datastore import SQLAlchemyConnectionDatastore

        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'secret'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'your_db_uri'

        db = SQLAlchemy(app)
        Social(app, SQLAlchemyConnectionDatastore(db))
    """

    def _save_model(self, model):
        self.db.session.add(model)
        self.db.session.commit()
        return model

    def _delete_model(self, *models):
        for m in models:
            self.db.session.delete(m)
        self.db.session.commit()

    def remove_connection(self, user_id, provider_id, provider_user_id):
        conn = self.get_connection(user_id, provider_id, provider_user_id)
        self._delete_model(conn)

    def remove_all_connections(self, user_id, provider_id):
        self._delete_model(
            self.connection_model.query.filter_by(
                user_id=user_id,
                provider_id=provider_id))

    def _get_connection_by_provider_user_id(self,
                                            provider_id,
                                            provider_user_id):
        return self.connection_model.query.filter_by(
            provider_id=provider_id,
            provider_user_id=provider_user_id).first()

    def _get_primary_connection(self, user_id, provider_id):
        return self.connection_model.query.filter_by(
            user_id=user_id,
            provider_id=provider_id).order_by(
                self.connection_model.rank).first()

    def _get_connection(self, user_id, provider_id, provider_user_id):
        return self.connection_model.query.filter_by(
            user_id=user_id,
            provider_id=provider_id,
            provider_user_id=provider_user_id).first()


class MongoEngineConnectionDatastore(ConnectionDatastore):
    """A MongoEngine datastore implementation for Flask-Social.
    Example usage::

        from flask import Flask
        from flask.ext.mongoengine import MongoEngine
        from flask.ext.social import Social
        from flask.ext.social.datastore import MongoEngineConnectionDatastore

        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'secret'
        app.config['MONGODB_DB'] = 'flask_social_example'
        app.config['MONGODB_HOST'] = 'localhost'
        app.config['MONGODB_PORT'] = 27017

        db = MongoEngine(app)
        Social(app, MongoEngineConnectionDatastore(db))
    """

    def _save_model(self, model):
        model.save()
        return model

    def _delete_model(self, *models):
        for m in models:
            m.delete()

    def remove_connection(self, user_id, provider_id, provider_user_id):
        self._delete_model(
            self.get_connection(user_id, provider_id, provider_user_id))

    def remove_all_connections(self, user_id, provider_id):
        self._delete_model(
            self.connection_model.objects(
                user_id=user_id,
                provider_id=provider_id))

    def _get_connection_by_provider_user_id(self,
                                            provider_id,
                                            provider_user_id):
        return self.connection_model.objects(
            provider_id=provider_id,
            provider_user_id=provider_user_id).first()

    def _get_primary_connection(self, user_id, provider_id):
        return self.connection_model.objects(
            user_id=user_id,
            provider_id=provider_id).order_by('+rank').first()

    def _get_connection(self, user_id, provider_id, provider_user_id):
        return self.connection_model.objects(
            user_id=user_id,
            provider_id=provider_id,
            provider_user_id=provider_user_id).first()
