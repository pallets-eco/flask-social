Flask-Social
==============

.. module:: flask_social

Flask-Social is a Flask extension that aims to add simple OAuth provider 
integration for `Flask-Security <http://packages.python.org/Flask-Security/>`_. 
An example application is located at 
`http://flask-social-example.ep.io <http://flask-social-example.ep.io/>`_. 


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
    from flask.ext.social.datastore.sqlalchemy import SQLAlchemyConnectionDatastore
    
    # ... create the app ...
    
    app.config['SECURITY_POST_LOGIN'] = '/profile'
    
    db = SQLAlchemy(app)
    Security(app, SQLAlchemyUserDatastore(db))
    Social(app, SQLAlchemyConnectionDatastore(db))
    
Connecting to Providers
-----------------------

In order to let users connect their Facebook or Twitter accounts you'll want to 
add a mechanism on the profile page to do so. First the view method::

    @app.route('/profile')
    @login_required
    def profile():
        return render_template('profile.html', content='Profile Page',
                twitter_conn=current_app.social.twitter.get_connection(),
                facebook_conn=current_app.social.facebook.get_connection(),
                foursquare_conn=current_app.social.foursquare.get_connection())
                
You should notice the mechanism for retreiving the current user's connection 
with each service provider. If a connection is not found, the value will be 
`None`. Now lets take a look at the profile template::

    {% macro show_provider_button(provider_id, display_name, conn) %}
        {% if conn %}
        <form action="{{ url_for('social.remove_connection', provider_id=conn.provider_id, provider_user_id=conn.provider_user_id) }}" method="DELETE">
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

Logging In
----------

If a user has a connection established to a service provider then it is possible
for them to login via the provider. A login form would look like the following::

    <form action="{{ url_for('auth.authenticate') }}" method="POST" name="login_form">
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


.. _configuration:

Configuration Values
====================

* :attr:`SOCIAL_URL_PREFIX`: Specifies the URL prefix for the Social blueprint
* :attr:`SOCIAL_APP_URL`: The URL your application is registered under with a
  service provider.
* :attr:`SOCIAL_CONNECTION_DATASTORE`: Specifies the property name to use for 
  the connection datastore on the application instance
* :attr:`SOCIAL_CONNECT_ALLOW_REDIRECT`: The URL to redirect to after a user 
  successfully authorizes a connection with a service provider
* :attr:`SOCIAL_CONNECT_DENY_REDIRECT`: The URL to redirect to when a user 
  denies the connection request with a service provider
* :attr:`SOCIAL_FLASH_MESSAGES`: Specifies wether or not to flash messages 
  during connection and login requests


.. _api:

API
===

.. autoclass:: flask_social.Social
    :members:
    
Models
------
.. autoclass:: flask_social.Connection

    .. attribute:: user_id
    
       Local user ID
       
    .. attribute:: provider_id
    
       Provider ID which is a lowercase string of the provider name
       
    .. attribute:: provider_user_id
    
       The provider's user ID
       
    .. attribute:: access_token
    
       The access token from the provider received upon authorization 
       
    .. attribute:: secret
    
       The secret from the provider received upon authorization
       
    .. attribute:: display_name
    
       The display name or username of the provider's user
       
    .. attribute:: profile_url
    
       The URL of the user's profile at the provider
       
    .. attribute:: image_url
    
       The URL of the user's profile image
       
Factories
---------

.. autoclass:: flask_social.ConnectionFactory
    :members:
    
.. autoclass:: flask_social.FacebookConnectionFactory
    :members:
    
.. autoclass:: flask_social.TwitterConnectionFactory
    :members:

.. autoclass:: flask_social.FoursquareConnectionFactory
    :members:
    
OAuth Handlers
--------------

.. autoclass:: flask_social.LoginHandler
    :members:
    
.. autoclass:: flask_social.FacebookLoginHandler
    :members:
    
.. autoclass:: flask_social.TwitterLoginHandler
    :members:

.. autoclass:: flask_social.FoursquareLoginHandler
    :members:
    
.. autoclass:: flask_social.ConnectHandler
    :members:
    
.. autoclass:: flask_social.FacebookConnectHandler
    :members:
    
.. autoclass:: flask_social.TwitterConnectHandler
    :members:

.. autoclass:: flask_social.FoursquareConnectHandler
    :members:
    
Exceptions
----------    
.. autoexception:: flask_social.ConnectionExistsError

.. autoexception:: flask_social.ConnectionNotFoundError


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