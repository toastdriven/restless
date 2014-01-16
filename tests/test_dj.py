import unittest

# Ugh. Settings for Django.
from django.conf import settings
settings.configure(DEBUG=True)

from restless.dj import DjangoResource
from restless.exceptions import MethodNotImplemented, Unauthorized
from restless.utils import json

from .fakes import FakeHttpRequest, FakeModel


class DjTestResource(DjangoResource):
    fields = {
        'id': 'id',
        'title': 'title',
        'author': 'username',
        'body': 'content'
    }
    fake_db = []

    def fake_init(self):
        # Just for testing.
        self.__class__.fake_db = [
            FakeModel(id=2, title='First post', username='daniel', content='Hello world!'),
            FakeModel(id=4, title='Another', username='daniel', content='Stuff here.'),
            FakeModel(id=5, title='Last', username='daniel', content="G'bye!"),
        ]

    def is_authenticated(self):
        if self.request_method() == 'DELETE':
            return False

        return True

    def list(self):
        return self.fake_db

    def detail(self, pk):
        for item in self.fake_db:
            if item.id == pk:
                return item

    def create(self):
        self.fake_db.append(FakeModel(
            **self.data
        ))

    def update(self, pk):
        for item in self.fake_db:
            if item.id == pk:
                for k, v in self.data:
                    setattr(item, k, v)
                    return

    def create_detail(self):
        raise ValueError("This is a random & crazy exception.")


class DjangoResourceTestCase(unittest.TestCase):
    def setUp(self):
        super(DjangoResourceTestCase, self).setUp()
        self.res = DjTestResource()
        # Just for the fake data.
        self.res.fake_init()

    def test_as_list(self):
        list_endpoint = DjTestResource.as_list()
        req = FakeHttpRequest('GET')

        resp = list_endpoint(req)
        self.assertEqual(resp['Content-Type'], 'application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content.decode('utf-8')), {
            'objects': [
                {
                    'author': 'daniel',
                    'body': 'Hello world!',
                    'id': 2,
                    'title': 'First post'
                },
                {
                    'author': 'daniel',
                    'body': 'Stuff here.',
                    'id': 4,
                    'title': 'Another'
                },
                {
                    'author': 'daniel',
                    'body': "G'bye!",
                    'id': 5,
                    'title': 'Last'
                }
            ]
        })

    def test_as_detail(self):
        detail_endpoint = DjTestResource.as_detail()
        req = FakeHttpRequest('GET')

        resp = detail_endpoint(req, 4)
        self.assertEqual(resp['Content-Type'], 'application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content.decode('utf-8')), {
            'author': 'daniel',
            'body': 'Stuff here.',
            'id': 4,
            'title': 'Another'
        })

    def test_handle_not_implemented(self):
        self.res.request = FakeHttpRequest('TRACE')

        with self.assertRaises(MethodNotImplemented):
            self.res.handle('list')

    def test_handle_not_authenticated(self):
        # Special-cased above for testing.
        self.res.request = FakeHttpRequest('DELETE')

        with self.assertRaises(Unauthorized):
            self.res.handle('list')

    def test_handle_build_err(self):
        # Special-cased above for testing.
        self.res.request = FakeHttpRequest('POST')
        settings.DEBUG = False
        self.addCleanup(setattr, settings, 'DEBUG', True)

        resp = self.res.handle('detail')
        self.assertEqual(resp['Content-Type'], 'application/json')
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(json.loads(resp.content.decode('utf-8')), {
            'error': 'This is a random & crazy exception.'
        })

    def test_urls(self):
        patterns = DjTestResource.urls()
        self.assertEqual(len(patterns), 2)
        self.assertEqual(patterns[0].name, 'api_djtest_list')
        self.assertEqual(patterns[1].name, 'api_djtest_detail')

        patterns = DjTestResource.urls(name_prefix='v2_tests')
        self.assertEqual(len(patterns), 2)
        self.assertEqual(patterns[0].name, 'v2_tests_list')
        self.assertEqual(patterns[1].name, 'v2_tests_detail')

    def test_create(self):
        self.res.request = FakeHttpRequest('POST', body='{"id": 6, "title": "Moved hosts", "author": "daniel"}')
        self.assertEqual(len(self.res.fake_db), 3)

        resp = self.res.handle('list')
        self.assertEqual(resp['Content-Type'], 'application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.content.decode('utf-8'), '')

        # Check the internal state.
        self.assertEqual(len(self.res.fake_db), 4)
        self.assertEqual(self.res.data, {
            'author': 'daniel',
            'id': 6,
            'title': 'Moved hosts'
        })
