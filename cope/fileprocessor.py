import os
import os.path
import enum
import time
from collections import namedtuple
from inspect import signature
from .provenancetracker import ProvenanceTracker
from .iterators.treewalk import TreeWalkIterator

def argcount(fn):
	"Return how many arguments a function accepts"
	return len(signature(fn).parameters)

class FileProcessor:
	"""
	The engine for automatically selecting suitable files from an input directory, and applying a process to derive output files from them in an output directory. 
	"""
	Result = namedtuple('Result', ['processed', 'already_present', 'unnameable', 'failed'])

	class ProgressType(enum.Enum):
		PROCESSED = 1
		ALREADY_PRESENT = 2
		UNNAMEABLE = 3
		ERROR = 4

	def __init__(self, srcpath, destpath, process, destname=None, iterator=None, includename=None, onprogress=None):
		"""
		Create a FileProcessor object. The arguments are:
		- srcpath: the tree containing files to traverse and process
		- destpath: the tree to place output (and working metadata) in
		- process: a function, given the absolute path of an input file and that of its output, carries out the process of generating the output from the input.
		- destname: a function that takes two arguments (the path relative to the source tree of a file and (optionally) its absolute path in the filesystem) and returns its relative path for its product, or None if the file is to be omitted
		- iterator: a function which takes a path and returns a generator of relative paths of input files within the source directory
		- includename: an optional function determining whether a file should be included; this should work solely by inspecting its name
		- onprogress: an optional function which, if provided, is called after each file is handled (one way or another), with a ProgressType, a source relative path and (where valid) a destination relative path. This is intended to be used for progress indicators or similar.
		"""
		self.srcpath = srcpath
		self.destpath = destpath
		self.includename = includename and includename or (lambda n: True)
		self.destname = destname and destname or (lambda name: name)
		self.process = process
		self.iterator = iterator and iterator or TreeWalkIterator
		# a method to call once any file has been processed/skipped, called with a ProgressType enum, source path and destination path or None
		self.onprogress = onprogress
		self.provenancetracker = ProvenanceTracker(destpath)

	def _call_onprogress(self, *args):
		if self.onprogress:
			self.onprogress(*args)

	def run(self, dry_run=False, max_items=None):
		"""Run the process. 

		If dry_run is true, no actual processing is done and the database is not updated, but everything else is handled as if it were live.
		If max_items is specified, the function will exit after that number of items have been processed.

		Returns a namedtuple containing the following fields, with all paths being relative to base directories:
		 - processed: list of (source, destination) tuples for all files that were or would have been processed
		 - already_present: list of (source, destination) tuples for files that had been handled before, and thus were omitted this time 
		 - unnameable: list of source tuples for files for which the destname operation failed to return a name.
		"""

		processed, already_present, unnameable, failed = [],[],[],[]

		for rsrcpath in self.iterator(self.srcpath):
			if max_items == 0:
				break
			if not self.includename(rsrcpath):
				continue
			fsrcpath = os.path.join(self.srcpath, rsrcpath)
			if not os.path.exists(fsrcpath):
				continue

			# we store the timestamp as an int for ease of comparison, but 
			# convert it to microseconds, as modern OSes support 
 			# sub-millisecond timestamps
			src_mtime = int(os.path.getmtime(fsrcpath)*1000000)
			prevdest = self.provenancetracker.check(rsrcpath, src_mtime)
			if prevdest:	
				already_present.append((rsrcpath, prevdest))
				self._call_onprogress(FileProcessor.ProgressType.ALREADY_PRESENT, rsrcpath, prevdest)
				continue
			if argcount(self.destname)>=2:
				rdestpath = self.destname(rsrcpath, fsrcpath)
			else:
				rdestpath = self.destname(rsrcpath)
			if not rdestpath:
				unnameable.append(rsrcpath)
				self._call_onprogress(FileProcessor.ProgressType.UNNAMEABLE, rsrcpath, None)
				continue
			if not dry_run:
				fdestpath = os.path.join(self.destpath, rdestpath)
				os.makedirs(os.path.dirname(fdestpath), exist_ok=True)
				try:
					self.process(fsrcpath, fdestpath)
				except Exception as e:
					failed.append((rsrcpath, e))
					self._call_onprogress(FileProcessor.ProgressType.ERROR, rsrcpath, e)
					continue
				self.provenancetracker.record(rsrcpath, src_mtime, rdestpath, int(os.path.getmtime(fdestpath)*1000000))
			processed.append((rsrcpath, rdestpath))
			self._call_onprogress(FileProcessor.ProgressType.PROCESSED, rsrcpath, rdestpath)
			if max_items is not None:
				max_items = max_items - 1

		return FileProcessor.Result(processed=processed, already_present=already_present, unnameable=unnameable, failed=failed)
