import unittest

from flask.ext.testing import Twill, twill
from tests.test_app.sqlalchemy import create_app as create_sql_app
from tests.test_app.mongoengine import create_app as create_mongo_app


class SocialTest(unittest.TestCase):

    SOCIAL_CONFIG = None
    APP_TYPE = None

    def setUp(self):
        super(SocialTest, self).setUp()

        self.app = self._create_app(self.SOCIAL_CONFIG or None)
        self.app.debug = False
        self.app.config['TESTING'] = True

        self.client = self.app.test_client()

    def _create_app(self, auth_config):
        app_type = self.APP_TYPE or 'sql'
        if app_type == 'sql':
            return create_sql_app(auth_config, False)
        if app_type == 'mongo':
            return create_mongo_app(auth_config, False)

    def _login(self, t):
        t.browser.go(t.url('/login'))
        twill.commands.fv('login_user_form', 'email', 'matt@lp.com')
        twill.commands.fv('login_user_form', 'password', 'password')
        twill.commands.submit(0)

    def _login_provider(self, t, provider):
        t.browser.go(t.url('/login'))
        twill.commands.fv('%s_login_form' % provider, 'login_%s' % provider, '')
        t.browser.submit(1)

    def _start_connect(self, t, provider):
        t.browser.go(t.url('/profile'))
        twill.commands.fv('%s_connect_form' % provider,
                          'connect_' + provider,
                          '')
        t.browser.submit('connect_' + provider)

    def _remove_connection(self, t, provider):
        t.browser.go(t.url('/profile'))
        twill.commands.fv('%s_disconnect_form' % provider,
                          'disconnect_' + provider,
                          '')
        t.browser.submit('disconnect_' + provider)


class TwitterSocialTests(SocialTest):

    def _fill_twitter_oauth(self, t, username, password):
        try:
            twill.commands.fv('oauth_form', 'session[username_or_email]', username)
            twill.commands.fv('oauth_form', 'session[password]', password)
        except:
            pass

    def _authorize_twitter(self, t, username=None, password=None):
        if not 'oauth_form' in t.browser.get_html():
            return
        username = username or self.app.config['TWITTER_USERNAME']
        password = password or self.app.config['TWITTER_PASSWORD']
        self._fill_twitter_oauth(t, username, password)
        form = t.browser.get_form('oauth_form')
        twill.commands.fv('oauth_form', 'cancel', '')
        form.find_control('cancel').disabled = True
        t.browser.submit(0)

    def _deny_twitter(self, t, username, password):
        self._fill_twitter_oauth(username, password)
        t.browser.submit(0)

    def test_connect_twitter(self):
        with Twill(self.app) as t:
            self._login(t)
            self._start_connect(t, 'twitter')
            self._authorize_twitter(t)
            self.assertIn('Connection established to Twitter', t.browser.get_html())

    def test_double_connect_twitter(self):
        with Twill(self.app) as t:
            self._login(t)
            self._start_connect(t, 'twitter')
            self._authorize_twitter(t)
            self._start_connect(t, 'twitter')
            self._authorize_twitter(t)
            self.assertIn('A connection is already established with', t.browser.get_html())

    def test_unconnected_twitter_login(self):
        with Twill(self.app) as t:
            self._login_provider(t, 'twitter')
            self._authorize_twitter(t)
            self.assertIn('Twitter account not associated with an existing user',
                          t.browser.get_html())

    def test_connected_login_with_twitter(self):
        with Twill(self.app) as t:
            self._login(t)
            self._start_connect(t, 'twitter')
            self._authorize_twitter(t)
            t.browser.go(t.url('/logout'))
            self._login_provider(t, 'twitter')
            self._authorize_twitter(t)
            self.assertIn('Profile Page', t.browser.get_html())

    def test_remove_connection(self):
        with Twill(self.app) as t:
            self._login(t)
            self._start_connect(t, 'twitter')
            self._authorize_twitter(t)
            self._remove_connection(t, 'twitter')
            assert 'Connection to Twitter removed' in t.browser.get_html()


class MongoEngineTwitterSocialTests(TwitterSocialTests):
    APP_TYPE = 'mongo'


"""
# Unfortunately Facebook can't be tested because
# the Twill client is not a supported browser.
# Leaving this in for reference
class FacebookSocialTests(SocialTest):

    def _login_facebook(self, t, email=None, password=None):
        email = email or self.app.config['FACEBOOK_EMAIL']
        password = password or self.app.config['FACEBOOK_PASSWORD']
        twill.commands.fv('login_form', 'email', email)
        twill.commands.fv('login_form', 'pass', password)
        t.browser.submit(0)

    def _authorize_facebook(self, t, username=None, password=None):
        if 'login_form' in t.browser.get_html():
            self._login_facebook(t)

        if 'uiserver_form' in t.browser.get_html():
            t.browser.get_form('uiserver_form')
            #t.browser.submit('grant_clicked')
            t.browser.submit(0)

    def test_connect_facebook(self):
        with Twill(self.app) as t:
            self._login(t)
            self._start_connect(t, 'facebook')
            self._authorize_facebook(t)
            assert 'Connection established to Facebook' in t.browser.get_html()
"""
