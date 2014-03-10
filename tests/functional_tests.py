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

def get_mock_twitter_token_pair():
    return {
        'access_token': 'the_oauth_token',
        'secret': 'the_oauth_token_secret'
        }

def get_mock_twitter_updated_token_pair():
    return {
        'access_token': 'the_updated_oauth_token',
        'secret': 'the_updated_oauth_token_secret'
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

    def _post(self, route, data=None, content_type=None, follow_redirects=True, headers=None):
        content_type = content_type or 'application/x-www-form-urlencoded'
        return self.client.post(route, data=data,
                                follow_redirects=follow_redirects,
                                content_type=content_type, headers=headers)

    def _get(self, route, content_type=None, follow_redirects=None, headers=None):
        return self.client.get(route, follow_redirects=follow_redirects,
                               content_type=content_type or 'text/html',
                               headers=headers)

    def authenticate(self, email="matt@lp.com", password="password", endpoint=None, **kwargs):
        data = dict(email=email, password=password, remember='y')
        return self._post(endpoint or '/login', data=data, **kwargs)

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
    @mock.patch('flask_oauthlib.client.OAuthRemoteApp.handle_oauth1_response')
    @mock.patch('flask_oauthlib.client.OAuthRemoteApp.authorize')
    def test_connect_twitter(self,
                             mock_authorize,
                             mock_handle_oauth1_response,
                             mock_get_connection_values):
        mock_get_connection_values.return_value = get_mock_twitter_connection_values()
        mock_authorize.return_value = 'Should be a redirect'
        mock_handle_oauth1_response.return_value = get_mock_twitter_response()

        r = self.authenticate()

        self.assertIn('Hello', r.data)
        self._post('/connect/twitter')
        r = self._get('/connect/twitter?oauth_token=oauth_token&oauth_verifier=oauth_verifier', follow_redirects=True)
        self.assertIn('Connection established to Twitter', r.data)

    @mock.patch('flask_social.providers.twitter.get_connection_values')
    @mock.patch('flask_oauthlib.client.OAuthRemoteApp.handle_oauth1_response')
    @mock.patch('flask_oauthlib.client.OAuthRemoteApp.authorize')
    def test_double_connect_twitter(self,
                                    mock_authorize,
                                    mock_handle_oauth1_response,
                                    mock_get_connection_values):
        mock_get_connection_values.return_value = get_mock_twitter_connection_values()
        mock_authorize.return_value = 'Should be a redirect'
        mock_handle_oauth1_response.return_value = get_mock_twitter_response()

        r = self.authenticate()

        for x in range(2):
            self._post('/connect/twitter')
            r = self._get('/connect/twitter?oauth_token=oauth_token&oauth_verifier=oauth_verifier', follow_redirects=True)
        self.assertIn('A connection is already established with', r.data)

    @mock.patch('flask_social.providers.twitter.get_connection_values')
    @mock.patch('flask_social.providers.twitter.get_token_pair_from_response')
    @mock.patch('flask_oauthlib.client.OAuthRemoteApp.handle_oauth1_response')
    @mock.patch('flask_oauthlib.client.OAuthRemoteApp.authorize')
    def test_unconnected_twitter_login(self,
                                       mock_authorize,
                                       mock_handle_oauth1_response,
                                       mock_get_token_pair_from_response,
                                       mock_get_connection_values):
        mock_get_connection_values.return_value = get_mock_twitter_connection_values()
        mock_get_token_pair_from_response.return_value = get_mock_twitter_token_pair()
        mock_authorize.return_value = 'Should be a redirect'
        mock_handle_oauth1_response.return_value = get_mock_twitter_response()

        self._post('/login/twitter')
        r = self._get('/login/twitter?oauth_token=oauth_token&oauth_verifier=oauth_verifier', follow_redirects=True)
        self.assertIn('Twitter account not associated with an existing user', r.data)

    @mock.patch('flask_social.providers.twitter.get_api')
    @mock.patch('flask_social.providers.twitter.get_connection_values')
    @mock.patch('flask_social.providers.twitter.get_token_pair_from_response')
    @mock.patch('flask_oauthlib.client.OAuthRemoteApp.handle_oauth1_response')
    @mock.patch('flask_oauthlib.client.OAuthRemoteApp.authorize')
    def test_connected_twitter_login(self,
                                     mock_authorize,
                                     mock_handle_oauth1_response,
                                     mock_get_token_pair_from_response,
                                     mock_get_connection_values,
                                     mock_get_twitter_api):
        mock_get_connection_values.return_value = get_mock_twitter_connection_values()
        mock_get_token_pair_from_response.return_value = get_mock_twitter_token_pair()
        mock_authorize.return_value = 'Should be a redirect'
        mock_handle_oauth1_response.return_value = get_mock_twitter_response()
        mock_get_twitter_api.return_value = get_mock_twitter_connection_values()

        self.authenticate()
        self._post('/connect/twitter')
        r = self._get('/connect/twitter?oauth_token=oauth_token&oauth_verifier=oauth_verifier', follow_redirects=True)
        self.assertIn('Connection established to Twitter', r.data)
        self._get('/logout')
        self._post('/login/twitter')
        r = self._get('/login/twitter?oauth_token=oauth_token&oauth_verifier=oauth_verifier', follow_redirects=True)
        self.assertIn("Hello matt@lp.com", r.data)

    @mock.patch('flask_social.providers.twitter.get_api')
    @mock.patch('flask_social.providers.twitter.get_connection_values')
    @mock.patch('flask_social.providers.twitter.get_token_pair_from_response')
    @mock.patch('flask_oauthlib.client.OAuthRemoteApp.handle_oauth1_response')
    @mock.patch('flask_oauthlib.client.OAuthRemoteApp.authorize')
    def test_connected_twitter_login_update_token(self,
                                                  mock_authorize,
                                                  mock_handle_oauth1_response,
                                                  mock_get_token_pair_from_response,
                                                  mock_get_connection_values,
                                                  mock_get_twitter_api):
        mock_get_connection_values.return_value = get_mock_twitter_connection_values()
        mock_get_token_pair_from_response.return_value = get_mock_twitter_updated_token_pair()
        mock_authorize.return_value = 'Should be a redirect'
        mock_handle_oauth1_response.return_value = get_mock_twitter_response()
        mock_get_twitter_api.return_value = get_mock_twitter_connection_values()

        self.authenticate()
        self._post('/connect/twitter')
        r = self._get('/connect/twitter?oauth_token=oauth_token&oauth_verifier=oauth_verifier', follow_redirects=True)
        self.assertIn('Connection established to Twitter', r.data)
        user = self.app.get_user()
        connection = [c for c in user.connections if c.provider_id == 'twitter'][0]
        self.assertEqual(connection.access_token,
                         get_mock_twitter_connection_values()['access_token'])
        self.assertEqual(connection.secret,
                         get_mock_twitter_connection_values()['secret'])

        self._get('/logout')
        self._post('/login/twitter')
        r = self._get('/login/twitter?oauth_token=oauth_token&oauth_verifier=oauth_verifier', follow_redirects=True)
        self.assertIn("Hello matt@lp.com", r.data)
        user = self.app.get_user()
        connection = [c for c in user.connections if c.provider_id == 'twitter'][0]
        self.assertEqual(connection.access_token,
                         get_mock_twitter_updated_token_pair()['access_token'])
        self.assertEqual(connection.secret,
                         get_mock_twitter_updated_token_pair()['secret'])

    @mock.patch('flask_social.providers.twitter.get_api')
    @mock.patch('flask_social.providers.twitter.get_connection_values')
    @mock.patch('flask_social.providers.twitter.get_token_pair_from_response')
    @mock.patch('flask_oauthlib.client.OAuthRemoteApp.handle_oauth1_response')
    @mock.patch('flask_oauthlib.client.OAuthRemoteApp.authorize')
    def test_reconnect_twitter_token(self,
                                     mock_authorize,
                                     mock_handle_oauth1_response,
                                     mock_get_token_pair_from_response,
                                     mock_get_connection_values,
                                     mock_get_twitter_api):
        mock_get_connection_values.return_value = get_mock_twitter_connection_values()
        mock_get_token_pair_from_response.return_value = get_mock_twitter_updated_token_pair()
        mock_authorize.return_value = 'Should be a redirect'
        mock_handle_oauth1_response.return_value = get_mock_twitter_response()
        mock_get_twitter_api.return_value = get_mock_twitter_connection_values()

        self.authenticate()
        self._post('/connect/twitter')
        r = self._get('/connect/twitter?oauth_token=oauth_token&oauth_verifier=oauth_verifier', follow_redirects=True)
        self.assertIn('Connection established to Twitter', r.data)
        user = self.app.get_user()
        connection = [c for c in user.connections if c.provider_id == 'twitter'][0]
        self.assertEqual(connection.access_token,
                         get_mock_twitter_connection_values()['access_token'])
        self.assertEqual(connection.secret,
                         get_mock_twitter_connection_values()['secret'])

        self._post('/reconnect/twitter')
        r = self._get('/login/twitter?oauth_token=oauth_token&oauth_verifier=oauth_verifier', follow_redirects=True)
        self.assertIn("Hello matt@lp.com", r.data)
        user = self.app.get_user()
        connection = [c for c in user.connections if c.provider_id == 'twitter'][0]
        self.assertEqual(connection.access_token,
                         get_mock_twitter_updated_token_pair()['access_token'])
        self.assertEqual(connection.secret,
                         get_mock_twitter_updated_token_pair()['secret'])

    @mock.patch('flask_social.providers.twitter.get_connection_values')
    @mock.patch('flask_oauthlib.client.OAuthRemoteApp.handle_oauth1_response')
    @mock.patch('flask_oauthlib.client.OAuthRemoteApp.authorize')
    def test_remove_connection(self,
                               mock_authorize,
                               mock_handle_oauth1_response,
                               mock_get_connection_values):
        mock_get_connection_values.return_value = get_mock_twitter_connection_values()
        mock_authorize.return_value = 'Should be a redirect'
        mock_handle_oauth1_response.return_value = get_mock_twitter_response()

        self._post('/login', data=dict(email='matt@lp.com', password='password'))
        self._post('/connect/twitter')
        r = self._get('/connect/twitter?oauth_token=oauth_token&oauth_verifier=oauth_verifier', follow_redirects=True)
        r = self.client.delete('/connect/twitter/1234', follow_redirects=True)
        self.assertIn('Connection to Twitter removed', r.data)


class MongoEngineTwitterSocialTests(TwitterSocialTests):
    APP_TYPE = 'mongo'

class PeeweeTwitterSocialTests(TwitterSocialTests):
    APP_TYPE = 'peewee'
