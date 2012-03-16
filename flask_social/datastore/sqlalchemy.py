# -*- coding: utf-8 -*-
"""
    flask.ext.social.datastore.sqlalchemy
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains a Flask-Social SQLAlchemy datastore implementation

    :copyright: (c) 2012 by Matt Wright.
    :license: MIT, see LICENSE for more details.
"""

from flask.ext import social
from flask.ext.social.datastore import ConnectionDatastore

class SQLAlchemyConnectionDatastore(ConnectionDatastore):
    """A SQLAlchemy datastore implementation for Flask-Social. 
    Example usage:: 
    
        from flask import Flask
        from flask.ext.sqlalchemy import SQLAlchemy
        from flask.ext.social import Social
        from flask.ext.social.datastore.sqlalchemy import SQLAlchemyConnectionDatastore
        
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'secret'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/flask_social_example.sqlite'
        
        db = SQLAlchemy(app)
        Social(app, SQLAlchemyConnectionDatastore(db))
    """
    
    def get_models(self):
        db = self.db
        
        class Connection(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
            provider_id = db.Column(db.String(255))
            provider_user_id = db.Column(db.String(255))
            access_token = db.Column(db.String(255))
            secret = db.Column(db.String(255))
            display_name = db.Column(db.String(255))
            profile_url = db.Column(db.String(512))
            image_url = db.Column(db.String(512))
            rank = db.Column(db.Integer)
        
        return Connection
    
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
            social.SocialConnection.query.filter_by(
                user_id=user_id, 
                provider_id=provider_id))
    
    def _get_connection_by_provider_user_id(self, provider_id, provider_user_id):
        return social.SocialConnection.query.filter_by(
            provider_id=provider_id, 
            provider_user_id=provider_user_id).first()
            
    def _get_primary_connection(self, user_id, provider_id):
        return social.SocialConnection.query.filter_by(
            user_id=user_id,
            provider_id=provider_id).order_by(
                social.SocialConnection.rank).first()
        
    def _get_connection(self, user_id, provider_id, provider_user_id):
        return social.SocialConnection.query.filter_by(
            user_id=user_id, 
            provider_id=provider_id, 
            provider_user_id=provider_user_id).first()