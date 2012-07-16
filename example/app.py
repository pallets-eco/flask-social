# a little trick so you can run:
# $ python example/app.py
# from the root of the security project
import os
import sys
sys.path.pop(0)
sys.path.insert(0, os.getcwd())

from flask import Flask, render_template, current_app, redirect
from flask.ext.mongoengine import MongoEngine
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, LoginForm, login_required, \
    current_user, UserMixin, RoleMixin
from flask.ext.security.datastore import SQLAlchemyUserDatastore, \
    MongoEngineUserDatastore
from flask.ext.social import Social
from flask.ext.social.datastore import SQLAlchemyConnectionDatastore, \
    MongoEngineConnectionDatastore
from werkzeug import url_decode


class HTTPMethodOverrideMiddleware(object):
    """The HTTPMethodOverrideMiddleware middleware implements the hidden HTTP
    method technique. Not all web browsers support every HTTP method, such as
    DELETE and PUT. Using a querystring parameter is the easiest implementation
    given Werkzeug and how middleware is implemented. The following is an
    example of how to create a form with a PUT method:

        <form action="/stuff/id?__METHOD__=PUT" method="POST">
            ...
        </form>
    """
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        if '__METHOD__' in environ.get('QUERY_STRING', ''):
            args = url_decode(environ['QUERY_STRING'])
            method = args.get('__METHOD__').upper()
            if method in ['GET', 'POST', 'PUT', 'DELETE']:
                method = method.encode('ascii', 'replace')
                environ['REQUEST_METHOD'] = method
        return self.app(environ, start_response)


def create_users():
    for u in  (('matt@lp.com', 'password'),):
        try:
            current_app.security.datastore.create_user(email=u[0], password=u[1])
        except Exception, e:
            print 'Errors: %s' % e
            raise


def populate_data():
    create_users()


def create_app(config, debug=True):
    app = Flask(__name__)
    app.debug = debug
    app.config['SECRET_KEY'] = 'secret'
    app.config['SECURITY_POST_LOGIN_VIEW'] = '/profile'

    try:
        from example.config import Config
        app.config.from_object(Config)
    except ImportError:
        print "Unable to load social configuration file. To run the example " \
              "application you'll need to create a file name `config.py` in " \
              "the example application folder. See the Flask-Social " \
              "documentation for more information"
        sys.exit()

    if config:
        for key, value in config.items():
            app.config[key] = value

    app.wsgi_app = HTTPMethodOverrideMiddleware(app.wsgi_app)

    @app.route('/')
    def index():
        return render_template('index.html', content='Home Page')

    @app.route('/login')
    def login():
        if current_user.is_authenticated():
            return redirect('/')

        return render_template(
            'login.html', content='Login Page', form=LoginForm())

    @app.route('/profile')
    @login_required
    def profile():
        return render_template(
            'profile.html',
            content='Profile Page',
            twitter_conn=current_app.social.twitter.get_connection(),
            facebook_conn=current_app.social.facebook.get_connection(),
            foursquare_conn=current_app.social.foursquare.get_connection())

    return app


def create_sqlalchemy_app(config=None, debug=True):
    app = create_app(config, debug)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost/flask_social_test'

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
        remember_token = db.Column(db.String(255))
        authentication_token = db.Column(db.String(255))
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

    return app


def create_mongoengine_app(auth_config=None, debug=True):
    app = create_app(auth_config, debug)
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
        user_id = db.StringField(max_length=255)
        provider_id = db.StringField(max_length=255)
        provider_user_id = db.StringField(max_length=255)
        access_token = db.StringField(max_length=255)
        secret = db.StringField(max_length=255)
        display_name = db.StringField(max_length=255)
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

    return app

if __name__ == '__main__':
    app = create_sqlalchemy_app()
    #app = create_mongoengine_app()
    app.run()
