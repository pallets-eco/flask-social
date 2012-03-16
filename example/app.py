# a little trick so you can run:
# $ python example/app.py 
# from the root of the security project
import sys, os
sys.path.pop(0)
sys.path.insert(0, os.getcwd())

from flask import Flask, render_template, current_app, redirect

from flask.ext.mongoengine import MongoEngine
from flask.ext.sqlalchemy import SQLAlchemy

from flask.ext.security import (Security, LoginForm, user_datastore, 
                                login_required, current_user)

from flask.ext.security.datastore.mongoengine import MongoEngineUserDatastore
from flask.ext.security.datastore.sqlalchemy import SQLAlchemyUserDatastore

from flask.ext.social import Social
from flask.ext.social.datastore.sqlalchemy import SQLAlchemyConnectionDatastore
from flask.ext.social.datastore.mongoengine import MongoEngineConnectionDatastore

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
    for u in  (('matt','matt@lp.com','password'),):
        user_datastore.create_user(
            username=u[0], email=u[1], password=u[2])

def populate_data():
    create_users()
    
def create_app(config):
    app = Flask(__name__)
    app.debug = True
    app.config['SECRET_KEY'] = 'secret'
    app.config['SECURITY_POST_LOGIN'] = '/profile'
    
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
        
        return render_template('login.html', content='Login Page', form=LoginForm())
    
    @app.route('/profile')
    @login_required
    def profile():
        return render_template('profile.html', content='Profile Page',
                twitter_conn=current_app.social.twitter.get_connection(),
                facebook_conn=current_app.social.facebook.get_connection())
    
    return app

def create_sqlalchemy_app(config=None):
    print 'create_sqlalchemy_app'
    app = create_app(config)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/flask_social_example.sqlite'
    
    db = SQLAlchemy(app)
    Security(app, SQLAlchemyUserDatastore(db))
    Social(app, SQLAlchemyConnectionDatastore(db))
    
    @app.before_first_request
    def before_first_request():
        db.drop_all()
        db.create_all()
        populate_data()
        
    return app

def create_mongoengine_app(auth_config=None):
    app = create_app(auth_config)
    app.config['MONGODB_DB'] = 'flask_social_example'
    app.config['MONGODB_HOST'] = 'localhost'
    app.config['MONGODB_PORT'] = 27017
    
    db = MongoEngine(app)
    Security(app, MongoEngineUserDatastore(db))
    Social(app, MongoEngineConnectionDatastore(db))
    
    @app.before_first_request
    def before_first_request():
        from flask.ext.security import User, Role
        from flask.ext.social import SocialConnection
        User.drop_collection()
        Role.drop_collection()
        SocialConnection.drop_collection()
        populate_data()
        
    return app

if __name__ == '__main__':
    app = create_sqlalchemy_app()
    #app = create_mongoengine_app()
    app.run()