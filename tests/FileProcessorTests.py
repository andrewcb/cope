import unittest
import os.path
import shutil
import tempfile
import time

from cope import FileProcessor, Process, NameMatcher

class FileProcessorTests(unittest.TestCase):

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
	
	def test_runNew(self):
		"""Given a directory of input files and naming processing functions,
		   When the FileProcessor is run,
		   Then the appropriately named output files should be created in the output directory, with correct contents, and the run log should contain their details
		"""
		self.createInputTree([
			("01/20.aa", "asdfgh"),
			("01/21.ab", "qwasds"),
			("02/11.aa", "oooppp"),
		])
		def destname(inname):
			return "".join(inname.split("/"))

		proc = FileProcessor(
			self.intree, 
			self.outtree, 
			Process.hardLink,
			destname,
			includename=NameMatcher.endswith(".aa"))

		log = proc.run()
		self.assertEqual(set(log.processed), {("01/20.aa", "0120.aa"), ("02/11.aa", "0211.aa")})
		self.assertEqual(log.already_present, [])
		self.assertEqual(log.unnameable, [])
		self.assertEqual(self.contentsOfOutputFile("0120.aa"), "asdfgh")
		self.assertEqual(self.contentsOfOutputFile("0211.aa"), "oooppp")
			
	def test_rerunDoesNotReprocessHandledFiles(self):
		"""
		Given an input directory of files and an output directory containing some files previously derived from these by FileProcessor,
		When FileProcessor is run on these again
		Then the previously handled, unmodified files should not be reprocessed, but newly added or modified files should be
		"""
		self.createInputTree([
			("01/20.aa", "asdfgh"),
			("01/21.ab", "qwasds"),
			("02/11.aa", "oooppp\n1"),
		])
		inbase = self.intree
		def destname(inname):
			(stem,ext) = os.path.splitext(inname)
			with open(os.path.join(inbase, inname)) as f:
				return "".join(stem.split("/")) + '/' + f.readline().strip() + ext
		def process(src, dst):
			with open(src) as fi:
				with open(dst, 'w') as fo:
					fo.write(fi.read())
		proc = FileProcessor(
			self.intree, self.outtree, process, destname,
			includename=lambda fn: fn.endswith(".aa"))

		# run 1
		log1 = proc.run()
		self.assertEqual(set(log1.processed), {("01/20.aa", "0120/asdfgh.aa"), ("02/11.aa", "0211/oooppp.aa")})
		self.assertEqual(log1.already_present, [])
		self.assertEqual(log1.unnameable, [])
		ts1_1 = os.path.getmtime(os.path.join(self.outtree, "0120/asdfgh.aa"))
		ts3_1 = os.path.getmtime(os.path.join(self.outtree, "0211/oooppp.aa"))

		# run 2
		time.sleep(0.01)
		self.createInputTree([
			("01/22.aa", "zxcvbn"),
			("02/11.aa", "oooppp\n2"),
		])
		log2 = proc.run()
		ts1_2 = os.path.getmtime(os.path.join(self.outtree, "0120/asdfgh.aa"))
		ts3_2 = os.path.getmtime(os.path.join(self.outtree, "0211/oooppp.aa"))
		self.assertEqual(set(log2.processed), {("01/22.aa", "0122/zxcvbn.aa"), ("02/11.aa", "0211/oooppp.aa")})
		self.assertEqual(log2.already_present, [("01/20.aa", "0120/asdfgh.aa")])
		self.assertEqual(log2.unnameable, [])
		self.assertEqual(ts1_1, ts1_2)
		self.assertNotEqual(ts3_1, ts3_2)
		self.assertEqual(self.contentsOfOutputFile("0211/oooppp.aa"), "oooppp\n2")
		
	def test_dryRunReturnsLogButDoesNotModifyFiles(self):
		"""
		Given a directory of input files
		When FileProcessor is run with dry_run=true
		Then no actual processing should take place, but the files that would have been processed should be returned as such in its log
		"""
		self.createInputTree([
			("01/20.aa", "asdfgh"),
			("01/21.ab", "qwasds"),
			("02/11.aa", "oooppp\n1"),
		])
		def destname(inname):
			return "".join(inname.split("/"))

		proc = FileProcessor(
			self.intree, 
			self.outtree, 
			Process.hardLink,
			destname,
			includename=lambda fn: fn.endswith(".aa"))

		log = proc.run(dry_run=True)
		self.assertEqual(set(log.processed), {("01/20.aa", "0120.aa"), ("02/11.aa", "0211.aa")})
		self.assertEqual(log.already_present, [])
		self.assertEqual(log.unnameable, [])
		self.assertEqual(os.listdir(self.outtree), [".copemetadata"])
		
	def test_nullFileNameNotCopied(self):
		"""
		Given a directory tree of input files
		When the function for naming output files returns None for one of the input names
		Then that file should be omitted from processing without error, but listed as unnameable
		"""
		self.createInputTree([
			("01/20.aa", "asdfgh"),
			("01/21.ab", "qwasds"),
			("02/11.aa", "oooppp\n1"),
		])
		def destname(inname):
			return inname.endswith(".aa") and "".join(inname.split("/"))

		proc = FileProcessor(
			self.intree, 
			self.outtree,
			Process.hardLink,
			destname
		)
		log = proc.run(dry_run=False)
		self.assertEqual(set(log.processed), {("01/20.aa", "0120.aa"), ("02/11.aa", "0211.aa")})
		self.assertEqual(log.already_present, [])
		self.assertEqual(log.unnameable, ["01/21.ab"])

	def test_handlesExceptionInProcess(self):
		"""
		Given a set of input files
		When the processing function raises an exception in the handling of a file
		Then that file should be logged as failed, but processing should continue
		"""
		self.createInputTree([
			("01/20.aa", "asdfgh"),
			("01/21.ab", "qwasds"),
			("02/11.aa", "oooppp\n1"),
		])
		def destname(inname):
			return "".join(inname.split("/"))
		def process(src,dst):
			if not src.endswith(".aa"):
				raise Exception(":-/")
			os.link(src,dst)
		proc = FileProcessor(
			self.intree, 
			self.outtree, 
			process,
			destname
		)
		log = proc.run(dry_run=False)
		self.assertEqual(set(log.processed), {("01/20.aa", "0120.aa"), ("02/11.aa", "0211.aa")})
		self.assertEqual(log.already_present, [])
		self.assertEqual(log.unnameable, [])
		#self.assertEqual(log.failed, [("01/21.ab", Exception(":-/"))])
		self.assertEqual(len(log.failed), 1)
		self.assertEqual(log.failed[0][0], "01/21.ab")

	def test_onprogress(self):
		"""
		Given an appropriately configured FileProcessor with an onprogress function specified
		When it is run 
		Then the onprogress function should be called for each file examined, with the correct values being passed
		"""
		self.createInputTree([
			("01/20.aa", "asdfgh"),
			("01/21.ab", "qwasds"),
			("02/11.aa", "oooppp"),
		])
		def destname(inname):
			return inname.endswith(".aa") and "".join(inname.split("/"))

		onprogress_results = []
		def onprogress(*args):
			onprogress_results.append(tuple(args))

		proc = FileProcessor(
			self.intree, 
			self.outtree, 
			Process.copy,
			destname,
			onprogress=onprogress
		)
		proc.run(dry_run=False)
		self.assertEqual(set(onprogress_results), {
			(FileProcessor.ProgressType.PROCESSED, "01/20.aa", "0120.aa"),
			(FileProcessor.ProgressType.UNNAMEABLE, "01/21.ab", None),
			(FileProcessor.ProgressType.PROCESSED, "02/11.aa", "0211.aa"),
		})
		onprogress_results = []
		self.createInputTree([
			("01/22.aa", "zxcvbn"),
			("02/11.aa", "oooppp\n2"),
		])
		proc.run()
		time.sleep(0.01)
		self.assertEqual(set(onprogress_results), {
			(FileProcessor.ProgressType.ALREADY_PRESENT, "01/20.aa", "0120.aa"),
			(FileProcessor.ProgressType.UNNAMEABLE, "01/21.ab", None),
			(FileProcessor.ProgressType.PROCESSED, "01/22.aa", "0122.aa"),
			(FileProcessor.ProgressType.PROCESSED, "02/11.aa", "0211.aa"),
		})


	def test_heedMaxItems(self):
		"""
		Given an appropriately configured FileProcessor
		When it is run with max_items specified
		Then only that many items at most should be processed
		"""
		self.createInputTree([
			("01/20.aa", "asdfgh"),
			("01/21.ab", "qwasds"),
			("02/11.aa", "oooppp"),
		])
		def destname(inname):
			return "".join(inname.split("/"))

		proc = FileProcessor(
			self.intree, 
			self.outtree, 
			Process.hardLink,
			destname
		)

		log1 = proc.run(max_items=2)
		#self.assertEqual(set(log1.processed), {("01/20.aa", "0120.aa"), ("01/21.ab", "0121.ab")})
		self.assertEqual(len(log1.processed), 2)
		self.assertEqual(log1.already_present, [])
		self.assertEqual(log1.unnameable, [])

		log2 = proc.run(max_items=2)
		self.assertEqual(len(log2.processed), 1)
		self.assertEqual(set(log1.processed), set(log2.already_present))
		self.assertEqual(set(log1.processed+log2.processed), {
			("01/20.aa", "0120.aa"), 
			("01/21.ab", "0121.ab"), 
			("02/11.aa", "0211.aa")
		})

	def test_customIterator(self):
		"""
		Given a FileProcessor with a custom directory iterator
		When it is run
		Then
		  - the files selected for processing are only those returned by the iterator which exist
		  - any files returned by the iterator which turn out to not exist are skipped
		"""
		self.createInputTree([
			('INDEX', "01/20.aa\n99/nonexistent.xx\n02/11.aa\n"),
			("01/20.aa", "asdfgh"),
			("01/21.ab", "qwasds"),
			("02/11.aa", "oooppp"),
		])
		def destname(inname):
			return "".join(inname.split("/"))

		def iterator(path):
			with open(os.path.join(path,"INDEX")) as f:
				for line in f.readlines():
					yield line[:-1]


		proc = FileProcessor(
			self.intree, 
			self.outtree, 
			Process.hardLink,
			destname,
			iterator=iterator)

		log = proc.run()
		self.assertEqual(set(log.processed), {("01/20.aa", "0120.aa"), ("02/11.aa", "0211.aa")})
		self.assertEqual(log.already_present, [])
		self.assertEqual(log.unnameable, [])
		self.assertEqual(self.contentsOfOutputFile("0120.aa"), "asdfgh")
		self.assertEqual(self.contentsOfOutputFile("0211.aa"), "oooppp")
