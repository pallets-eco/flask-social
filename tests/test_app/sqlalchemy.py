# -*- coding: utf-8 -*-

import sys
import os

sys.path.pop(0)
sys.path.insert(0, os.getcwd())

from flask.ext.security import Security, UserMixin, RoleMixin, \
     SQLAlchemyUserDatastore
from flask.ext.social import Social, SQLAlchemyConnectionDatastore
from flask.ext.sqlalchemy import SQLAlchemy

from tests.test_app import create_app as create_base_app, populate_data


def create_app(config=None, debug=True):
    app = create_base_app(config, debug)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'

    db = SQLAlchemy(app)

    roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

    class Role(db.Model, RoleMixin):
        id = db.Column(db.Integer(), primary_key=True)
        name = db.Column(db.String(80), unique=True)
        description = db.Column(db.String(255))

    class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        email = db.Column(db.String(255), unique=True)
        password = db.Column(db.String(120))
        active = db.Column(db.Boolean())
        roles = db.relationship('Role', secondary=roles_users,
                    backref=db.backref('users', lazy='dynamic'))
        connections = db.relationship('Connection',
                    backref=db.backref('user', lazy='joined'))

    class Connection(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
        provider_id = db.Column(db.String(255))
        provider_user_id = db.Column(db.String(255))
        access_token = db.Column(db.String(255))
        secret = db.Column(db.String(255))
        display_name = db.Column(db.String(255))
        full_name = db.Column(db.String(255))
        profile_url = db.Column(db.String(512))
        image_url = db.Column(db.String(512))
        rank = db.Column(db.Integer)

    app.security = Security(app, SQLAlchemyUserDatastore(db, User, Role))
    app.social = Social(app, SQLAlchemyConnectionDatastore(db, Connection))

    @app.before_first_request
    def before_first_request():
        db.drop_all()
        db.create_all()
        populate_data()


    app.get_user = lambda: User.query.first()
    return app

if __name__ == '__main__':
    create_app().run()
