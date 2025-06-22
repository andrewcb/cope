import unittest
import os.path
import shutil
import sqlite3
import tempfile
from urllib.request import pathname2url
from cope.provenancetracker import ProvenanceTracker

class ProvenanceTrackerTests(unittest.TestCase):
	# ---- utility methods for accessing the database itself
	def db_open(self, dblocation=".copemetadata/provenance.sqlite"):
		# throw an exception if the database does not exist
		dbpath = os.path.join(self.tempdir, dblocation)
		dburi = "file:{}?mode=rw".format(pathname2url(dbpath))
		return sqlite3.connect(dburi, uri=True)

	def db_execute(self, cmds):
		dbc = self.db_open()
		if type(cmds) is not list:
			cmds = [cmds]
		cur = dbc.cursor()
		for cmd in cmds:
			cur.execute(cmd)
		dbc.commit()

	def db_query(self, query, *args, **kw):
		dbc = self.db_open()
		cur = dbc.cursor()
		cur.execute(query, *args, **kw)
		return cur.fetchall()

	def db_insert_oprecord(self, values):
		dbc = self.db_open()
		cur = dbc.cursor()
		cur.executemany("insert into oprecord values (?,?,?,?,?,?)", values)
		dbc.commit()
		

	# ---- 

	def setUp(self):
		self.tempdir = tempfile.mkdtemp()

	def tearDown(self):
		shutil.rmtree(self.tempdir)

	#def test_sanity(self):
	#	self.assertEqual(1+1, 2)

	def test_create(self):
		dbname = os.path.join(self.tempdir, "foo")
		rec=ProvenanceTracker(dbname)
		self.assertTrue(os.path.isfile(dbname))
		
	def test_record(self):
		rec=ProvenanceTracker(os.path.join(self.tempdir, ".copemetadata/provenance.sqlite"))
		rec.record("/in/foo", 1000, "/out/bar", 1234)
		self.assertTrue(self.db_query("select inpath, inmtime, outpath, outmtime from oprecord"), [("/in/foo", 1000, "/out/bar", 1234)])

	def test_multiple_record(self):
		rec=ProvenanceTracker(os.path.join(self.tempdir, ".copemetadata/provenance.sqlite"))
		rec.record("/in/foo", 1000, "/out/bar", 1234)
		rec.record("/in/fpp", 1001, "/out/baz", 1234)
		self.assertTrue(self.db_query("select inpath, inmtime, outpath, outmtime from oprecord"), [("/in/foo", 1000, "/out/bar", 1234), ("/in/fpp", 1001, "/out/baz", 1234)])

	def test_duplicate_record(self):
		rec=ProvenanceTracker(os.path.join(self.tempdir, ".copemetadata/provenance.sqlite"))
		rec.record("/in/foo", 1000, "/out/bar", 1234)
		rec.record("/in/foo", 1235, "/out/bar", 1240)
		self.assertTrue(self.db_query("select inpath, inmtime, outpath, outmtime from oprecord"), [("/in/foo", 1235, "/out/bar", 1240)])


	# ----

	def test_check(self):
		rec=ProvenanceTracker(os.path.join(self.tempdir, ".copemetadata/provenance.sqlite"))
		self.db_insert_oprecord([
			("/in/1000-1999/f1023.data", 1027, "/out/a/alpaca/1023.data", 2222, "wibble", 2222),
			("/in/1000-1999/f1024.data", 1029, "/out/s/sloth/1024.data", 2222, None, 2222),
			("/in/1000-1999/f1025.data", 1021, "/out/m/mongoose/1025.data", 2222, "defrobnosticate", 2222)
		])
		# return true for the correct name and timestamp
		self.assertTrue(rec.check("/in/1000-1999/f1024.data", 1029))
		# return false for the correct name but incorrect timestamp
		self.assertFalse(rec.check("/in/1000-1999/f1024.data", 1200))
		# return true for a record with an operation name if none is specified in the call
		self.assertTrue(rec.check("/in/1000-1999/f1023.data", 1027))
		# return true if matching a specific operation name
		self.assertTrue(rec.check("/in/1000-1999/f1023.data", 1027, "wibble"))
		# return false if the operation name mismatches
		self.assertFalse(rec.check("/in/1000-1999/f1023.data", 1027, "blah"))
		# return false if matching a specific operation name but the record does not have one
		self.assertFalse(rec.check("/in/1000-1999/f1024.data", 1029, "wibble"))
