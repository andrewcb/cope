import os
import os.path
import time
import sqlite3

class ProvenanceTracker:
	def __init__(self, dbpath):
		self.dbpath = dbpath
		self.dbc = self._ensure_database_exists()

	def _ensure_database_exists(self):
		dir = os.path.dirname(self.dbpath)
		os.makedirs(dir, exist_ok=True)
		db_existed = os.path.isfile(self.dbpath)
		dbc = sqlite3.connect(self.dbpath)
		if not db_existed:
			cur = dbc.cursor()
			cur.execute("create table oprecord (inpath VARCHAR, inmtime INT, outpath VARCHAR PRIMARY KEY, outmtime INT, opname VARCHAR, timestamp INT)")
			dbc.commit()
		return dbc

	def check(self, inpath, mtime, opname=None):
		"Checks if if an output file has been created for an input file with a name and creation time, returning the outpath or None"
		cur = self.dbc.cursor()
		if opname:
			cur.execute("select outpath from oprecord where inpath=:inpath and inmtime=:mtime and opname=:opname", {"inpath": inpath, "mtime":mtime, "opname":opname})
		else:
			cur.execute("select outpath from oprecord where inpath=:inpath and inmtime=:mtime", {"inpath": inpath, "mtime":mtime})
		r = cur.fetchone()
		return r and r[0]

	def record(self, inpath, inmtime, outpath, outmtime, opname=None, timestamp=None):
		"Record the processing of a file"
		timestamp = int(timestamp or time.time())
		cur = self.dbc.cursor()
		cur.execute("DELETE FROM oprecord WHERE OUTPATH=?", (outpath,))
		cur.execute("INSERT INTO oprecord VALUES (?, ?, ?, ?, ?, ?)", (inpath, inmtime, outpath, outmtime, opname, timestamp))
		self.dbc.commit()