"""
Crochet tests.
"""

from twisted.python.filepath import FilePath

# Directory where the crochet package is stored:
crochet_directory = FilePath(__file__).parent().parent().parent().path
