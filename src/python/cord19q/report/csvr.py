"""
CSV report module
"""

import csv
import os
import os.path

from nltk.corpus import stopwords

from ..query import Query

from .common import Report

class CSV(Report):
    """
    Report writer for CSV exports. Format is designed to be imported into other tools.
    """

    # Stop words to use for generating a clean sheet name
    STOP_WORDS = set(stopwords.words("english"))

    def __init__(self, embeddings, db):
        super(CSV, self).__init__(embeddings, db)

        # CSV writer handle
        self.csvout = None
        self.writer = None

    def cleanup(self, outfile):
        # Delete created master csv file
        os.remove(outfile)

    def filename(self, query):
        """
        Builds a file name from a query.

        Args:
            query: query

        Returns:
            file name
        """

        # Build file name up to 30 chars, prevent breaking on word
        tokens = [token for token in query.split() if token.lower() not in CSV.STOP_WORDS]
        name = ""
        for token in tokens:
            if len(name) + len(token) > 30:
                break
            name += ("_" if len(name) > 0 else "") + token

        # Replace special characters
        name = name.replace("/", "")

        return name.lower()

    def query(self, output, query):
        # Close existing file
        if self.csvout:
            self.csvout.close()

        self.csvout = open(os.path.join(os.path.dirname(output.name), "%s.csv" % self.filename(query)), "w")
        self.writer = csv.writer(self.csvout, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)

    def write(self, row):
        """
        Writes line to output file.

        Args:
            line: line to write
        """

        # Write csv line
        self.writer.writerow(row)

    def headers(self, output, names):
        # CSV header is different from standard report header
        self.write(["Date", "Study", "Study Link", "Journal", "Severe", "Severe Significant", "Severe Age Adjusted",
                    "Severe OR Calculated or Extracted", "Fatality", "Fatality Significant", "Fatality Age Adjusted",
                    "Fatality OR Calculated or Extracted", "Design", "Sample", "Study Population"])

    def buildRow(self, article, stat, sections):
        columns = []

        # Date
        columns.append(Query.date(article[0]))

        # Study
        columns.append(article[1])

        # Study Link
        columns.append(article[2])

        # Journal
        columns.append(article[3] if article[3] else article[4])

        # Severe
        columns.append(stat)

        # Severe Significant
        columns.append(None)

        # Severe Age Adjusted
        columns.append(None)

        # Severe OR Calculated or Extracted
        columns.append("Extracted" if stat else None)

        # Fatality
        columns.append(None)

        # Fatality Significant
        columns.append(None)

        # Fatality Age Adjusted
        columns.append(None)

        # Fatality OR Calculated or Extracted
        columns.append(None)

        # Design
        columns.append(Query.design(article[5]))

        # Sample
        columns.append(article[6])

        # Study Population
        columns.append(Query.text(article[8] if article[8] else article[7]))

        return columns

    def writeRow(self, output, row):
        self.write(row)
