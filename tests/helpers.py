def create_tree(base, files):
	"""Create a set of files under a directory. The list of files is
	   a list of (subpath, contents) tuples """
	for (subpath, contents) in files:
		path = os.path.join(base, subpath)
		os.makedirs(os.path.dirname(path), exist_ok=True)
		with open(path, "w") as f:
			f.write(contents)