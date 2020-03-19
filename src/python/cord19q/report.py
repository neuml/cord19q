"""
Report module
"""

import os
import os.path
import sqlite3
import sys

# pylint: disable = E0401
from .embeddings import Embeddings
from .models import Models
from .tokenizer import Tokenizer

class Report(object):
    """
    Methods to build reports from a series of queries
    """

    @staticmethod
    def load():
        """
        Loads an embeddings model and db database.

        Returns:
            (embeddings, db handle)
        """

        path = Models.modelPath()
        dbfile = os.path.join(path, "articles.db")

        if os.path.isfile(os.path.join(path, "config")):
            print("Loading model from %s" % path)
            embeddings = Embeddings()
            embeddings.load(path)
        else:
            print("ERROR: loading model: ensure model is present")
            raise FileNotFoundError("Unable to load model from %s" % path)

        # Connect to database file
        db = sqlite3.connect(dbfile)

        return (embeddings, db)

    @staticmethod
    def write(output, line):
        """
        Writes line to output file.

        Args:
            output: output file
            line: line to write
        """

        output.write("%s<br/>\n" % line)

    @staticmethod
    def build(embeddings, db, queries, outfile):
        """
        Builds a report using a list of input queries

        Args:
            embeddings: embeddings model
            db: open SQLite database
            queries: list of queries to execute
            outfile: report output file
        """

        with open(outfile, "w") as output:
            cur = db.cursor()

            for query in queries:
                output.write("# %s\n" % query)

                query = Tokenizer.tokenize(query)

                for uid, score in embeddings.search(query, 10):
                    cur.execute("SELECT Article, Text FROM sections WHERE id = ?", [uid])
                    section = cur.fetchone()

                    if score >= 0.0:
                        # Unpack match
                        article, text = section

                        cur.execute("SELECT Title, Reference, Authors, Published, Publication from articles where id = ?", [article])
                        article = cur.fetchone()

                        Report.write(output, "[%s](%s)" % (article[0], article[1]))
                        Report.write(output, "Authors: %s" % article[2])

                        if article[3]:
                            Report.write(output, "Published: %s" % article[3])

                        if article[4]:
                            Report.write(output, "Publication: %s" % article[4])

                        Report.write(output, "Match (%.4f): **%s**" % (score, text))
                        Report.write(output, "")

    @staticmethod
    def close(db):
        """
        Closes a SQLite database database.

        Args:
            db: open database
        """

        # Free database resources
        db.close()

    @staticmethod
    def run(task):
        """
        Reads a list of queries from a task file and builds a report.

        Args:
            task: input task file
        """

        # Load model
        embeddings, db = Report.load()

        # Read each task query
        with open(task, "r") as f:
            queries = f.readlines()

        # Build the report file
        Report.build(embeddings, db, queries, "%s.md" % os.path.splitext(task)[0])

        # Free resources
        Report.close(db)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        Report.run(sys.argv[1])
