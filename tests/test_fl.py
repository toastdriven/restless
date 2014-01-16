import unittest

# Ugh. Globals for Flask.
import flask

from restless.fl import FlaskResource
from restless.utils import json

from .fakes import FakeHttpRequest


class FlTestResource(FlaskResource):
    fake_db = []

    def fake_init(self):
        # Just for testing.
        self.__class__.fake_db = [
            {"id": 2, "title": 'First post'},
            {"id": 4, "title": 'Another'},
            {"id": 5, "title": 'Last'},
        ]

    def list(self):
        return self.fake_db

    def detail(self, pk):
        for item in self.fake_db:
            if item['id'] == pk:
                return item

    def create(self):
        self.fake_db.append(self.data)


class FlaskResourceTestCase(unittest.TestCase):
    def setUp(self):
        super(FlaskResourceTestCase, self).setUp()
        self.res = FlTestResource()

        self.app = flask.Flask('test_restless')
        self.app.config['DEBUG'] = True

        # Just for the fake data.
        self.res.fake_init()

    def test_as_list(self):
        list_endpoint = FlTestResource.as_list()
        flask.request = FakeHttpRequest('GET')

        with self.app.test_request_context('/whatever/', method='GET'):
            resp = list_endpoint()
            self.assertEqual(resp.headers['Content-Type'], 'application/json')
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(json.loads(resp.data.decode('utf-8')), {
                'objects': [
                    {
                        'id': 2,
                        'title': 'First post'
                    },
                    {
                        'id': 4,
                        'title': 'Another'
                    },
                    {
                        'id': 5,
                        'title': 'Last'
                    }
                ]
            })

    def test_as_detail(self):
        detail_endpoint = FlTestResource.as_detail()
        flask.request = FakeHttpRequest('GET')

        with self.app.test_request_context('/whatever/', method='GET'):
            resp = detail_endpoint(4)
            self.assertEqual(resp.headers['Content-Type'], 'application/json')
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(json.loads(resp.data.decode('utf-8')), {
                'id': 4,
                'title': 'Another'
            })

    def test_is_debug(self):
        with self.app.test_request_context('/whatever/', method='GET'):
            self.assertTrue(self.res.is_debug())

        with self.app.test_request_context('/whatever/', method='GET'):
            self.app.debug = False
            # This should do the correct lookup.
            self.assertFalse(self.res.is_debug())

    def test_build_response(self):
        with self.app.test_request_context('/whatever/', method='GET'):
            resp = self.res.build_response('Hello, world!', status=302)
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.headers['Content-Type'], 'application/json')
            self.assertEqual(resp.data.decode('utf-8'), 'Hello, world!')

    def test_add_url_rules(self):
        with self.app.test_request_context('/whatever/', method='GET'):
            FlTestResource.add_url_rules(self.app, '/api/')
            rules = sorted([rule.endpoint for rule in self.app.url_map.iter_rules()])
            self.assertEqual(len(rules), 3)
            self.assertEqual(rules[0], 'api_fltest_detail')
            self.assertEqual(rules[1], 'api_fltest_list')

            FlTestResource.add_url_rules(self.app, '/api/', endpoint_prefix='v2_tests')
            rules = sorted([rule.endpoint for rule in self.app.url_map.iter_rules()])
            self.assertEqual(len(rules), 5)
            self.assertEqual(rules[3], 'v2_tests_detail')
            self.assertEqual(rules[4], 'v2_tests_list')
