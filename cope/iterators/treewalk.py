
import os

def TreeWalkIterator(path):
	"""
	An iterator that walks a directory tree and yields relative subpaths.
	"""
	for (dirpath, dirnames, filenames) in os.walk(path):
		reldir = os.path.relpath(dirpath, path)
		filenames.sort()
		for filename in filenames:
			filepath = os.path.normpath(os.path.join(reldir, filename))
			yield filepath
