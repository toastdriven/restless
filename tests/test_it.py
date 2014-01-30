import unittest

try:
    import itty
    from restless.it import IttyResource
except ImportError:
    itty = None
    IttyResource = object

from restless.utils import json

from .fakes import FakeHttpRequest


class ItTestResource(IttyResource):
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


@unittest.skipIf(not itty, "itty is not available")
class IttyResourceTestCase(unittest.TestCase):
    def setUp(self):
        super(IttyResourceTestCase, self).setUp()
        self.res = ItTestResource()

        # Just for the fake data.
        self.res.fake_init()

    def test_as_list(self):
        list_endpoint = ItTestResource.as_list()
        request = FakeHttpRequest('GET')

        resp = list_endpoint(request)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.status, 200)
        self.assertEqual(json.loads(resp.output), {
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
        detail_endpoint = ItTestResource.as_detail()
        request = FakeHttpRequest('GET')

        resp = detail_endpoint(request, 4)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.status, 200)
        self.assertEqual(json.loads(resp.output), {
            'id': 4,
            'title': 'Another'
        })

    def test_is_debug(self):
        self.assertFalse(self.res.is_debug())

        self.res.debug = True
        self.addCleanup(setattr, self.res, 'debug', False)
        self.assertTrue(self.res.is_debug())

    def test_build_response(self):
        resp = self.res.build_response('Hello, world!', status=302)
        self.assertEqual(resp.status, 302)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.output, 'Hello, world!')

    def test_setup_urls(self):
        self.assertEqual(len(itty.REQUEST_MAPPINGS['GET']), 0)
        self.assertEqual(len(itty.REQUEST_MAPPINGS['POST']), 0)
        self.assertEqual(len(itty.REQUEST_MAPPINGS['PUT']), 0)
        self.assertEqual(len(itty.REQUEST_MAPPINGS['DELETE']), 0)

        ItTestResource.setup_urls('/test')
        self.assertEqual(len(itty.REQUEST_MAPPINGS['GET']), 2)
        self.assertEqual(len(itty.REQUEST_MAPPINGS['POST']), 2)
        self.assertEqual(len(itty.REQUEST_MAPPINGS['PUT']), 2)
        self.assertEqual(len(itty.REQUEST_MAPPINGS['DELETE']), 2)
        self.assertEqual(itty.REQUEST_MAPPINGS['GET'][0][1], '/test/')
        self.assertEqual(itty.REQUEST_MAPPINGS['GET'][1][1], '/test/(?P<pk>\\d+)/')
