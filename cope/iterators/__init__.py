""" Directory iterators live here

A directory iterator is a function which takes a path and returns a generator 
of relative paths of input files within the source directory. The generic 
implementation provided walks the tree and returns all files under it, though
it is conceivable that some tasks may require iterators that get source files 
from a more specific source of truth than the filesystem, such as an index or
database.
"""