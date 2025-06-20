# This is a replacement for TreeWalkIterator, written from first principles, and 
# allowing more control, including custom starting positions

import os
import os.path

def DirectoryTreeIterator(include_dir=lambda d:True):
	""" """
	def iter(path, start=None, stop=None, limit_to=None, base_path=None):
		"""
		iterate under a directory, yielding a succession of relative paths
		if specified, start is a path before which items are to be ignored,
		either as a string or a list of path segments. stop is an optional 
		path in the same format after which items are to be ignored. 
		If limit_to is specified, only items whose paths are prefixed with
		this path will be processed; this is effectively specifying start and stop
		as the same path.
		"""
		if limit_to:
			start = limit_to
			stop = limit_to
		if type(start) == str:
			start = start.split('/')
		if type(stop) == str:
			stop = stop.split('/')
		base_path = base_path or path
		items = os.listdir(path)
		items.sort()
		for item in items:
			if start and item < start[0]:
				continue
			if stop and item > stop[0]:
				continue
			itempath = os.path.join(path, item)
			relitempath = os.path.relpath(itempath, base_path)

			if os.path.isdir(itempath):
				if include_dir(relitempath):
					for i in iter(
						itempath, 
						start=(start and item == start[0]) and start[1:] or None,
						stop=(stop and item == stop[0]) and stop[1:] or None,
						base_path = base_path
					):
						yield i
			elif os.path.isfile(itempath):
				yield os.path.normpath(relitempath)

	return iter