import unittest
import os
import os.path
import shutil
import tempfile
import time

from cope import FileProcessor, Process, INFILE, OUTFILE

class ProcessFunctionTests(unittest.TestCase):

	def createTree(self, base, files):
		"""Create a set of files under a directory. The list of files is
		   a list of (subpath, contents) tuples """
		for (subpath, contents) in files:
			path = os.path.join(base, subpath)
			os.makedirs(os.path.dirname(path), exist_ok=True)
			with open(path, "w") as f:
				f.write(contents)

	def createInputTree(self, files):
		self.createTree(self.intree, files)
	def createOutputTree(self, files):
		self.createTree(self.outtree, files)

	def contentsOfOutputFile(self, path):
		with open(os.path.join(self.outtree, path)) as f:
			return f.read()

	# ----

	def setUp(self):
		self.tempdir = tempfile.mkdtemp()
		self.intree = os.path.join(self.tempdir, "in")
		self.outtree = os.path.join(self.tempdir, "out")
		os.makedirs(self.intree)
		os.makedirs(self.outtree)

	def tearDown(self):
		shutil.rmtree(self.tempdir)

	# ----

	def test_run(self):
		"""
		Given: a set of input files
		When: a FileProcessor is run with Process.run(commandname, INFILE, OUTFILE)
		Then: the UNIX process specified is executed
		"""
		self.createInputTree([
			("au", "Sydney\nMelbourne\nBrisbane\nPerth\n"),
			("uk", "London\nManchester\nGlasgow\nCardiff\n"),
			("is", "Reykjavík\n")
		])
		proc = FileProcessor(
			self.intree,
			self.outtree,
			lambda name:name,
			Process.run("/usr/bin/sort", "-o", OUTFILE, INFILE)
		)

		log = proc.run()
		self.assertEqual(set(log.processed), {("au", "au"), ("is","is"), ("uk", "uk")})
		self.assertEqual(log.failed, [])
		self.assertEqual(self.contentsOfOutputFile("au"), "Brisbane\nMelbourne\nPerth\nSydney\n")
		self.assertEqual(self.contentsOfOutputFile("uk"), "Cardiff\nGlasgow\nLondon\nManchester\n")
		self.assertEqual(self.contentsOfOutputFile("is"), "Reykjavík\n")

	def test_run_recordFailedResults(self):
		"""
		Given: a FileProcessor configured to run a command with Process.run
		When: the command returns a nonzero result
		Then: the file processing is marked as a failure
		"""
		self.createInputTree([
			("test", "testing")
		])
		proc = FileProcessor(
			self.intree,
			self.outtree,
			lambda name:name,
			Process.run("/bin/false")
		)

		log = proc.run()
		self.assertEqual(log.processed, [])
		self.assertEqual(len(log.failed), 1)
		self.assertEqual(log.failed[0][0], "test")

	def test_captureOutputOf(self):
		"""
		Given: a set of input files
		When: a FileProcessor is run with Process.run(commandname, INFILE, OUTFILE)
		Then: the UNIX process specified is executed
		"""
		self.createInputTree([
			("au", "Sydney\nMelbourne\nBrisbane\nPerth\n"),
			("europe/uk", "London\nManchester\nGlasgow\nCardiff\n"),
			("europe/is", "Reykjavík\n")
		])
		proc = FileProcessor(
			self.intree,
			self.outtree,
			lambda name:name,
			Process.captureOutputOf("/usr/bin/sort", INFILE)
		)

		log = proc.run()
		self.assertEqual(set(log.processed), {("au", "au"), ("europe/is","europe/is"), ("europe/uk", "europe/uk")})
		self.assertEqual(log.failed, [])
		self.assertEqual(self.contentsOfOutputFile("au"), "Brisbane\nMelbourne\nPerth\nSydney\n")
		self.assertEqual(self.contentsOfOutputFile("europe/uk"), "Cardiff\nGlasgow\nLondon\nManchester\n")
		self.assertEqual(self.contentsOfOutputFile("europe/is"), "Reykjavík\n")

	def test_copy(self):
		"""
		Given: a set of input files
		When: a FileProcessor is run with Process.copy
		Then: the files are copied to their destination
		"""
		self.createInputTree([
			("au", "Sydney\nMelbourne\nBrisbane\nPerth\n"),
			("europe/uk", "London\nManchester\nGlasgow\nCardiff\n"),
			("europe/is", "Reykjavík\n")
		])
		proc = FileProcessor(
			self.intree,
			self.outtree,
			lambda name:name,
			Process.copy
		)
		log = proc.run()
		self.assertEqual(set(log.processed), {("au", "au"), ("europe/is","europe/is"), ("europe/uk", "europe/uk")})
		self.assertEqual(log.failed, [])
		self.assertEqual(self.contentsOfOutputFile("au"), "Sydney\nMelbourne\nBrisbane\nPerth\n")
		self.assertNotEqual(os.stat(os.path.join(self.intree, "au")).st_ino, os.stat(os.path.join(self.outtree, "au")).st_ino)
	
	def test_hardLink(self):
		"""
		Given: a set of input files
		When: a FileProcessor is run with Process.copy
		Then: the files are copied to their destination
		"""
		self.createInputTree([
			("au", "Sydney\nMelbourne\nBrisbane\nPerth\n"),
			("europe/uk", "London\nManchester\nGlasgow\nCardiff\n"),
			("europe/is", "Reykjavík\n")
		])
		proc = FileProcessor(
			self.intree,
			self.outtree,
			lambda name:name,
			Process.hardLink
		)
		log = proc.run()
		self.assertEqual(set(log.processed), {("au", "au"), ("europe/is","europe/is"), ("europe/uk", "europe/uk")})
		self.assertEqual(log.failed, [])
		self.assertEqual(self.contentsOfOutputFile("au"), "Sydney\nMelbourne\nBrisbane\nPerth\n")
		self.assertEqual(os.stat(os.path.join(self.intree, "au")).st_ino, os.stat(os.path.join(self.outtree, "au")).st_ino)
	