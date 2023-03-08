import subprocess
import shutil
import os


# constants for use in process argument replacement
INFILE = 1
OUTFILE = 2

def _sub_arglist(src, dest, args):
	return [ a == INFILE and src or a == OUTFILE and dest or a for a in args ]

class Process:
	"""
	A namespace containing some useful processing functions or functions that generate them
	"""
	@staticmethod
	def run(*args):
		"""
		Return a processing function that runs an external process with the 
		array of arguments specified, substituting the input and output file
		paths for the INFILE and OUTFILE placeholders. This process is assumed
		to create the output file as a side-effect. If it returns a nonzero
		status code, a subprocess exception is raised.
		"""
		def proc(src, dest):
			args2 = _sub_arglist(src, dest, args)
			subprocess.run(args2, check=True)
		return proc

	@staticmethod
	def captureOutputOf(*args):
		"""
		Return a processing function that runs an external process with the 
		array of arguments specified, substituting the input file paths for 
		the INFILE placeholder, and capture its standard output into the 
		output file.  If it returns a nonzero status code, a subprocess 
		exception is raised.
		"""
		def proc(src, dest):
			args2 = _sub_arglist(src, None, args)
			with open(dest, 'wb') as fo:
				res = subprocess.run(args2, capture_output=True, check=True)
				fo.write(res.stdout)

		return proc

	copy = shutil.copy

	hardLink = os.link

	# TODO: add copy, hard/soft link and such

