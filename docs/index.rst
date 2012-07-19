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

Essentially, Flask-Social sets up endpoints for your app to make it easy for 
you to let your users connect and/or login using Facebook and Twitter. 
Flask-Social persists the connection information and allows you to get a 
configured instance of an API object with your user's token so you can make API 
calls on behalf of them. Currently Facebook and Twitter are supported out of 
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

    $ pip install https://github.com/sbook/flask-mongoengine/tarball/master
    
Then install your provider API libraries.

**Facebook**::

    $ pip install http://github.com/pythonforfacebook/facebook-sdk/tarball/master
    
**Twitter**::

    $ pip install python-twitter


.. _getting-started:

Getting Started
===============

If you plan on allowing your users to connect with Facebook or Twitter, the 
first thing you'll want to do is register an application with either service 
provider. To create an application with Facebook visit the 
`Facebook Developers <https://developers.facebook.com/>`_ page. To create an 
application with Twitter visit the 
`Twitter Developers <https://dev.twitter.com/>`_ page.

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
        'oauth': {
            'consumer_key': 'twitter consumer key',
            'consumer_secret': 'twitter consumer secret'
        }
    }
    
**Facebook**::
    
    app.config['SOCIAL_FACEBOOK'] = {
        'oauth': {
            'consumer_key': 'facebook app id',
            'consumer_secret': 'facebook app secret',
            'request_token_params': {
                'scope': 'email'
            }
        }
    }

**foursquare**::

    app.config['SOCIAL_FOURSQUARE'] = {
        'oauth': {
            'consumer_key': 'client id',
            'consumer_secret': 'client secret',
            'request_token_params': {
                'response_type': 'code'
            },
            'access_token_params': {
                'grant_type': 'authorization_code'
            }
        }
    }

Next you'll want to setup the `Social` extension and give it an instance of 
your datastore. In the following code the post login page is set to a 
hypothetical profile page instead of Flask-Security's default of the root 
index::

    # ... other required imports ...
    from flask.ext.social import Social
    from flask.ext.social.datastore import SQLAlchemyConnectionDatastore
    
    # ... create the app ...
    
    app.config['SECURITY_POST_LOGIN'] = '/profile'
    
    db = SQLAlchemy(app)

    # ... define user and role models ...

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

    Security(app, SQLAlchemyUserDatastore(db, User, Role))
    Social(app, SQLAlchemyConnectionDatastore(db, Connection))
    

Connecting to Providers
-----------------------

In order to let users connect their Facebook or Twitter accounts you'll want to 
add a mechanism on the profile page to do so. First the view method::

    @app.route('/profile')
    @login_required
    def profile():
        s = current_app.social
        
        return render_template(
            'profile.html', 
            content='Profile Page',
            twitter_conn=s.twitter.get_connection(),
            facebook_conn=s.facebook.get_connection(),
            foursquare_conn=s.foursquare.get_connection())
                
You should notice the mechanism for retreiving the current user's connection 
with each service provider. If a connection is not found, the value will be 
`None`. Now lets take a look at the profile template::

    {% macro show_provider_button(provider_id, display_name, conn) %}
        {% if conn %}
        <form action="{{ url_for('flask_social.remove_connection', provider_id=conn.provider_id, provider_user_id=conn.provider_user_id) }}" method="DELETE">
          <input type="submit" value="Disconnect {{ display_name }}" />
        </form>
        {% else %}
        <form action="{{ url_for('flask_social.connect', provider_id=provider_id) }}" method="POST">
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

Logging In
----------

If a user has a connection established to a service provider then it is possible
for them to login via the provider. A login form would look like the following::

    <form action="{{ url_for('flask_security.authenticate') }}" method="POST" name="login_form">
      {{ form.hidden_tag() }}
      {{ form.username.label }} {{ form.username }}<br/>
      {{ form.password.label }} {{ form.password }}<br/>
      {{ form.remember.label }} {{ form.remember }}<br/>
      {{ form.submit }}
    </form>
    
    {% macro social_login(provider_id, display_name) %}
      <form action="{{ url_for('flask_social.login', provider_id=provider_id) }}" method="POST">
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
    
       
Factories
---------

.. autoclass:: flask_social.core.ConnectionFactory
    :members:
    
.. autoclass:: flask_social.providers.facebook.FacebookConnectionFactory
    :members:
    
.. autoclass:: flask_social.providers.twitter.TwitterConnectionFactory
    :members:

.. autoclass:: flask_social.providers.foursquare.FoursquareConnectionFactory
    :members:

    
Login Handlers
--------------

.. autoclass:: flask_social.core.LoginHandler
    :members:
    
.. autoclass:: flask_social.providers.facebook.FacebookLoginHandler
    :members:
    
.. autoclass:: flask_social.providers.twitter.TwitterLoginHandler
    :members:

.. autoclass:: flask_social.providers.foursquare.FoursquareLoginHandler
    :members:


Connect Handlers
----------------
    
.. autoclass:: flask_social.core.ConnectHandler
    :members:
    
.. autoclass:: flask_social.providers.facebook.FacebookConnectHandler
    :members:
    
.. autoclass:: flask_social.providers.twitter.TwitterConnectHandler
    :members:

.. autoclass:: flask_social.providers.foursquare.FoursquareConnectHandler
    :members:


Exceptions
----------    
.. autoexception:: flask_social.exceptions.ConnectionExistsError

.. autoexception:: flask_social.exceptions.ConnectionNotFoundError


.. _signals:

Signals
-------

See the Flask documentation on signals for information on how to use these
signals in your code.

.. data:: social_connection_created

   Sent when a user successfully authorizes a connection with a service 
   provider. In addition to the app (which is the sender), it is passed `user`, 
   which is the local user and `connection` which is the connection that was 
   created
   
.. data:: social_login_failed

   Sent when a login attempt via a provider fails. In addition to the app 
   (which is the sender), it is passed `provider_id` which is the service 
   provider ID, and `oauth_response` which is the response returned by the
   provider


Changelog
=========

.. toctree::
   :maxdepth: 2

   changelog