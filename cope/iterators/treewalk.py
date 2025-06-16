
import os
import itertools

def TreeWalkIterator(include_dir=lambda d:True, max_dirs=None):
	"""
	An iterator that walks a directory tree and yields relative subpaths.

	Arguments:
	- include_dir: an optional lambda function called with the relative path of a directory, returning 
	  a truth value. If false, the directory will not be processed.
	- max_dirs: the maximum number of directories to process in this run. This counts all directories
	  visited, regardless of whether any action is taken.
	"""
	def iter(path):
		generator = os.walk(path)
		if max_dirs:
			generator = itertools.islice(generator,max_dirs)
		for (dirpath, dirnames, filenames) in generator:
			reldir = os.path.relpath(dirpath, path)
			if not include_dir(reldir):
				continue
			filenames.sort()
			for filename in filenames:
				filepath = os.path.normpath(os.path.join(reldir, filename))
				yield filepath
	return iter
