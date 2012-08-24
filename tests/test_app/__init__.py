# -*- coding: utf-8 -*-

from flask import Flask, render_template, current_app
from flask.ext.security import login_required
from flask.ext.social.utils import get_remote_app
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
        current_app.security.datastore.create_user(email=u[0], password=u[1])
        current_app.security.datastore.commit()


def populate_data():
    create_users()


def create_app(config, debug=True):
    app = Flask(__name__)
    app.debug = debug
    app.config['SECRET_KEY'] = 'secret'
    app.config['SECURITY_POST_LOGIN_VIEW'] = '/profile'

    from tests.test_app.config import Config
    app.config.from_object(Config)

    if config:
        for key, value in config.items():
            app.config[key] = value

    app.wsgi_app = HTTPMethodOverrideMiddleware(app.wsgi_app)

    @app.route('/')
    def index():
        return render_template('index.html', content='Home Page')

    @app.route('/profile')
    @login_required
    def profile():
        return render_template(
            'profile.html',
            content='Profile Page',
            twitter_conn=get_remote_app('twitter').get_connection(),
            facebook_conn=get_remote_app('facebook').get_connection(),
            foursquare_conn=get_remote_app('foursquare').get_connection())

    return app
