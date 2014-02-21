import sys
import unittest

from restless.utils import lookup_data, format_traceback


class InstaObj(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class LookupDataTestCase(unittest.TestCase):
    def setUp(self):
        super(LookupDataTestCase, self).setUp()
        self.obj_data = InstaObj(
            say='what',
            count=453,
            moof={
                'buried': {
                    'id': 7,
                    'data': InstaObj(yes='no')
                }
            }
        )
        self.dict_data = {
            'hello': 'world',
            'abc': 123,
            'more': {
                'things': 'here',
                'nested': InstaObj(
                    awesome=True,
                    depth=3
                ),
            },
        }

    def test_dict_simple(self):
        self.assertEqual(lookup_data('hello', self.dict_data), 'world')
        self.assertEqual(lookup_data('abc', self.dict_data), 123)

    def test_obj_simple(self):
        self.assertEqual(lookup_data('say', self.obj_data), 'what')
        self.assertEqual(lookup_data('count', self.obj_data), 453)

    def test_dict_nested(self):
        self.assertEqual(lookup_data('more.things', self.dict_data), 'here')
        self.assertEqual(lookup_data('more.nested.depth', self.dict_data), 3)

    def test_obj_nested(self):
        self.assertEqual(lookup_data('moof.buried.id', self.obj_data), 7)
        self.assertEqual(lookup_data('moof.buried.data.yes', self.obj_data), 'no')

    def test_dict_miss(self):
        with self.assertRaises(KeyError):
            lookup_data('another', self.dict_data)

    def test_obj_miss(self):
        with self.assertRaises(AttributeError):
            lookup_data('whee', self.obj_data)

    def test_empty_lookup(self):
        # We could possibly get here in the recursion.
        self.assertEqual(lookup_data('', 'Last value'), 'Last value')

    def test_complex_miss(self):
        with self.assertRaises(AttributeError):
            lookup_data('more.nested.nope', self.dict_data)


class FormatTracebackTestCase(unittest.TestCase):
    def test_format_traceback(self):
        try:
            raise ValueError("Because we need an exception.")
        except:
            exc_info = sys.exc_info()
            result = format_traceback(exc_info)
            self.assertTrue(result.startswith('Traceback (most recent call last):\n'))
            self.assertFalse(result.endswith('\n'))
            lines = result.split('\n')
            self.assertTrue(len(lines) > 3)
            self.assertEqual(lines[-1], 'ValueError: Because we need an exception.')
