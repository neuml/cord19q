"""
Report module
"""

import os
import os.path
import sys

from .models import Models
from .query import Query

class Report(object):
    """
    Methods to build reports from a series of queries
    """

    @staticmethod
    def encode(url):
        """
        URL encodes parens as they cause issues with markdown links.

        Args:
            url: input url

        Returns:
            url with parens encoded
        """

        # Escape ()
        return url.replace("(", "%28").replace(")", "%29") if url else url

    @staticmethod
    def column(value):
        """
        Escapes invalid characters (| char) within a table column value.

        Args:
            value: input value

        Returns:
            value with | escaped
        """

        # Escape |
        return value.replace("|", "&#124;") if value else value

    @staticmethod
    def write(output, line):
        """
        Writes line to output file.

        Args:
            output: output file
            line: line to write
        """

        output.write("%s\n" % line)

    @staticmethod
    def highlights(output, results, cur, topn):
        """
        Builds a highlights section in markdown.

        Args:
            output: output file
            results: search results
            cur: cursor handle to articles database
            topn: number of highlights to return
        """

        # Extract top sections as highlights
        Report.write(output, "#### Highlights<br/>")
        for highlight in Query.highlights(results, topn):
            # Get matching article
            uid = [article for _, _, article, text in results if text == highlight][0]
            cur.execute("SELECT Authors, Reference from articles where id = ?", [uid])
            article = cur.fetchone()

            link = "[%s](%s)" % (Query.authors(article[0]) if article[0] else "Source", Report.encode(article[1]))

            Report.write(output, "- %s %s<br/>" % (Query.text(highlight), link))

    @staticmethod
    def articles(output, results, cur):
        """
        Builds an articles section in markdown.

        Args:
            output: output file
            results: search results
            cur: cursor handle to articles database
        """

        # Write each article result
        Report.write(output, "\n#### Articles<br/>")

        # Get results grouped by document
        documents = Query.documents(results)

        # Write table header
        Report.write(output, "| Date | Authors | Title | Matches |")
        Report.write(output, "| ---- | ---- | ------ | -----------|")

        # Print each result, sorted by max score descending
        for uid in sorted(documents, key=lambda k: sum([x[0] for x in documents[k]]), reverse=True):
            cur.execute("SELECT Published, Authors, Title, Reference, Publication from articles where id = ?", [uid])
            article = cur.fetchone()

            columns = []

            # Date
            columns.append(Query.date(article[0]) if article[0] else "")

            # Authors
            columns.append(Query.authors(article[1]) if article[1] else "")

            # Title
            title = "[%s](%s)" % (article[2], Report.encode(article[3]))

            # Append Publication if available
            if article[4]:
                title += " (%s)" % article[4]

            # Title + Publication if available
            columns.append(title)

            # Top matches
            columns.append("<br/><br/>".join([Query.text(text) for _, text in documents[uid]]))

            # Escape | characters embedded within columns
            columns = [Report.column(column) for column in columns]

            # Write out row
            Report.write(output, "|%s|" % "|".join(columns))

    @staticmethod
    def build(embeddings, db, queries, topn, output):
        """
        Builds a report using a list of input queries

        Args:
            embeddings: embeddings model
            db: open SQLite database
            queries: queries to execute
            topn: number of section results to return
            output: output I/O object
        """

        # Create database cursor
        cur = db.cursor()

        # Default to 50 results if not specified
        topn = topn if topn else 50

        for query in queries:
            output.write("# %s\n" % query)

            # Query for best matches
            results = Query.search(embeddings, cur, query, topn)

            # Generate highlights section
            Report.highlights(output, results, cur, int(topn / 10))

            # Generate articles section
            Report.articles(output, results, cur)

            # Create separator between sections
            Report.write(output, "")

    @staticmethod
    def run(task, topn=None, path=None):
        """
        Reads a list of queries from a task file and builds a report.

        Args:
            task: input task file
            topn: number of results
            path: model path
        """

        # Load model
        embeddings, db = Models.load(path)

        # Read each task query
        with open(task, "r") as f:
            queries = f.readlines()

        # Generate output filename
        outfile = "%s.md" % os.path.splitext(task)[0]

        # Stream report to file
        with open(outfile, "w") as output:
            # Build the report
            Report.build(embeddings, db, queries, topn, output)

        # Free resources
        Models.close(db)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        Report.run(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None, sys.argv[3] if len(sys.argv) > 3 else None)
