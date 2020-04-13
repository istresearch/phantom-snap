from unittest import TestCase
from phantom_snap.lambda_schema import SCHEMA
from jsonschema.validators import validator_for


class TestSchema(TestCase):

    def test_valid_schema_render(self):
        for version in SCHEMA.keys():
            for name in SCHEMA[version]:
                schema = SCHEMA[version][name]
                cls = validator_for(schema)
                result = cls.check_schema(schema)