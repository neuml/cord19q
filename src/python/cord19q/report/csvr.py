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
        if "Severe" in names:
            self.names = ["Date", "Study", "Study Link", "Journal", "Severe", "Severe Significant", "Severe Age Adjusted",
                          "Severe OR Calculated or Extracted", "Fatality", "Fatality Significant", "Fatality Age Adjusted",
                          "Fatality OR Calculated or Extracted", "Design", "Sample", "Study Population", "Sample Text", "Matches"]
        else:
            self.names = ["Date", "Study", "Study Link", "Journal", "Design", "Sample", "Study Population", "Sample Text", "Matches"]

        # Write out column names
        self.write(self.names)

    def buildRow(self, article, stat, sections):
        columns = {}

        # Date
        columns["Date"] = Query.date(article[0])

        # Study
        columns["Study"] = article[1]

        # Study Link
        columns["Study Link"] = article[2]

        # Journal
        columns["Journal"] = article[3] if article[3] else article[4]

        # Severe
        columns["Severe"] = stat

        # Severe Significant
        columns["Severe Significant"] = None

        # Severe Age Adjusted
        columns["Severe Age Adjusted"] = None

        # Severe OR Calculated or Extracted
        columns["Severe OR Calculated or Extracted"] = "Extracted" if stat else None

        # Fatality
        columns["Fatality"] = None

        # Fatality Significant
        columns["Fatality Significant"] = None

        # Fatality Age Adjusted
        columns["Fatality Age Adjusted"] = None

        # Fatality OR Calculated or Extracted
        columns["Fatality OR Calculated or Extracted"] = None

        # Design
        columns["Design"] = Query.design(article[5])

        # Sample
        columns["Sample"] = article[6]

        # Study Population
        columns["Study Population"] = Query.text(article[8] if article[8] else article[7])

        # Sample Text
        columns["Sample Text"] = article[7]

        # Top Matches
        columns["Matches"] = "\n\n".join([Query.text(text) for _, text in sections])

        return columns

    def writeRow(self, output, row):
        self.write(row)
