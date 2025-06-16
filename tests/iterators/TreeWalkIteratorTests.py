import unittest
import tempfile
import os.path
import shutil

from cope.iterators.treewalk import TreeWalkIterator

class TreeWalkIteratorTests(unittest.TestCase):

	def createTree(self, base, files):
		"""Create a set of files under a directory. The list of files is
		   a list of (subpath, contents) tuples """
		for (subpath, contents) in files:
			path = os.path.join(base, subpath)
			os.makedirs(os.path.dirname(path), exist_ok=True)
			with open(path, "w") as f:
				f.write(contents)

	def setUp(self):
		self.tempdir = tempfile.mkdtemp()
#		os.makedirs(self.tempdir)

	def tearDown(self):
		shutil.rmtree(self.tempdir)

	def test_walk(self):
		self.createTree(self.tempdir, [
			("a0001/bcd/jk", ''),
			("a0001/bcd/jm", ''),
			("a0001/bce/jk", ''),
			("a0002/abc", ''),
			("b", '')
		])
		iter = TreeWalkIterator()(self.tempdir)
		iterated = [f for f in iter]
		iterated.sort()
		self.assertEqual(iterated, ["a0001/bcd/jk", "a0001/bcd/jm", "a0001/bce/jk", "a0002/abc", "b"])

