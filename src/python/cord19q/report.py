"""
Report module
"""

import datetime
import os
import os.path
import re
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
    def date(date):
        if date:
            date = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

            # 1/1 dates had no month/day specified, use only year
            if date.month == 1 and date.day == 1:
                return date.strftime("%Y")

            return date.strftime("%b %d, %Y")

    @staticmethod
    def text(text):
        """
        Formats match text.

        Args:
            text: input text

        Returns:
            formatted text
        """

        # Remove reference links ([1], [2], etc)
        text = re.sub(r"\s*\[[0-9, ]+\]\s*", "", text)

        # Remove •
        text = text.replace("•", "")

        return text

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

                documents = {}
                for uid, score in embeddings.search(query, 50):
                    cur.execute("SELECT Article, Text FROM sections WHERE id = ?", [uid])
                    article, text = cur.fetchone()

                    if article not in documents:
                        documents[article] = set()

                    documents[article].add((score, text))

                # Sort each set
                for uid in documents:
                    documents[uid] = sorted(list(documents[uid]), reverse=True)

                # Print each result, sorted by max score descending
                for uid in sorted(documents, key=lambda k: sum([x[0] for x in documents[k]]), reverse=True)[:10]:
                    cur.execute("SELECT Title, Reference, Authors, Publication, Published from articles where id = ?", [uid])
                    article = cur.fetchone()

                    Report.write(output, "[%s](%s)" % (article[0], article[1]))

                    if article[2]:
                        Report.write(output, "by %s" % article[2])

                    # Publication name and date
                    publication = article[3] if article[3] else None
                    if article[4]:
                        published = Report.date(article[4])
                        publication = (publication + " - " + published) if publication else published

                    if publication and len(publication) > 0:
                        Report.write(output, "*%s*" % publication)

                    # Print each match
                    for (_, text) in documents[uid]:
                        Report.write(output, "- %s" % Report.text(text))

                    # Start new section
                    output.write("\n")

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
