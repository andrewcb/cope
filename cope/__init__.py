"""
An engine for automatically traversing files in a directory and running a process to generate other files elsewhere, whilst keeping track of which files have been processed.

Typical usage:

	def destination_name_for(infile_relative_path, infile_absolute_path):
		# return the name for the output name to be generated from an input file
		# this version extracts a date from the file in a format-specific way
		# and puts the file under a yyyy/mm/dd/ subpath of the output directory
		time = get_timestamp(infile_absolute_path)
		basename = os.path.split(infile_relative_path)[1]
		return "%04d/%02d/%02d/%s"%(time.year, time.month, time.day, basename)

	def process_file(source, dest):
		# process the file. Here we just read it and write it. 
		# note that this assumes the files aren't huge
		with open(source) as fi:
			with open(dest, "w") as fo:
				fo.write(fi.read())

	proc = FileProcessor(
		"/raw_files", 
		"/processed_files", 
		destination_name_for, 
		process_file
	)

	report = proc.run()
	print("%d files processed"%len(report.processed))
"""

from .fileprocessor import FileProcessor
from .processfunctions import Process, INFILE, OUTFILE

__all__ = ['FileProcessor', 'Process', 'INFILE', 'OUTFILE']

