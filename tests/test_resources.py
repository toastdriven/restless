import datetime
import decimal
import unittest

from restless.exceptions import HttpError, NotFound, MethodNotImplemented
from restless.resources import Resource
from restless.utils import json

from .fakes import FakeHttpRequest, FakeHttpResponse


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

    def test_bubble_exceptions(self):
        self.assertFalse(self.res.bubble_exceptions())

    def test_raw_deserialize(self):
        body = '{"title": "Hitchhiker\'s Guide To The Galaxy", "author": "Douglas Adams"}'
        self.assertEqual(self.res.raw_deserialize(body), {
            'author': 'Douglas Adams',
            'title': "Hitchhiker's Guide To The Galaxy",
        })

    def test_raw_serialize(self):
        # This isn't very unit-y, but we're also testing that we're using the
        # right JSON encoder & that it can handle other data types.
        data = {
            'title': 'Cosmos',
            'author': 'Carl Sagan',
            'short_desc': 'A journey through the stars by an emminent astrophysist.',
            'pub_date': datetime.date(1980, 10, 5),
            'price': decimal.Decimal('17.99'),
        }
        res = self.res.raw_serialize(data)
        # Note the keys **don't** get remapped here.
        self.assertEqual(json.loads(res), {
            'author': 'Carl Sagan',
            'price': '17.99',
            'pub_date': '1980-10-05',
            'short_desc': 'A journey through the stars by an emminent astrophysist.',
            'title': 'Cosmos'
        })

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
        }

        self.res.fields = {
            'title': 'title',
            'author': 'author',
            'synopsis': 'short_desc',
        }
        res = self.res.serialize_detail(data)
        self.assertEqual(json.loads(res), {
            'author': 'Carl Sagan',
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
