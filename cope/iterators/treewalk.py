
import os

def TreeWalkIterator(include_dir=lambda d:True):
	"""
	An iterator that walks a directory tree and yields relative subpaths.
	"""
	def iter(path):
		for (dirpath, dirnames, filenames) in os.walk(path):
			reldir = os.path.relpath(dirpath, path)
			if not include_dir(reldir):
				continue
			filenames.sort()
			for filename in filenames:
				filepath = os.path.normpath(os.path.join(reldir, filename))
				yield filepath
	return iter
