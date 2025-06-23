import os.path
from .provenancetracker import ProvenanceTracker

class MetadataRepository:
	"""
	This embodies a metadata repository for a destination path, which contains
	provenance tracking and other data.
	"""
	# this class is the source of truth for the metadata directory path and
	# the files contained therein.

	def __init__(self, destpath, metadatadirname=".copemetadata"):
		self.dirpath = os.path.join(destpath, metadatadirname)
		dbpath = os.path.join(self.dirpath, "provenance.sqlite")
		self.provenancetracker = ProvenanceTracker(dbpath)

	# --- provenance tracking

	def check_for_product(self, inpath, mtime, opname=None):
		"Returns the path of the product file produced for an input, or None if none exists"
		return self.provenancetracker.check(inpath, mtime, opname)

	def record_product(self, inpath, inmtime, outpath, outmtime, opname=None, timestamp=None):
		return self.provenancetracker.record(inpath, inmtime, outpath, outmtime, opname, timestamp)

	# --- last-processed handling

	def get_last_processed(self):
		return self.provenancetracker.most_recently_processed()
