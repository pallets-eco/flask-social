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
    version='1.1.0-dev',
    url='https://github.com/mattupstate/flask-social',
    license='MIT',
    author='Matthew Wright',
    author_email='matt@nobien.net',
    description='Simple OAuth provider integration for Flask-Security',
    long_description=__doc__,
    packages=[
        'flask_social'
    ],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask-Security==1.3.0-dev',
        'Flask-OAuth==0.12-dev'
    ],
    test_suite='nose.collector',
    tests_require=[
        'nose',
        'Flask-Testing',
        'Flask-SQLAlchemy',
        'Flask-MongoEngine'
    ],
    dependency_links=[
        'http://github.com/mattupstate/flask-security/tarball/master#egg=Flask-Security-1.3.0-dev',
        'http://github.com/mattupstate/flask-oauth/tarball/master#egg=Flask-OAuth-0.12-dev',
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
