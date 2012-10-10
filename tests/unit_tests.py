from unittest import TestCase
from flask_social.core import _SocialState


class FlaskSocialUnitTests(TestCase):

    def test_social_state_raises_attribute_error(self):
        state = _SocialState(providers={})
        self.assertRaises(AttributeError, lambda: state.something)
