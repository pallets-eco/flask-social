Flask-Social
==============

.. module:: flask_social

Flask-Social provides OAuth provider login and APIs for your web application 
via Flask-Security and Flask-Oauth. 


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
    $ pip install https://github.com/mattupstate/flask-social/tarball/develop
    
Then install your datastore requirement. 

**SQLAlchemy**::

    $ pip install Flask-SQLAlchemy
    
**MongoEngine**::

    $ pip install https://github.com/sbook/flask-mongoengine/tarball/master
    
Then install your provider API libraries.

**Facebook**

    $ pip install http://github.com/pythonforfacebook/facebook-sdk/tarball/master
    
**Twitter**

    $ pip install python-twitter


.. _getting-started:

Getting Started
===============


        

.. _configuration:

Configuration Values
====================



.. _api:

API
===



Changelog
=========
.. toctree::
   :maxdepth: 2

   changelog