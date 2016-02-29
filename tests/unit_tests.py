from unittest import TestCase
from flask_social.core import _SocialState
from flask_social import utils


class FlaskSocialUnitTests(TestCase):

    def test_social_state_raises_attribute_error(self):
        state = _SocialState(providers={})
        self.assertRaises(AttributeError, lambda: state.something)

    def test_update_recursive(self):
        dct = {'a': {'b': None, 'c': 'c'}}
        upd = {'a': {'b': 'c'}}
        utils.update_recursive(dct, upd)

        self.assertEqual(dct['a']['c'], 'c')
        self.assertEqual(dct['a']['b'], 'c')
