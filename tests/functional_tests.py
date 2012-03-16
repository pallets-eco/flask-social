import unittest
from example import app
from flask.ext.testing import Twill, twill

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
            fn = app.create_sqlalchemy_app
        
        if app_type == 'mongo':
            fn = app.create_mongoengine_app
        
        return fn(auth_config)
    
  
class TwitterSocialTests(SocialTest):
    
    def _login(self, t):
        t.browser.go(t.url('/login'))
        twill.commands.fv('login_form', 'username', 'matt@lp.com')
        twill.commands.fv('login_form', 'password', 'password')
        twill.commands.submit(0)
    
    def _login_provider(self, t, provider):
        t.browser.go(t.url('/login'))
        twill.commands.fv('%s_login_form' % provider, 'login_%s' % provider, '')
        t.browser.submit(1)
        
    def _start_connect(self, t, provider):
        t.browser.go(t.url('/profile'))
        twill.commands.fv('%s_connect_form' % provider, 'connect_%s' % provider, '')
        t.browser.submit(0)
    
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
            assert 'Connection established to Twitter' in t.browser.get_html()
            
    def test_double_connect_twitter(self):
        with Twill(self.app) as t:
            self._login(t)
            self._start_connect(t, 'twitter')
            self._authorize_twitter(t)
            self._start_connect(t, 'twitter')
            self._authorize_twitter(t)
            assert 'A connection is already established with' in t.browser.get_html()
            
    def test_unconnected_twitter_login(self):
        with Twill(self.app) as t:
            self._login_provider(t, 'twitter')
            self._authorize_twitter(t)
            assert 'Twitter account not associated with an existing user' in t.browser.get_html()
       
    def test_connected_login_with_twitter(self):
        with Twill(self.app) as t:
            self._login(t)
            self._start_connect(t, 'twitter')
            self._authorize_twitter(t)
            t.browser.go(t.url('/logout'))
            self._login_provider(t, 'twitter')
            self._authorize_twitter(t)
            assert 'Profile Page' in t.browser.get_html()
            
class MongoEngineTwitterSocialTests(TwitterSocialTests):
    APP_TYPE = 'mongo'