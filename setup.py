"""
Flask-Social
--------------

Simple OAuth provider integration for Flask-Security.

Links
`````

* `development version
  <https://github.com/mattupstate/flask-social/raw/develop#egg=Flask-Social-dev>`_

"""
from setuptools import setup

setup(
    name='Flask-Social',
    version='1.0.0',
    url='https://github.com/mattupstate/flask-social',
    license='MIT',
    author='Matthew Wright',
    author_email='matt@nobien.net',
    description='Simple OAuth provider integration for Flask-Security',
    long_description=__doc__,
    packages=[
        'flask_social',
        'flask_social.datastore'
    ],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask-Security',
        'Flask-Oauth'
    ],
    test_suite='nose.collector',
    tests_require=[
        'nose',
        'Flask-Testing',
        'Flask-SQLAlchemy',
        'Flask-MongoEngine'
    ],
    dependency_links=[
        'http://github.com/sbook/flask-mongoengine/tarball/master#egg=Flask-MongoEngine-0.1.3-dev'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
