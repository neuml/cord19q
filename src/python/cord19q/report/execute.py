"""
Report factory module
"""

import os.path

from .csvr import CSV
from .excel import XLSX
from .markdown import Markdown

from ..models import Models

class Execute(object):
    """
    Creates a Report
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

        if render == "csv":
            return CSV(embeddings, cur)
        elif render == "md":
            return Markdown(embeddings, cur)
        elif render == "xlsx":
            return XLSX(embeddings, cur)

        return None

    @staticmethod
    def run(task, topn=None, category=None, render=None, path=None):
        """
        Reads a list of queries from a task file and builds a report.

        Args:
            task: input task file
            topn: number of results
            category: report category, used to decide what columns to include
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
        report = Execute.create(render, embeddings, db)

        # Generate output filename
        outfile = "%s.%s" % (os.path.splitext(task)[0], render)

        # Stream report to file
        with open(outfile, report.mode()) as output:
            # Initialize report
            report.open(output)

            # Build the report
            report.build(queries, topn, category, output)

            # Close the report
            report.close()

        # Free any resources
        report.cleanup(outfile)

        # Free resources
        Models.close(db)
