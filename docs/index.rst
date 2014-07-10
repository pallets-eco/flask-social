.. include:: ../README.rst


Contents
=========
* :ref:`overview`
* :ref:`installation`
* :ref:`getting-started`
* :ref:`api`
* :doc:`Changelog </changelog>`


.. _overview:

Overview
========

Flask-Social sets up endpoints for your app to make it easy for you to let your
users connect and/or login using Facebook and Twitter. Flask-Social persists
the connection information and allows you to get a configured instance of an
API object with your user's token so you can make API calls on behalf of them.
Currently Facebook, Twitter, foursquare and Google are supported out of
the box as long as you install the appropriate API library.


.. _installation:

Installation
============

First, install Flask-Social::

    $ mkvirtualenv app-name
    $ pip install Flask-Social

Then install your datastore requirement.

**SQLAlchemy**::

    $ pip install Flask-SQLAlchemy

**MongoEngine**::

    $ pip install flask-mongoengine

Then install your provider API libraries.

**Facebook**::

    $ pip install facebook-sdk

**Twitter**::

    $ pip install python-twitter

**foursquare**::

    $ pip install foursquare


**Google**::

    $ pip install oauth2client google-api-python-client


.. _getting-started:

Getting Started
===============

If you plan on allowing your users to connect with Facebook or Twitter, the
first thing you'll want to do is register an application with either service
provider:

* `Facebook <https://developers.facebook.com/>`_
* `Twitter <https://dev.twitter.com/>`_
* `foursquare <https://developer.foursquare.com/>`_

Bear in mind that Flask-Social requires Flask-Security. It would be a good idea
to review the documentation for Flask-Security before moving on here as it
assumes you have knowledge and a working Flask-Security app already.

Configuration
-------------

After you register your application(s) you'll need to configure your Flask app
with the consumer key and secret. When dealing with Facebook, the consumer key
is also referred to as the App ID/API Key. The following is an example of how
to configure your application with your provider's application values

**Twitter**::

    app.config['SOCIAL_TWITTER'] = {
        'consumer_key': 'twitter consumer key',
        'consumer_secret': 'twitter consumer secret'
    }

**Facebook**::

    app.config['SOCIAL_FACEBOOK'] = {
        'consumer_key': 'facebook app id',
        'consumer_secret': 'facebook app secret'
    }

**foursquare**::

    app.config['SOCIAL_FOURSQUARE'] = {
        'consumer_key': 'client id',
        'consumer_secret': 'client secret'
    }

**Google**::

    app.config['SOCIAL_GOOGLE'] = {
        'consumer_key': 'xxxx',
        'consumer_secret': 'xxxx'
    }

Next you'll want to setup the `Social` extension and give it an instance of
your datastore. In the following code the post login page is set to a
hypothetical profile page instead of Flask-Security's default of the root
index::

    # ... other required imports ...
    from flask.ext.social import Social
    from flask.ext.social.datastore import SQLAlchemyConnectionDatastore

    # ... create the app ...

    app.config['SECURITY_POST_LOGIN_VIEW'] = '/profile'

    db = SQLAlchemy(app)

    # ... define user and role models ...

    class Connection(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        user = db.relationship('user')
        full_name = db.Column(db.String(255))
        provider_id = db.Column(db.String(255))
        provider_user_id = db.Column(db.String(255))
        access_token = db.Column(db.String(255))
        secret = db.Column(db.String(255))
        display_name = db.Column(db.String(255))
        email = db.Column(db.String(255))
        profile_url = db.Column(db.String(512))
        image_url = db.Column(db.String(512))
        rank = db.Column(db.Integer)

    Security(app, SQLAlchemyUserDatastore(db, User, Role))
    Social(app, SQLAlchemyConnectionDatastore(db, Connection))

If you do not want the same OAuth account to be connected to more than one user account, 
add the following to the Connection database model:

    __table_args__ = (db.UniqueConstraint('provider_id', 'provider_user_id', name='_providerid_userid_uc'), {})

This will ensure that every row in the Connection table has a unique provider_id and 
provider_user_id pair. This means that any given Twitter account can only be connected 
once.


Connecting to Providers
-----------------------

In order to let users connect their Facebook or Twitter accounts you'll want to
add a mechanism on the profile page to do so. First the view method::

    @app.route('/profile')
    @login_required
    def profile():
        return render_template(
            'profile.html',
            content='Profile Page',
            twitter_conn=social.twitter.get_connection(),
            facebook_conn=social.facebook.get_connection(),
            foursquare_conn=social.foursquare.get_connection())

You should notice the mechanism for retreiving the current user's connection
with each service provider. If a connection is not found, the value will be
`None`. 

Now lets take a look at the profile template::

    {% macro show_provider_button(provider_id, display_name, conn) %}
        {% if conn %}
        <form action="{{ url_for('social.remove_connection', provider_id=conn.provider_id, provider_user_id=conn.provider_user_id) }}?__METHOD_OVERRIDE__=DELETE" method="POST">
          <input type="submit" value="Disconnect {{ display_name }}" />
        </form>
        {% else %}
        <form action="{{ url_for('social.connect', provider_id=provider_id) }}" method="POST">
          <input type="submit" value="Connect {{ display_name }}" />
        </form>
        {% endif %}
    {% endmacro %}

    {{ show_provider_button('twitter', 'Twitter', twitter_conn) }}

    {{ show_provider_button('facebook', 'Facebook', facebook_conn) }}

    {{ show_provider_button('foursquare', 'foursquare', foursquare_conn) }}

In the above template code a form is displayed depending on if a connection for
the current user exists or not. If the connection exists a disconnect button is
displayed and if it doesn't exist a connect button is displayed. Clicking the
connect button will initiate the OAuth flow with the given provider, allowing
the user to authorize the application and return a token and/or secret to be
used when configuring an API instance.

However, notice that the first form for removing social connections uses HTTP method
tunneling, since HTML forms only support POST and GET. We tunnel by passing a query
string parameter called __METHOD_OVERRIDE__ and set its value to DELETE. Ideally, we 
can handle this via a piece of middleware::

    from werkzeug import url_decode

    # Taken from https://github.com/mattupstate/flask-social-example/blob/master/app/middleware.py
    class MethodRewriteMiddleware(object):
        ''' Middleware that will allow the passing of METHOD_OVERRIDE to a url
        for HTTP verbs that cannot be done via <form>, like DELETE. '''
        def __init__(self, app):
            self.app = app

        def __call__(self, environ, start_response):
            if 'METHOD_OVERRIDE' in environ.get('QUERY_STRING', ''):
                args = url_decode(environ['QUERY_STRING'])
                method = args.get('__METHOD_OVERRIDE__')
                if method:
                    method = method.encode('ascii', 'replace')
                    environ['REQUEST_METHOD'] = method
            return self.app(environ, start_response)

    app.wsgi_app = MethodRewriteMiddleware(app.wsgi_app)

The middleware will now look for "METHOD_OVERRIDE" in the query string and if it's 
found, update the REQUEST_METHOD environment variable.

Logging In
----------

If a user has a connection established to a service provider then it is possible
for them to login via the provider. A login form would look like the following::

    <form action="{{ url_for('security.authenticate') }}" method="POST" name="login_form">
      {{ form.hidden_tag() }}
      {{ form.username.label }} {{ form.username }}<br/>
      {{ form.password.label }} {{ form.password }}<br/>
      {{ form.remember.label }} {{ form.remember }}<br/>
      {{ form.submit }}
    </form>

    {% macro social_login(provider_id, display_name) %}
      <form action="{{ url_for('social.login', provider_id=provider_id) }}" method="POST">
        <input type="submit" value="Login with {{ display_name }}" />
      </form>
    {% endmacro %}

    {{ social_login('twitter', 'Twitter' )}}

    {{ social_login('facebook', 'Facebook' )}}

    {{ social_login('foursquare', 'foursquare' )}}

In the above template code you'll notice the regular username and password login
form and forms for the user to login via Twitter, Facebook, and foursquare. If
the user has an existing connection with the provider they will automatically be
logged in without having to enter their username or password.


Provider API's
--------------

Flask Social is opinionated and uses available Python libraries when possible
to interact with the API's of the stock providers. This means that you'll need
to install the appropriate library for this functionality to work.

Configured instances of an API client are available via the `get_api` method
of the provider instance. For example, lets say you wany to post the current
user's Twitter feed::

    social = Social(...)

    @app.route('/profile')
    def profile():
        twitter_api = social.twitter.get_api()
        twitter_api.PostUpdate('hello from my Flask app!')


.. _configuration:

Configuration Values
====================

* :attr:`SOCIAL_URL_PREFIX`: Specifies the URL prefix for the Social blueprint.
* :attr:`SOCIAL_APP_URL`: The URL your application is registered under with a
  service provider.
* :attr:`SOCIAL_CONNECT_ALLOW_REDIRECT`: The URL to redirect to after a user
  successfully authorizes a connection with a service provider.
* :attr:`SOCIAL_CONNECT_DENY_REDIRECT`: The URL to redirect to when a user
  denies the connection request with a service provider.
* :attr:`SOCIAL_FLASH_MESSAGES`: Specifies wether or not to flash messages
  during connection and login requests.
* :attr:`SOCIAL_POST_OAUTH_CONNECT_SESSION_KEY`: Specifies the session key to
  use when looking for a redirect value after a connection is made.
* :attr:`SOCIAL_POST_OAUTH_LOGIN_SESSION_KEY`: Specifis the session key to use
  when looking for a redirect value after a login is completed.


.. _api:

API
===

.. autoclass:: flask_social.core.Social
    :members:


.. _signals:

Signals
-------

See the Flask documentation on signals for information on how to use these
signals in your code.

.. data:: connection_created

   Sent when a user successfully authorizes a connection with a provider
   provider. In addition to the app (which is the sender), it is passed `user`,
   which is the current user and `connection` which is the connection that was
   created

.. data:: connection_failed

    Sent when a user attempts to authorize a connection with a provider but
    it fails because it already exists. In addition to the app (which is the
    sender), it is passed `user`, which is the current user

.. data:: connection_removed

    Sent when a user removes a connection to a provider. In addition to the app
    (which is the sender), it is passed `user`, which is the current user and
    `provider_id` which is the ID of the provider that was removed

.. data:: login_failed

   Sent when a login attempt via a provider fails. In addition to the app
   (which is the sender), it is passed `provider` which is the service
   provider, and `oauth_response` which is the response returned by the
   provider

.. data:: login_completed

   Sent when a login attempt via a provider fails. In addition to the app
   (which is the sender), it is passed `provider` which is the service
   provider, and `user` which is the current user


Changelog
=========

.. toctree::
   :maxdepth: 2

   changelog
