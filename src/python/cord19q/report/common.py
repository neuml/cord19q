"""
Report module
"""

from ..query import Query

class Report(object):
    """
    Methods to build reports from a series of queries
    """

    def __init__(self, embeddings, db):
        """
        Creates a new report.

        Args:
            embeddings: embeddings index
            db: database connection
        """

        # Store references to embeddings index and open database cursor
        self.embeddings = embeddings
        self.cur = db.cursor()
        self.names = None

    def build(self, queries, topn, category, output):
        """
        Builds a report using a list of input queries

        Args:
            queries: queries to execute
            topn: number of section results to return
            category: report category
            output: output I/O object
        """

        # Default to 50 results if not specified
        topn = topn if topn else 50

        # Get columns for category
        self.names = self.columns(category)

        for query in queries:
            # Write query string
            self.query(output, query)

            # Write separator
            self.separator(output)

            # Query for best matches
            results = Query.search(self.embeddings, self.cur, query, topn)

            # Generate highlights section
            self.section(output, "Highlights")

            # Generate highlights
            self.highlights(output, results, int(topn / 10))

            # Separator between highlights and articles
            self.separator(output)

            # Generate articles section
            self.section(output, "Articles")

            # Generate table headers
            self.headers(output, self.names)

            # Generate table rows
            self.articles(output, query, results)

            # Write section separator
            self.separator(output)

    def columns(self, category):
        """
        Gets the display columns depending on the category of report

        Args:
            category: report category
        """

        if category == "risk":
            return ["Date", "Title", "Severe", "Fatality", "Design", "Sample", "Sampling Method", "Matches"]

        return ["Date", "Title", "Design", "Sample", "Sampling Method", "Matches"]

    def highlights(self, output, results, topn):
        """
        Builds a highlights section.

        Args:
            output: output file
            results: search results
            topn: number of results to return
        """

        # Extract top sections as highlights
        for highlight in Query.highlights(results, topn):
            # Get matching article
            uid = [article for _, _, article, text in results if text == highlight][0]
            self.cur.execute("SELECT Authors, Reference FROM articles WHERE id = ?", [uid])
            article = self.cur.fetchone()

            # Write out highlight row
            self.highlight(output, article, highlight)

    def articles(self, output, query, results):
        """
        Builds an articles section.

        Args:
            output: output file
            query: search query
            results: search results
        """

        # Get results grouped by document
        documents = Query.documents(results)

        # Collect matching rows
        rows = []

        for uid in documents:
            # Get article metadata
            self.cur.execute("SELECT Published, Title, Reference, Publication, Source, Design, Size, Sample, Method " +
                             "FROM articles WHERE id = ?", [uid])
            article = self.cur.fetchone()

            # Lookup stat
            stat = Query.stat(self.cur, uid, query)

            # Builds a row for article
            rows.append(self.buildRow(article, stat, documents[uid]))

        # Print report by published desc
        for row in sorted(rows, key=lambda x: x["Date"], reverse=True):
            # Convert row dict to list
            row = [row[column] for column in self.names]

            # Write out row
            self.writeRow(output, row)

    def mode(self):
        """
        Output mode "w" for writing text files, "wb" for binary files.

        Returns:
            default returns "w"
        """

        return "w"

    def open(self, output):
        """
        Opens a report.

        Args:
            output: output file handle
        """

    def close(self):
        """
        Closes a report.
        """

    def cleanup(self, outfile):
        """
        Allow freeing or cleaning up resources.

        Args:
            outfile: output file path
        """

    def query(self, output, query):
        """
        Writes query.

        Args:
            output: output file
            query: query string
        """

    def section(self, output, name):
        """
        Writes a section name

        Args:
            output: output file
            name: section name
        """

    def highlight(self, output, article, highlight):
        """
        Writes a highlight row

        Args:
            output: output file
            article: article reference
            highlight: highlight text
        """

    def headers(self, output, names):
        """
        Writes table headers.

        Args:
            output: output file
            name: section name
        """

    def buildRow(self, article, stat, sections):
        """
        Converts a document to a table row.

        Args:
            article: article
            stat: top article statistic matching query
            sections: text sections for article
        """

    def writeRow(self, output, row):
        """
        Writes a table row.

        Args:
            output: output file
            row: output row
        """

    def separator(self, output):
        """
        Writes a separator between sections
        """
