# -*- coding: utf-8 -*-

import sys
import os

sys.path.pop(0)
sys.path.insert(0, os.getcwd())

from flask_peewee.db import Database
from flask.ext.security import Security, UserMixin, RoleMixin, \
    PeeweeUserDatastore
from flask.ext.social import Social, PeeweeConnectionDatastore
from peewee import *

from tests.test_app import create_app as create_base_app, populate_data


def create_app(config=None, debug=True):
    app = create_base_app(config, debug)
    app.config['DATABASE'] = {
        'name': 'example2.db',
        'engine': 'peewee.SqliteDatabase',
    }

    db = Database(app)

    class Role(db.Model, RoleMixin):
        name = TextField(unique=True)
        description = TextField(null=True)

    class User(db.Model, UserMixin):
        email = TextField()
        password = TextField()
        last_login_at = DateTimeField(null=True)
        current_login_at = DateTimeField(null=True)
        last_login_ip = TextField(null=True)
        current_login_ip = TextField(null=True)
        login_count = IntegerField(null=True)
        active = BooleanField(default=True)
        confirmed_at = DateTimeField(null=True)

    class UserRoles(db.Model):
        """ Peewee does not have built-in many-to-many support, so we have to
        create this mapping class to link users to roles."""
        user = ForeignKeyField(User, related_name='roles')
        role = ForeignKeyField(Role, related_name='users')
        name = property(lambda self: self.role.name)
        description = property(lambda self: self.role.description)

    class Connection(db.Model):
        user = ForeignKeyField(User, related_name='connections')
        provider_id = TextField()
        provider_user_id = TextField()
        access_token = TextField()
        secret = TextField(null=True)
        display_name = TextField()
        full_name = TextField()
        profile_url = TextField()
        image_url = TextField()
        rank = IntegerField(null=True)

    app.security = Security(app, PeeweeUserDatastore(db, User, Role, UserRoles))
    app.social = Social(app, PeeweeConnectionDatastore(db, Connection))

    @app.before_first_request
    def before_first_request():
        for Model in (Role, User, UserRoles, Connection):
            Model.drop_table(fail_silently=True)
            Model.create_table(fail_silently=True)
        populate_data()

    app.get_user = lambda: User.select().get()

    return app

if __name__ == '__main__':
    create_app().run()
