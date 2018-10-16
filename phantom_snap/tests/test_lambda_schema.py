from unittest import TestCase
from phantom_snap.lambda_schema import SCHEMA
from flex.core import validate

class TestSchema(TestCase):

    def test_valid_schema(self):
        validate(SCHEMA)