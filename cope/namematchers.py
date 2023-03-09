
import functools

class NameMatcher:
	"""
	A namespace containing functions for matching filenames for processing.
	"""

	@staticmethod
	def endswith(*v, case_sensitive=False):
		matchable = case_sensitive and v or [i.lower() for i in v]
		def match(name):
			name = case_sensitive and name or name.lower()
			return functools.reduce(lambda r,i: r or name.endswith(i), matchable, False)
		return match