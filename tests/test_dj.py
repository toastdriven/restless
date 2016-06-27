import unittest

from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist

# Ugh. Settings for Django.
from django.conf import settings
settings.configure(DEBUG=True)

from restless.dj import DjangoResource
from restless.exceptions import Unauthorized
from restless.preparers import FieldsPreparer
from restless.resources import skip_prepare
from restless.utils import json

from .fakes import FakeHttpRequest, FakeModel


class DjTestResource(DjangoResource):
    preparer = FieldsPreparer(fields={
        'id': 'id',
        'title': 'title',
        'author': 'username',
        'body': 'content'
    })
    fake_db = []

    def __init__(self, *args, **kwargs):
        super(DjTestResource, self).__init__(*args, **kwargs)

        self.http_methods.update({
            'schema': {
                'GET': 'schema',
            }
        })

    def fake_init(self):
        # Just for testing.
        self.__class__.fake_db = [
            FakeModel(
                id=2,
                title='First post',
                username='daniel',
                content='Hello world!'),
            FakeModel(
                id=4,
                title='Another',
                username='daniel',
                content='Stuff here.'),
            FakeModel(id=5, title='Last', username='daniel', content="G'bye!"),
        ]

    def is_authenticated(self):
        if self.request_method() == 'DELETE' and self.endpoint == 'list':
            return False

        return True

    def list(self):
        return self.fake_db

    def detail(self, pk):
        for item in self.fake_db:
            if item.id == pk:
                return item

        # If it wasn't found in our fake DB, raise a Django-esque exception.
        raise ObjectDoesNotExist("Model with pk {0} not found.".format(pk))

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

    def delete(self, pk):
        for i, item in enumerate(self.fake_db):
            if item.id == pk:
                del self.fake_db[i]
                return

    @skip_prepare
    def schema(self):
        # A WILD SCHEMA VIEW APPEARS!
        return {
            'fields': {
                'id': {
                    'type': 'integer',
                    'required': True,
                    'help_text': 'The unique id for the post',
                },
                'title': {
                    'type': 'string',
                    'required': True,
                    'help_text': "The post's title",
                },
                'author': {
                    'type': 'string',
                    'required': True,
                    'help_text': 'The username of the author of the post',
                },
                'body': {
                    'type': 'string',
                    'required': False,
                    'default': '',
                    'help_text': 'The content of the post',
                }
            },
            'format': 'application/json',
            'allowed_list_http_methods': ['GET', 'POST'],
            'allowed_detail_http_methods': ['GET', 'PUT', 'DELETE'],
        }


class DjTestResourceHttp404Handling(DjTestResource):
    def detail(self, pk):
        for item in self.fake_db:
            if item.id == pk:
                return item

        # If it wasn't found in our fake DB, raise a Django-esque exception.
        raise Http404("Model with pk {0} not found.".format(pk))


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

    def test_as_view(self):
        # This would be hooked up via the URLconf...
        schema_endpoint = DjTestResource.as_view('schema')
        req = FakeHttpRequest('GET')

        resp = schema_endpoint(req)
        self.assertEqual(resp['Content-Type'], 'application/json')
        self.assertEqual(resp.status_code, 200)
        schema = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(
            sorted(list(schema['fields'].keys())),
            [
                'author',
                'body',
                'id',
                'title',
            ]
        )
        self.assertEqual(schema['fields']['id']['type'], 'integer')
        self.assertEqual(schema['format'], 'application/json')

    def test_handle_not_implemented(self):
        self.res.request = FakeHttpRequest('TRACE')

        resp = self.res.handle('list')
        self.assertEqual(resp['Content-Type'], 'application/json')
        self.assertEqual(resp.status_code, 501)
        resp_json = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(
            resp_json['error'], "Unsupported method 'TRACE' for list endpoint.")
        self.assertTrue('traceback' in resp_json)

    def test_handle_not_authenticated(self):
        # Special-cased above for testing.
        self.res.request = FakeHttpRequest('DELETE')

        # First with DEBUG on
        resp = self.res.handle('list')
        self.assertEqual(resp['Content-Type'], 'application/json')
        self.assertEqual(resp.status_code, 401)
        resp_json = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(resp_json['error'], 'Unauthorized.')
        self.assertTrue('traceback' in resp_json)

        # Now with DEBUG off.
        settings.DEBUG = False
        self.addCleanup(setattr, settings, 'DEBUG', True)
        resp = self.res.handle('list')
        self.assertEqual(resp['Content-Type'], 'application/json')
        self.assertEqual(resp.status_code, 401)
        resp_json = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(resp_json, {
            'error': 'Unauthorized.',
        })
        self.assertFalse('traceback' in resp_json)

        # Last, with bubble_exceptions.
        class Bubbly(DjTestResource):
            def bubble_exceptions(self):
                return True

        with self.assertRaises(Unauthorized):
            bubb = Bubbly()
            bubb.request = FakeHttpRequest('DELETE')
            bubb.handle('list')

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

    def test_object_does_not_exist(self):
        # Make sure we get a proper Not Found exception rather than a
        # generic 500, when code raises a ObjectDoesNotExist exception.
        self.res.request = FakeHttpRequest('GET')
        settings.DEBUG = False
        self.addCleanup(setattr, settings, 'DEBUG', True)

        resp = self.res.handle('detail', 1001)
        self.assertEqual(resp['Content-Type'], 'application/json')
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(json.loads(resp.content.decode('utf-8')), {
            'error': 'Model with pk 1001 not found.'
        })

    def test_http404_exception_handling(self):
        # Make sure we get a proper Not Found exception rather than a
        # generic 500, when code raises a Http404 exception.
        res = DjTestResourceHttp404Handling()
        res.request = FakeHttpRequest('GET')
        settings.DEBUG = False
        self.addCleanup(setattr, settings, 'DEBUG', True)

        resp = res.handle('detail', 1001)
        self.assertEqual(resp['Content-Type'], 'application/json')
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(json.loads(resp.content.decode('utf-8')), {
            'error': 'Model with pk 1001 not found.'
        })

    def test_build_url_name(self):
        self.assertEqual(
            DjTestResource.build_url_name('list'),
            'api_djtest_list'
        )
        self.assertEqual(
            DjTestResource.build_url_name('detail'),
            'api_djtest_detail'
        )
        self.assertEqual(
            DjTestResource.build_url_name('schema'),
            'api_djtest_schema'
        )

        self.assertEqual(
            DjTestResource.build_url_name('list', name_prefix='v2_'),
            'v2_list'
        )
        self.assertEqual(
            DjTestResource.build_url_name('detail', name_prefix='v2_'),
            'v2_detail'
        )
        self.assertEqual(
            DjTestResource.build_url_name('schema', name_prefix='v2_'),
            'v2_schema'
        )

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
        self.res.request = FakeHttpRequest(
            'POST',
            body='{"id": 6, "title": "Moved hosts", "author": "daniel"}')
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

    def test_delete(self):
        self.res.request = FakeHttpRequest('DELETE')
        self.assertEqual(len(self.res.fake_db), 3)

        resp = self.res.handle('detail', pk=2)
        self.assertEqual(resp['Content-Type'], 'text/plain')
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.content.decode('utf-8'), '')

        # Check the internal state.
        self.res.request = FakeHttpRequest('GET')
        self.assertEqual(len(self.res.fake_db), 2)
        resp = self.res.handle('detail', pk=2)
        self.assertEqual(resp.status_code, 404)
