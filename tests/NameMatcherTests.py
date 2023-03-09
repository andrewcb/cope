import unittest
from cope import NameMatcher

class NameMatcherTests(unittest.TestCase):
	def test_endswith(self):
		self.assertTrue(NameMatcher.endswith(".tar.gz", ".tar.bz2")("foo.tar.gz"))
		self.assertTrue(NameMatcher.endswith(".tar")("foo.tar"))
		self.assertFalse(NameMatcher.endswith(".tar")("foo.tar.gz"))