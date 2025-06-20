import unittest
import tempfile
import os.path
import shutil

from cope.iterators.directorytree import DirectoryTreeIterator

class DirectoryTreeIteratorTests(unittest.TestCase):

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
		iter = DirectoryTreeIterator()(self.tempdir)
		iterated = [f for f in iter]
		self.assertEqual(iterated, ["a0001/bcd/jk", "a0001/bcd/jm", "a0001/bce/jk", "a0002/abc", "b"])

	def test_include_dir(self):
		self.createTree(self.tempdir, [
			("a0001/bcd/jk", ''),
			("a0001/bcd/jm", ''),
			("a0001/bce/jk", ''),
			("a0002/abc", ''),
			("b", ''),
			(".DS_STORE/foo", '')
		])
		iter = DirectoryTreeIterator(include_dir=lambda s:s[0] != '.')(self.tempdir)
		iterated = [f for f in iter]
		self.assertEqual(iterated, ["a0001/bcd/jk", "a0001/bcd/jm", "a0001/bce/jk", "a0002/abc", "b"])

	def test_walk_with_start(self):
		self.createTree(self.tempdir, [
			('Australia/Melbourne', ''),
			('Australia/Sydney', ''),
			('Canada/Montreal', ''),
			('Canada/Vancouver', ''),
			('Denmark/Copenhagen', ''),
			('Estonia/Tallinn', ''),
			('France/Marseille', ''),
			('France/Paris', ''),

		])
		iter = DirectoryTreeIterator()(self.tempdir, start="Canada/Vancouver")
		iterated = [f for f in iter]
		self.assertEqual(iterated, ["Canada/Vancouver", "Denmark/Copenhagen", "Estonia/Tallinn", "France/Marseille", "France/Paris"])

	def test_walk_with_stop(self):
		self.createTree(self.tempdir, [
			('Australia/Melbourne', ''),
			('Australia/Sydney', ''),
			('Canada/Montreal', ''),
			('Canada/Vancouver', ''),
			('Denmark/Copenhagen', ''),
			('Estonia/Tallinn', ''),
			('France/Marseille', ''),
			('France/Paris', ''),

		])
		iter = DirectoryTreeIterator()(self.tempdir, stop="Denmark/Copenhagen")
		iterated = [f for f in iter]
		self.assertEqual(iterated, ["Australia/Melbourne", "Australia/Sydney", "Canada/Montreal", "Canada/Vancouver", "Denmark/Copenhagen"])


	def test_walk_with_limit_to(self):
		self.createTree(self.tempdir, [
			("Australia/NSW/Newcastle", ""),
			("Australia/NSW/Sydney", ""),
			("Australia/VIC/Ballarat", ""),
			("Australia/VIC/Bendigo", ""),
			("Australia/VIC/Melbourne", ""),
			("EU/DE/Berlin", ""),
			("EU/DE/Hamburg", ""),
			("EU/ES/Barcelona", ""),
			("EU/ES/Madrid", ""),
			("EU/FR/Paris", ""),
			("EU/SE/Stockholm", ""),
			("US/CA/San Francisco", ""),
			("US/WA/Seattle", "")
		])

		self.assertEqual(
			[i for i in DirectoryTreeIterator()(self.tempdir, limit_to="Australia/VIC")],
			["Australia/VIC/Ballarat", "Australia/VIC/Bendigo", "Australia/VIC/Melbourne"]
		)
		self.assertEqual(
			[i for i in DirectoryTreeIterator()(self.tempdir, limit_to="Australia")],
			["Australia/NSW/Newcastle", "Australia/NSW/Sydney", "Australia/VIC/Ballarat", "Australia/VIC/Bendigo", "Australia/VIC/Melbourne"]
		)
		self.assertEqual(
			[i for i in DirectoryTreeIterator()(self.tempdir, limit_to="EU/FR")],
			["EU/FR/Paris"]
		)
