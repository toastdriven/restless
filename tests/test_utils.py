import sys
import unittest

from restless.utils import format_traceback


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
            self.assertGreater(len(lines), 3)
            self.assertEqual(lines[-1], 'ValueError: Because we need an exception.')
