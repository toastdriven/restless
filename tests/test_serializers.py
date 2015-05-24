import datetime
from decimal import Decimal
import unittest
import uuid

from restless.serializers import JSONSerializer


class JSONSerializerTestCase(unittest.TestCase):
    def setUp(self):
        super(JSONSerializerTestCase, self).setUp()
        self.serializer = JSONSerializer()
        self.dict_data = {
            'hello': 'world',
            'abc': 123,
            'more': {
                'things': 'here',
                # Some data the usual JSON encoder can't handle...
                'nested': datetime.datetime(2014, 3, 30, 12, 55, 15),
                'again': Decimal('18.9'),
                'uuid': uuid.uuid4()
            },
        }

    def test_serialize(self):
        body = self.serializer.serialize(self.dict_data)
        self.assertTrue('"hello": "world"' in body)
        self.assertTrue('"abc": 123' in body)
        self.assertTrue('"nested": "2014-03-30T12:55:15"' in body)
        self.assertTrue('"again": "18.9"' in body)

    def test_deserialize(self):
        self.assertEqual(self.serializer.deserialize('{"more": "things"}'), {
            'more': 'things',
        })
