# cope - Continuous Processing Engine

`cope` is a Python 3-based engine for building scripts for processing incoming files from an input directory and generating output files in an output directory. The engine keeps track of files seen and processed, and can be run repeatedly, with each run picking up new files. Code using the engine must define functions for naming output files and generating output files from input files, and can optionally define code for filtering input files and/or traversing the input directory.

## Example usage

```python

import cope

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

proc = cope.FileProcessor(
	"/raw_files", 
	"/processed_files", 
	destination_name_for, 
	process_file
)

report = proc.run()
print("%d files processed"%len(report.processed))

```

## FileProcessor

`FileProcessor` is the file processing engine exported by `cope`; using `cope` involves instantiating and configuring a `FileProcessor` and then running it. 


### Initialisation and configuration

The `FileProcessor` is configured at creation time, with all options including source and destination paths being set, and takes the following arguments:

- `srcpath` (required): the root of the directory tree from which input files will be taken
- `destpath` (required): the root of the directory tree in which output files will be placed
- `destname` (required): A function which is given the name of a input file and comes up with a name for the output file to be created from it. This takes either one or two arguments: the first argument is the relative path of the input file under `srcpath`, and if a second argument is accepted, it will be prefilled with the absolute path of the file in the filesystem, ready to access for inspection. The function must return a relative path to be placed under the destination tree or `None` if the file should be rejected for processing.
- `process` (required): the function which creates an output file from an input file. It takes two arguments: the absolute path of the input file and the absolute path the output file is to be written at. This function may create the file in Python, copy/link the source to the destination (useful if the script's purpose is naming/arranging files rather than converting them), or call a shell command to perform the operation.
- `iterator` (optional): if specified, this allows an alternative operation for enumerating possible input files in the source directory to be specified. If not, the default is used, which is to walk the directory tree using `os.walk`. Cases where an iterator may be useful include where the source directory tree contains an index or database of some sort listing all viable files, which should be used as a source of truth instead of walking the filesystem. The iterator function should accept the path of a source directory and return a generator that yields the relative paths of all potentially relevant files within it.
- `includename` (optional): if specified, this is a function that determines from an input file's relative path whether this file should be processed. This looks only at the name, and not the contents, and should be used for things such as filtering out files without the correct extensions; i.e., `lambda name: name.endswith('.jpg')`.
- `onprogress` (optional): a function that, if provided, will be called for each input file processing attempt with three arguments: a `FileProcessor.ProgressType` value, a source path, and either a destination path (if successful), an error (if an error occurred) or `None` if no name could be derived.

### Running

Once the `FileProcessor` is configured, it is run with its `run` method, which returns a record of which files were processed. The `run` method accepts the following arguments:

- `dry_run` (optional, default `false`): if `true`, do not process any files, but merely walk the source files, determine output file names and return them as if they were successfully processed. This assumes that the processing function would have worked each time.
- `max_items` (optional): if specified, only handle the given number of files. This allows the process to be throttled to only process a certain number of files in a batch.

The `run` method returns a `FileProcessor.Result` object, which contains the following fields:
- `processed`: a list of all the files that were (or, in the event of a dry run, would have been) successfully processed, each as a (input path, output path) tuple.
- `already_present`: a list of input files examined whose output files are recorded as already having been processed previously (i.e., an output file exists that was created for the file of the same name and modification time). This is returned as a list of (input path, previous output path) values.
- `unnameable`: a list of the source paths of input files for which the destination naming function returned `None`.
- `failed`: a list of files for which processing failed, each as a (source path, error) tuple.

All paths here are relative to the input or output directories, as relevant.

## Tracking already processed files

To keep track of which files had been processed, `cope` creates a hidden directory named `.copemetadata` under the destination path; a SQLite database is stored under this directory; there, each processing of an input file to an output file is recorded, along with the modification times of the files involved. If the input file is modified subsequently, the new time will invalidate this, causing it to be reprocessed when the script is next run.


## Author
Andrew Bulhak (https://github.com/andrewcb/)