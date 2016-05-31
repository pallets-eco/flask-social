# -*- coding: utf-8 -*-

import sys
import os

sys.path.pop(0)
sys.path.insert(0, os.getcwd())

from flask_mongoengine import MongoEngine
from flask_security import Security, UserMixin, RoleMixin, \
     MongoEngineUserDatastore
from flask_social import Social, MongoEngineConnectionDatastore

from tests.test_app import create_app as create_base_app, populate_data


def create_app(auth_config=None, debug=True):
    app = create_base_app(auth_config, debug)
    app.config['MONGODB_DB'] = 'flask_social_test'
    app.config['MONGODB_HOST'] = 'localhost'
    app.config['MONGODB_PORT'] = 27017

    db = MongoEngine(app)

    class Role(db.Document, RoleMixin):
        name = db.StringField(required=True, unique=True, max_length=80)
        description = db.StringField(max_length=255)

    class User(db.Document, UserMixin):
        email = db.StringField(unique=True, max_length=255)
        password = db.StringField(required=True, max_length=120)
        active = db.BooleanField(default=True)
        remember_token = db.StringField(max_length=255)
        authentication_token = db.StringField(max_length=255)
        roles = db.ListField(db.ReferenceField(Role), default=[])

        @property
        def connections(self):
            return Connection.objects(user_id=str(self.id))

    class Connection(db.Document):
        user_id = db.ObjectIdField()
        provider_id = db.StringField(max_length=255)
        provider_user_id = db.StringField(max_length=255)
        access_token = db.StringField(max_length=255)
        secret = db.StringField(max_length=255)
        display_name = db.StringField(max_length=255)
        full_name = db.StringField(max_length=255)
        profile_url = db.StringField(max_length=512)
        image_url = db.StringField(max_length=512)
        rank = db.IntField(default=1)

        @property
        def user(self):
            return User.objects(id=self.user_id).first()

    app.security = Security(app, MongoEngineUserDatastore(db, User, Role))
    app.social = Social(app, MongoEngineConnectionDatastore(db, Connection))

    @app.before_first_request
    def before_first_request():
        for m in [User, Role, Connection]:
            m.drop_collection()
        populate_data()

    app.get_user = lambda: User.objects().first()
    return app

if __name__ == '__main__':
    create_app().run()
