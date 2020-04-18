"""
Excel report module
"""

from nltk.corpus import stopwords
from xlsxwriter import Workbook

from ..query import Query

from .common import Report

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

        # Build sheet name up to 30 chars, prevent breaking on word
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

        # Column widths
        widths = None
        if "Severe" in self.names:
            widths = [15, 50, 15, 15, 15, 8, 50, 70]
        else:
            widths = [15, 50, 15, 20, 20, 50, 70]

        # Format size of columns
        for column, width in enumerate(widths):
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
        columns = {}

        # Date
        columns["Date"] = Query.date(article[0]) if article[0] else ""

        # Title
        title = article[1]

        # Append Publication if available. Assume preprint otherwise and show preprint source.
        title += " [%s]" % (article[3] if article[3] else article[4])

        # Title + Publication if available
        columns["Title"] = (article[2], title)

        # Severe
        columns["Severe"] = stat

        # Fatality
        columns["Fatality"] = ""

        # Design
        columns["Design"] = Query.design(article[5])

        # Sample Size
        columns["Sample"] = Query.sample(article[6], article[7])

        # Sampling Method
        columns["Sampling Method"] = Query.text(article[8])

        # Top Matches
        columns["Matches"] = "\n\n".join([Query.text(text) for _, text in sections])

        return columns

    def writeRow(self, output, row):
        # Write row, use alternate color shading for rows
        self.write(row, None, True)

    def separator(self, output):
        # Section separator
        self.row += 1
