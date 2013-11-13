import unittest

import mock

from tests.test_app.sqlalchemy import create_app as create_sql_app
from tests.test_app.mongoengine import create_app as create_mongo_app
from tests.test_app.peewee_app import create_app as create_peewee_app


def get_mock_twitter_response():
    return {
        'oauth_token_secret': 'the_oauth_token_secret',
        'user_id': '1234',
        'oauth_token': 'the_oauth_token',
        'screen_name': 'twitter_username',
        'name': 'twitter_name'
    }


def get_mock_twitter_connection_values():
    return {
        'provider_id': 'twitter',
        'provider_user_id': '1234',
        'access_token': 'the_oauth_token',
        'secret': 'the_oauth_token_secret',
        'display_name': '@twitter_username',
        'full_name': 'twitter_name',
        'profile_url': 'http://twitter.com/twitter_username',
        'image_url': 'https://cdn.twitter.com/something.png'
    }


class SocialTest(unittest.TestCase):

    SOCIAL_CONFIG = None
    APP_TYPE = None

    def setUp(self):
        super(SocialTest, self).setUp()
        self.app = self._create_app(self.SOCIAL_CONFIG or None)
        self.app.debug = False
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def tearDown(self):
        super(SocialTest, self).tearDown()
        self.client.get('/logout')

    def _create_app(self, auth_config):
        app_type = self.APP_TYPE or 'sql'
        if app_type == 'sql':
            return create_sql_app(auth_config, False)
        if app_type == 'mongo':
            return create_mongo_app(auth_config, False)
        if app_type == 'peewee':
            return create_peewee_app(auth_config, False)

    def assertIn(self, member, container, msg=None):
        if hasattr(unittest.TestCase, 'assertIn'):
            return unittest.TestCase.assertIn(self, member, container, msg)

        return self.assertTrue(member in container)

    def assertNotIn(self, member, container, msg=None):
        if hasattr(unittest.TestCase, 'assertNotIn'):
            return unittest.TestCase.assertNotIn(self, member, container, msg)

        return self.assertFalse(member in container)

    def assertIsNotNone(self, obj, msg=None):
        if hasattr(unittest.TestCase, 'assertIsNotNone'):
            return unittest.TestCase.assertIsNotNone(self, obj, msg)

        return self.assertTrue(obj is not None)


class TwitterSocialTests(SocialTest):

    @mock.patch('flask_social.providers.twitter.get_connection_values')
    @mock.patch('flask_oauth.OAuthRemoteApp.handle_oauth1_response')
    @mock.patch('flask_oauth.OAuthRemoteApp.authorize')
    def test_connect_twitter(self, mock_authorize, mock_handle_oauth1_response, mock_get_connection_values):
        mock_get_connection_values.return_value = get_mock_twitter_connection_values()
        mock_authorize.return_value = 'Should be a redirect'
        mock_handle_oauth1_response.return_value = get_mock_twitter_response()

        self.client.post('/login', data=dict(email='matt@lp.com', password='password'))
        self.client.post('/connect/twitter')
        r = self.client.get('/connect/twitter?oauth_token=oauth_token&oauth_verifier=oauth_verifier', follow_redirects=True)
        self.assertIn('Connection established to Twitter', r.data)

    @mock.patch('flask_social.providers.twitter.get_connection_values')
    @mock.patch('flask_oauth.OAuthRemoteApp.handle_oauth1_response')
    @mock.patch('flask_oauth.OAuthRemoteApp.authorize')
    def test_double_connect_twitter(self, mock_authorize, mock_handle_oauth1_response, mock_get_connection_values):
        mock_get_connection_values.return_value = get_mock_twitter_connection_values()
        mock_authorize.return_value = 'Should be a redirect'
        mock_handle_oauth1_response.return_value = get_mock_twitter_response()

        self.client.post('/login', data=dict(email='matt@lp.com', password='password'))
        for x in range(2):
            self.client.post('/connect/twitter')
            r = self.client.get('/connect/twitter?oauth_token=oauth_token&oauth_verifier=oauth_verifier', follow_redirects=True)
        self.assertIn('A connection is already established with', r.data)

    @mock.patch('flask_social.providers.twitter.get_connection_values')
    @mock.patch('flask_oauth.OAuthRemoteApp.handle_oauth1_response')
    @mock.patch('flask_oauth.OAuthRemoteApp.authorize')
    def test_unconnected_twitter_login(self, mock_authorize, mock_handle_oauth1_response, mock_get_connection_values):
        mock_get_connection_values.return_value = get_mock_twitter_connection_values()
        mock_authorize.return_value = 'Should be a redirect'
        mock_handle_oauth1_response.return_value = get_mock_twitter_response()

        self.client.post('/login/twitter')
        r = self.client.get('/login/twitter?oauth_token=oauth_token&oauth_verifier=oauth_verifier', follow_redirects=True)
        self.assertIn('Twitter account not associated with an existing user', r.data)

    @mock.patch('flask_social.providers.twitter.get_connection_values')
    @mock.patch('flask_oauth.OAuthRemoteApp.handle_oauth1_response')
    @mock.patch('flask_oauth.OAuthRemoteApp.authorize')
    def test_connected_twitter_login(self, mock_authorize, mock_handle_oauth1_response, mock_get_connection_values):
        mock_get_connection_values.return_value = get_mock_twitter_connection_values()
        mock_authorize.return_value = 'Should be a redirect'
        mock_handle_oauth1_response.return_value = get_mock_twitter_response()

        self.client.post('/login', data=dict(email='matt@lp.com', password='password'))
        self.client.post('/connect/twitter')
        r = self.client.get('/connect/twitter?oauth_token=oauth_token&oauth_verifier=oauth_verifier', follow_redirects=True)
        self.assertIn('Connection established to Twitter', r.data)
        self.client.get('/logout')
        self.client.post('/login/twitter')
        r = self.client.get('/login/twitter?oauth_token=oauth_token&oauth_verifier=oauth_verifier', follow_redirects=True)
        self.assertIn("Hello matt@lp.com", r.data)

    @mock.patch('flask_social.providers.twitter.get_connection_values')
    @mock.patch('flask_oauth.OAuthRemoteApp.handle_oauth1_response')
    @mock.patch('flask_oauth.OAuthRemoteApp.authorize')
    def test_remove_connection(self, mock_authorize, mock_handle_oauth1_response, mock_get_connection_values):
        mock_get_connection_values.return_value = get_mock_twitter_connection_values()
        mock_authorize.return_value = 'Should be a redirect'
        mock_handle_oauth1_response.return_value = get_mock_twitter_response()

        self.client.post('/login', data=dict(email='matt@lp.com', password='password'))
        self.client.post('/connect/twitter')
        r = self.client.get('/connect/twitter?oauth_token=oauth_token&oauth_verifier=oauth_verifier', follow_redirects=True)
        r = self.client.delete('/connect/twitter/1234', follow_redirects=True)
        self.assertIn('Connection to Twitter removed', r.data)


class MongoEngineTwitterSocialTests(TwitterSocialTests):
    APP_TYPE = 'mongo'


class PeeweeTwitterSocialTests(TwitterSocialTests):
    APP_TYPE = 'peewee'
