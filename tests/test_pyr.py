import unittest

try:
    from pyramid import testing
    from restless.pyr import PyramidResource
except ImportError:
    testing = None
    PyramidResource = object

from restless.utils import json

from .fakes import FakeHttpRequest, FakeHttpResponse


class PyrTestResource(PyramidResource):
    fake_db = []

    def fake_init(self):
        # Just for testing.
        self.__class__.fake_db = [
            {"id": "dead-beef", "title": 'First post'},
            {"id": "de-faced", "title": 'Another'},
            {"id": "bad-f00d", "title": 'Last'},
        ]

    def list(self):
        return self.fake_db

    def detail(self, name):
        for item in self.fake_db:
            if item['id'] == name:
                return item

    def create(self):
        self.fake_db.append(self.data)

    def is_authenticated(self):
        return self.request_method() != 'DELETE'


@unittest.skipIf(not testing, 'Pyramid is not available')
class PyramidResourceTestCase(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.res = PyrTestResource()
        self.res.fake_init()

    def test_as_list(self):
        list_endpoint = PyrTestResource.as_list()
        req = FakeHttpRequest('GET')
        resp = list_endpoint(req)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.body.decode('utf-8')), {
            'objects': [
                {
                    'id': 'dead-beef',
                    'title': 'First post'
                },
                {
                    'id': 'de-faced',
                    'title': 'Another'
                },
                {
                    'id': 'bad-f00d',
                    'title': 'Last'
                }
            ]
        })

    def test_as_detail(self):
        detail_endpoint = PyrTestResource.as_detail()
        req = testing.DummyRequest()

        req = FakeHttpRequest('GET')
        req.matchdict = {'name': 'de-faced'}

        resp = detail_endpoint(req)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.body.decode('utf-8')), {
            'id': 'de-faced',
            'title': 'Another'
        })

    def test_handle_not_authenticated(self):
        # Special-cased above for testing.
        self.res.request = FakeHttpRequest('DELETE')

        resp = self.res.handle('list')
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.body.decode('utf-8'), '{"error": "Unauthorized."}')

    def test_add_views(self):
        config = PyrTestResource.add_views(self.config, '/users/')
        routes = config.get_routes_mapper().get_routes()
        self.assertEqual(len(routes), 2)
        self.assertEqual([r.name for r in routes], ['api_pyrtest_list', 'api_pyrtest_detail'])
        self.assertEqual([r.path for r in routes], ['/users/', '/users/{name}/'])

    def test_create(self):
        self.res.request = FakeHttpRequest('POST', body='{"id": 6, "title": "Moved hosts"}')
        self.assertEqual(len(self.res.fake_db), 3)

        resp = self.res.handle('list')
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.body.decode('utf-8'), '')

        # Check the internal state.
        self.assertEqual(len(self.res.fake_db), 4)
        self.assertEqual(self.res.data, {
            'id': 6,
            'title': 'Moved hosts'
        })
