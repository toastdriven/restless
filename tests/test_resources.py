import datetime
import decimal
import unittest

# Ugh. Settings for Django.
from django.conf import settings
settings.configure(DEBUG=True)

# Ugh. Globals for Flask.
import flask

from restless.dj import DjangoResource
from restless.exceptions import HttpError, NotFound, MethodNotImplemented, Unauthorized
from restless.fl import FlaskResource
from restless.resources import Resource
from restless.utils import json


class FakeHttpRequest(object):
    def __init__(self, method='GET', body=''):
        self.method = method.upper()
        self.body = body


class FakeHttpResponse(object):
    def __init__(self, body, content_type='text/html'):
        self.body = body
        self.content_type = content_type
        self.status_code = 200


class NonDjangoResource(Resource):
    # Because the default implementation is a tiny-bit Django-specific,
    # we're faking some things here.
    def build_response(self, data, status=200):
        resp = FakeHttpResponse(data, content_type='application/json')
        resp.status_code = status
        return resp


class ResourceTestCase(unittest.TestCase):
    resource_class = NonDjangoResource

    def setUp(self):
        super(ResourceTestCase, self).setUp()
        self.res = self.resource_class()
        # Assign here, since we typically won't be entering through
        # ``as_list/as_detail`` methods like normal flow.
        self.res.request = FakeHttpRequest()

    def test_init(self):
        res = self.resource_class('abc', test=True)
        self.assertEqual(res.init_args, ('abc',))
        self.assertEqual(res.init_kwargs, {'test': True})
        self.assertEqual(res.request, None)
        self.assertEqual(res.data, None)
        self.assertEqual(res.status, 200)

    def test_request_method(self):
        self.assertEqual(self.res.request_method(), 'GET')

        self.res.request = FakeHttpRequest('POST', '{"hello": "world"}')
        self.assertEqual(self.res.request_method(), 'POST')

        self.res.request = FakeHttpRequest('PUT', '{"hello": "world"}')
        self.assertEqual(self.res.request_method(), 'PUT')

        self.res.request = FakeHttpRequest('DELETE', '')
        self.assertEqual(self.res.request_method(), 'DELETE')

    def test_request_body(self):
        self.assertEqual(self.res.request_body(), '')

        self.res.request = FakeHttpRequest('POST', '{"hello": "world"}')
        self.assertEqual(self.res.request_body(), '{"hello": "world"}')

        self.res.request = FakeHttpRequest('PUT', '{"hello": "world"}')
        self.assertEqual(self.res.request_body(), '{"hello": "world"}')

        self.res.request = FakeHttpRequest('DELETE', '{}')
        self.assertEqual(self.res.request_body(), '{}')

    def test_build_response(self):
        resp = self.res.build_response('Hello, world!')
        self.assertEqual(resp.body, 'Hello, world!')
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.status_code, 200)

        resp = self.res.build_response('{"hello": "world"}', status=302)
        self.assertEqual(resp.body, '{"hello": "world"}')
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.status_code, 302)

    def test_build_error(self):
        err = HttpError("Whoopsie")
        resp = self.res.build_error(err)
        resp_body = json.loads(resp.body)
        self.assertEqual(resp_body, {'error': 'Whoopsie'})
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.status_code, 500)

        nf_err = NotFound()
        resp = self.res.build_error(nf_err)
        resp_body = json.loads(resp.body)
        # Default error message.
        self.assertEqual(resp_body, {'error': 'Resource not found.'})
        self.assertEqual(resp.content_type, 'application/json')
        # Custom status code.
        self.assertEqual(resp.status_code, 404)

        # Non-restless exception.
        unknown_err = AttributeError("'something' not found on the object.")
        resp = self.res.build_error(unknown_err)
        resp_body = json.loads(resp.body)
        # Still gets the JSON treatment & an appropriate status code.
        self.assertEqual(resp_body, {'error': "'something' not found on the object."})
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.status_code, 500)

    def test_is_debug(self):
        self.assertFalse(self.res.is_debug())

    def test_deserialize(self):
        list_body = '["one", "three", "two"]'
        self.assertEqual(self.res.deserialize('POST', 'list', list_body), [
            "one",
            "three",
            "two",
        ])

        # Should select list.
        self.assertEqual(self.res.deserialize('POST', 'list', ''), [])
        # Should select detail.
        self.assertEqual(self.res.deserialize('PUT', 'detail', ''), {})

    def test_deserialize_list(self):
        body = '["one", "three", "two"]'
        self.assertEqual(self.res.deserialize_list(body), [
            "one",
            "three",
            "two",
        ])

        self.assertEqual(self.res.deserialize_list(''), [])

    def test_deserialize_detail(self):
        body = '{"title": "Hitchhiker\'s Guide To The Galaxy", "author": "Douglas Adams"}'
        self.assertEqual(self.res.deserialize_detail(body), {
            'author': 'Douglas Adams',
            'title': "Hitchhiker's Guide To The Galaxy",
        })

        self.assertEqual(self.res.deserialize_detail(''), {})

    def test_serialize(self):
        list_data = ['a', 'c', 'b']
        detail_data = {'hello': 'world'}

        # Normal calls.
        self.assertEqual(self.res.serialize('GET', 'list', list_data), '{"objects": ["a", "c", "b"]}')
        self.assertEqual(self.res.serialize('GET', 'detail', detail_data), '{"hello": "world"}')
        # The create special-case.
        self.assertEqual(self.res.serialize('POST', 'list', detail_data), '{"hello": "world"}')
        # Make sure other methods aren't special-cased.
        self.assertEqual(self.res.serialize('PUT', 'list', list_data), '{"objects": ["a", "c", "b"]}')

    def test_serialize_list(self):
        data = [
            {
                'title': 'Cosmos',
                'author': 'Carl Sagan',
                'short_desc': 'A journey through the stars by an emminent astrophysist.',
                'pub_date': '1980',
            },
            {
                'title': "Hitchhiker's Guide To The Galaxy",
                'author': 'Douglas Adams',
                'short_desc': "Don't forget your towel.",
                'pub_date': '1979',
            }
        ]

        self.res.fields = {
            'title': 'title',
            'author': 'author',
            'synopsis': 'short_desc',
        }
        res = self.res.serialize_list(data)
        self.assertEqual(json.loads(res), {
            'objects': [
                {
                    'author': 'Carl Sagan',
                    'synopsis': 'A journey through the stars by an emminent astrophysist.',
                    'title': 'Cosmos'
                },
                {
                    'title': "Hitchhiker's Guide To The Galaxy",
                    'author': 'Douglas Adams',
                    'synopsis': "Don't forget your towel.",
                },
            ],
        })

        # Make sure we don't try to serialize a ``None``, which would fail.
        self.assertEqual(self.res.serialize_list(None), '')

    def test_serialize_detail(self):
        # This isn't very unit-y, but we're also testing that we're using the
        # right JSON encoder & that it can handle other data types.
        data = {
            'title': 'Cosmos',
            'author': 'Carl Sagan',
            'short_desc': 'A journey through the stars by an emminent astrophysist.',
            'pub_date': datetime.date(1980, 10, 5),
            'price': decimal.Decimal('17.99'),
        }

        self.res.fields = {
            'title': 'title',
            'author': 'author',
            'synopsis': 'short_desc',
            'published': 'pub_date',
            'price': 'price',
        }
        res = self.res.serialize_detail(data)
        self.assertEqual(json.loads(res), {
            'author': 'Carl Sagan',
            'price': '17.99',
            'published': '1980-10-05',
            'synopsis': 'A journey through the stars by an emminent astrophysist.',
            'title': 'Cosmos'
        })

        # Make sure we don't try to serialize a ``None``, which would fail.
        self.assertEqual(self.res.serialize_detail(None), '')

    def test_prepare(self):
        # Without fields.
        data = {
            'title': 'Cosmos',
            'author': 'Carl Sagan',
            'short_desc': 'A journey through the stars by an emminent astrophysist.',
            'pub_date': '1980'
        }

        # Should be unmodified.
        self.assertEqual(self.res.fields, None)
        self.assertEqual(self.res.prepare(data), data)

        self.res.fields = {
            'title': 'title',
            'author': 'author',
            'synopsis': 'short_desc',
        }
        self.assertEqual(self.res.prepare(data), {
            'author': 'Carl Sagan',
            'synopsis': 'A journey through the stars by an emminent astrophysist.',
            'title': 'Cosmos'
        })

    def test_wrap_list_response(self):
        data = ['one', 'three', 'two']
        self.assertEqual(self.res.wrap_list_response(data), {
            'objects': [
                'one',
                'three',
                'two',
            ],
        })

    def test_is_authenticated(self):
        # By default, only GETs are allowed.
        self.assertTrue(self.res.is_authenticated())

        self.res.request = FakeHttpRequest('POST')
        self.assertFalse(self.res.is_authenticated())

        self.res.request = FakeHttpRequest('PUT')
        self.assertFalse(self.res.is_authenticated())

        self.res.request = FakeHttpRequest('DELETE')
        self.assertFalse(self.res.is_authenticated())

    def test_list(self):
        with self.assertRaises(MethodNotImplemented):
            self.res.list()

    def test_detail(self):
        with self.assertRaises(MethodNotImplemented):
            self.res.detail()

    def test_create(self):
        with self.assertRaises(MethodNotImplemented):
            self.res.create()

    def test_update(self):
        with self.assertRaises(MethodNotImplemented):
            self.res.update()

    def test_delete(self):
        with self.assertRaises(MethodNotImplemented):
            self.res.delete()

    def test_update_list(self):
        with self.assertRaises(MethodNotImplemented):
            self.res.update_list()

    def test_create_detail(self):
        with self.assertRaises(MethodNotImplemented):
            self.res.create_detail()

    def test_delete_list(self):
        with self.assertRaises(MethodNotImplemented):
            self.res.delete_list()


class FakeModel(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


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
                    'id': 5, 'title': 'Last'
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
        # The Flask testing docs talk about this, but I can't get it to work.
        # Help please?
        # self.app = app.test_client()

        # Just for the fake data.
        self.res.fake_init()

    @unittest.skipIf(True, "Flask tests are broken & I'm not an expert on how to get the globals cooperating. :(")
    def test_as_list(self):
        list_endpoint = FlTestResource.as_list()
        flask.request = FakeHttpRequest('GET')

        resp = list_endpoint()
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
                    'id': 5, 'title': 'Last'
                }
            ]
        })

    @unittest.skipIf(True, "Flask tests are broken & I'm not an expert on how to get the globals cooperating. :(")
    def test_as_detail(self):
        detail_endpoint = FlTestResource.as_detail()
        flask.request = FakeHttpRequest('GET')

        resp = detail_endpoint(4)
        self.assertEqual(resp['Content-Type'], 'application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content.decode('utf-8')), {
            'author': 'daniel',
            'body': 'Stuff here.',
            'id': 4,
            'title': 'Another'
        })

    @unittest.skipIf(True, "Flask tests are broken & I'm not an expert on how to get the globals cooperating. :(")
    def test_build_response(self):
        resp = self.res.build_response('Hello, world!', status=302)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.headers['Content-Type'], 302)
        self.assertEqual(resp.read(), 'Hello, world!')

    @unittest.skipIf(True, "Flask tests are broken & I'm not an expert on how to get the globals cooperating. :(")
    def test_add_url_rules(self):
        FlTestResource.add_url_rules(self.app, '/api/')
        self.assertEqual(len(self.app.url_map), 2)
        self.assertEqual(patterns[0].name, 'api_djtest_list')
        self.assertEqual(patterns[1].name, 'api_djtest_detail')

        FlTestResource.add_url_rules(self.app, '/api/', endpoint_prefix='v2_tests')
        self.assertEqual(len(patterns), 2)
        self.assertEqual(patterns[0].name, 'v2_tests_list')
        self.assertEqual(patterns[1].name, 'v2_tests_detail')
