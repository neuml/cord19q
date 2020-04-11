"""
Report module
"""

import os
import os.path
import sys

from nltk.corpus import stopwords
from xlsxwriter import Workbook

from .models import Models
from .query import Query

class Report(object):
    """
    Methods to build reports from a series of queries
    """

    @staticmethod
    def create(render, embeddings, cur):
        """
        Factory method to construct a Report.

        Args:
            render: report rendering format

        Returns:
            Report
        """

        if render == "md":
            return Markdown(embeddings, cur)
        elif render == "xlsx":
            return XLSX(embeddings, cur)

        return None

    @staticmethod
    def run(task, topn=None, render=None, path=None):
        """
        Reads a list of queries from a task file and builds a report.

        Args:
            task: input task file
            topn: number of results
            render: report rendering format ("md" for markdown, "csv" for csv)
            path: model path
        """

        # Load model
        embeddings, db = Models.load(path)

        # Read each task query
        with open(task, "r") as f:
            queries = [line.strip() for line in f.readlines()]

        # Derive report format
        render = render if render else "md"

        # Create report object. Default to Markdown.
        report = Report.create(render, embeddings, db)

        # Generate output filename
        outfile = "%s.%s" % (os.path.splitext(task)[0], render)

        # Stream report to file
        with open(outfile, report.mode()) as output:
            # Initialize report
            report.open(output)

            # Build the report
            report.build(queries, topn, output)

            # Close the report
            report.close()

        # Free resources
        Models.close(db)

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

    def build(self, queries, topn, output):
        """
        Builds a report using a list of input queries

        Args:
            queries: queries to execute
            topn: number of section results to return
            output: output I/O object
        """

        # Default to 50 results if not specified
        topn = topn if topn else 50

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
            self.headers(output, ["Date", "Title", "Severe", "Fatality", "Design", "Sample", "Sampling Method", "Matches"])

            # Generate table rows
            self.articles(output, query, results)

            # Write section separator
            self.separator(output)

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

        # Print report by published asc
        for row in sorted(rows, key=lambda x: x[0]):
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

class Markdown(Report):
    """
    Report writer for Markdown.
    """

    def encode(self, url):
        """
        URL encodes parens as they cause issues with markdown links.

        Args:
            url: input url

        Returns:
            url with parens encoded
        """

        # Escape ()
        return url.replace("(", "%28").replace(")", "%29") if url else url

    def column(self, value):
        """
        Escapes invalid characters (| char) within a table column value.

        Args:
            value: input value

        Returns:
            value with | escaped
        """

        # Escape |
        return value.replace("|", "&#124;") if value else value

    def write(self, output, line):
        """
        Writes line to output file.

        Args:
            output: output file
            line: line to write
        """

        output.write("%s\n" % line)

    def query(self, output, query):
        self.write(output, "# %s" % query)

    def section(self, output, name):
        self.write(output, "#### %s<br/>" % name)

    def highlight(self, output, article, highlight):
        # Build citation link
        link = "[%s](%s)" % (Query.authors(article[0]) if article[0] else "Source", self.encode(article[1]))

        # Build highlight row with citation link
        self.write(output, "- %s %s<br/>" % (Query.text(highlight), link))

    def headers(self, output, names):
        # Write table header
        headers = "|".join(names)
        self.write(output, "|%s|" % headers)

        # Write markdown separator for headers
        headers = "|".join(["----"] * len(names))
        self.write(output, "|%s|" % headers)

    def buildRow(self, article, stat, sections):
        columns = []

        # Date
        columns.append(Query.date(article[0]) if article[0] else "")

        # Title
        title = "[%s](%s)" % (article[1], self.encode(article[2]))

        # Append Publication if available. Assume preprint otherwise and show preprint source.
        title += "<br/>%s" % (article[3] if article[3] else article[4])

        # Title + Publication if available
        columns.append(title)

        # Severe
        columns.append(stat if stat else "")

        # Fatality
        columns.append("")

        # Design
        columns.append(Query.design(article[5]))

        # Sample Size
        sample = Query.sample(article[6], article[7])
        columns.append(sample if sample else "")

        # Sampling Method
        columns.append(Query.text(article[8]) if article[8] else "")

        # Top Matches
        columns.append("<br/><br/>".join([Query.text(text) for _, text in sections]))

        # Escape | characters embedded within columns
        return [self.column(column) for column in columns]

    def writeRow(self, output, row):
        self.write(output, "|%s|" % "|".join(row))

    def separator(self, output):
        # Write section separator
        self.write(output, "")

class XLSX(Report):
    """
    Report writer for XLSX.
    """

    # Stop words to use for generating a clean sheet name
    STOP_WORDS = set(stopwords.words("english"))

    def __init__(self, embeddings, db):
        super(XLSX, self).__init__(embeddings, db)

        # Workbook handles
        self.workbook = None
        self.worksheet = None

        # Workbook styles
        self.styles = {}

        # Row index
        self.row = 0

    def mode(self):
        # xlsxwriter writes binary output
        return "wb"

    def open(self, output):
        self.workbook = Workbook(output)

        # Header styles
        self.styles["query"] = self.workbook.add_format({"bold": True, "font_size": 14})
        self.styles["section"] = self.workbook.add_format({"bold": True, "font_size": 12})
        self.styles["highlight"] = self.workbook.add_format({"underline": True, "font_color": "blue", "font_size": 10.5})
        self.styles["highlight-noref"] = self.workbook.add_format({"font_size": 10.5})
        self.styles["header"] = self.workbook.add_format({"bold": True, "underline": True, "bg_color": "#cccccc"})

        # Common style definitions
        common = {"text_wrap": True, "align": "vcenter", "font_size": 10.5}
        url = {"font_color": "blue", "underline": True}
        even = {"bg_color": "#f5f5f5"}

        # Column styles
        self.styles["default"] = self.workbook.add_format(common)
        self.styles["url"] = self.workbook.add_format({**common, **url})

        # Even row column styles
        self.styles["default-even"] = self.workbook.add_format({**common, **even})
        self.styles["url-even"] = self.workbook.add_format({**common, **url, **even})

    def close(self):
        # Free xlsx resources and close file handle
        if self.workbook:
            self.workbook.close()

    def style(self, name):
        """
        Looks up a style by name.

        Args:
            name: style name
        """

        return self.styles[name]

    def sheetname(self, query):
        """
        Builds a sheet name from a query.

        Args:
            query: query

        Returns:
            sheet name
        """

        # Build sheet name up to 25 chars, prevent breaking on word
        tokens = [token for token in query.split() if token.lower() not in XLSX.STOP_WORDS]
        name = ""
        for token in tokens:
            if len(name) + len(token) > 30:
                break
            name += token + " "

        return name

    def write(self, columns, style=None, altrows=False):
        """
        Writes a row to excel.

        Args:
            columns: list of columns to write for row
            style: optional style to use for row
            altrows: if every other row should be color shaded
        """

        # Use altstyle if enabled and it exists
        altstyle = ""
        if altrows and self.row % 2 == 0:
            altstyle = "-even"
            if style and (style + altstyle) in self.styles:
                style += altstyle

        # Write out row column by column
        for x, value in enumerate(columns):
            if isinstance(value, tuple):
                if value[0]:
                    # Tuples are URLs
                    url = "url" + altstyle if altrows else "highlight"
                    self.worksheet.write_url(self.row, x, value[0], self.styles[url], string=value[1])
                else:
                    # URL link empty, write text with no wrap
                    default = "default" + altstyle if altrows else "highlight-noref"
                    self.worksheet.write(self.row, x, value[1], self.styles[default])
            else:
                # Default write method
                self.worksheet.write(self.row, x, value, self.styles[style if style else "default" + altstyle])

        # Increment row count
        self.row += 1

    def query(self, output, query):
        # Build sheet name
        name = self.sheetname(query)

        # Create new worksheet, reset rows index
        self.worksheet = self.workbook.add_worksheet(name.title().strip())
        self.row = 0

        # Format size of columns
        for column, width in enumerate([15, 50, 15, 15, 15, 8, 50, 70]):
            self.worksheet.set_column(column, column, width)

        # Write query to file
        self.write(["%s" % query.strip()], "query")

    def section(self, output, name):
        self.write([name], "section")

    def highlight(self, output, article, highlight):
        # Extract fields
        author, reference = article

        # Build text and citation name
        text = "%s (%s)" % (Query.text(highlight), Query.authors(author if author else "Source"))

        # Write out highlight
        self.write([(reference, text)])

    def headers(self, output, names):
        self.write(names, "header")

    def buildRow(self, article, stat, sections):
        columns = []

        # Date
        columns.append(Query.date(article[0]) if article[0] else "")

        # Title
        title = article[1]

        # Append Publication if available. Assume preprint otherwise and show preprint source.
        title += " [%s]" % (article[3] if article[3] else article[4])

        # Title + Publication if available
        columns.append((article[2], title))

        # Severe
        columns.append(stat)

        # Fatality
        columns.append("")

        # Design
        columns.append(Query.design(article[5]))

        # Sample Size
        columns.append(Query.sample(article[6], article[7]))

        # Sampling Method
        columns.append(Query.text(article[8]))

        # Top Matches
        columns.append("\n\n".join([Query.text(text) for _, text in sections]))

        return columns

    def writeRow(self, output, row):
        # Write row, use alternate color shading for rows
        self.write(row, None, True)

    def separator(self, output):
        # Section separator
        self.row += 1

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run report with params: input file, topn, render format, model path
        Report.run(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None, sys.argv[3] if len(sys.argv) > 3 else None,
                   sys.argv[4] if len(sys.argv) > 4 else None)
