import unittest

if not hasattr(unittest.TestCase, 'addCleanup'):
    raise Exception("You're likely running Python 2.6. Please test on a newer version of Python.")
