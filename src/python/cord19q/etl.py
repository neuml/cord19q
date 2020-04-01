"""
Transforms raw CORD-19 data into an articles.sqlite SQLite database.
"""

import csv
import hashlib
import json
import os.path
import re
import sqlite3
import sys

from multiprocessing import Pool

from dateutil import parser
from nltk.tokenize import sent_tokenize

from .grammar import Grammar
from .metadata import Metadata

# Global helper for multi-processing support
# pylint: disable=W0603
GRAMMAR = None

def getGrammar():
    """
    Multiprocessing helper method. Gets (or first creates then gets) a global grammar object to
    be accessed in a new subprocess.

    Returns:
        Grammar
    """

    global GRAMMAR

    if not GRAMMAR:
        GRAMMAR = Grammar()

    return GRAMMAR

class Etl(object):
    """
    Transforms raw csv and json files into an articles.sqlite SQLite database.
    """

    # Articles schema
    ARTICLES = {
        'Id': 'TEXT PRIMARY KEY',
        'Source': 'TEXT',
        'Published': 'DATETIME',
        'Publication': "TEXT",
        'Authors': 'TEXT',
        'Title': 'TEXT',
        'Tags': 'TEXT',
        'LOE': 'INTEGER',
        'Sample': 'TEXT',
        'Reference': 'TEXT'
    }

    # Sections schema
    SECTIONS = {
        'Id': 'INTEGER PRIMARY KEY',
        'Article': 'TEXT',
        'Name': 'TEXT',
        'Text': 'TEXT',
        'Tags': 'TEXT',
        'Labels': 'TEXT'
    }

    # SQL statements
    CREATE_TABLE = "CREATE TABLE IF NOT EXISTS {table} ({fields})"
    INSERT_ROW = "INSERT INTO {table} ({columns}) VALUES ({values})"

    @staticmethod
    def init(output):
        """
        Connects initializes a new output SQLite database.

        Args:
            output: output directory, if None uses default path

        Returns:
            connection to new SQLite database
        """

        # Default path if not provided
        if not output:
            output = os.path.join(os.path.expanduser("~"), ".cord19", "models")

        # Create if output path doesn't exist
        os.makedirs(output, exist_ok=True)

        # Output database file
        dbfile = os.path.join(output, "articles.sqlite")

        # Delete existing file
        if os.path.exists(dbfile):
            os.remove(dbfile)

        # Create output database
        db = sqlite3.connect(dbfile)

        # Create articles table
        Etl.create(db, Etl.ARTICLES, "articles")

        # Create sections table
        Etl.create(db, Etl.SECTIONS, "sections")

        return db

    @staticmethod
    def create(db, table, name):
        """
        Creates a SQLite table.

        Args:
            db: database connection
            table: table schema
            name: table name
        """

        columns = ['{0} {1}'.format(name, ctype) for name, ctype in table.items()]
        create = Etl.CREATE_TABLE.format(table=name, fields=", ".join(columns))

        # pylint: disable=W0703
        try:
            db.execute(create)
        except Exception as e:
            print(create)
            print("Failed to create table: " + e)

    @staticmethod
    def insert(db, table, name, row):
        """
        Builds and inserts a row.

        Args:
            db: database connection
            table: table object
            name: table name
            row: row to insert
        """

        # Build insert prepared statement
        columns = [name for name, _ in table.items()]
        insert = Etl.INSERT_ROW.format(table=name,
                                       columns=", ".join(columns),
                                       values=("?, " * len(columns))[:-2])

        try:
            # Execute insert statement
            db.execute(insert, Etl.values(table, row, columns))
        # pylint: disable=W0703
        except Exception as ex:
            print("Error inserting row: {}".format(row), ex)

    @staticmethod
    def values(table, row, columns):
        """
        Formats and converts row into database types based on table schema.

        Args:
            table: table schema
            row: row tuple
            columns: column names

        Returns:
            Database schema formatted row tuple
        """

        values = []
        for x, column in enumerate(columns):
            # Get value
            value = row[x]

            if table[column].startswith("INTEGER"):
                values.append(int(value) if value else 0)
            elif table[column] == "BOOLEAN":
                values.append(1 if value == "TRUE" else 0)
            elif table[column] == "TEXT":
                # Clean empty text and replace with None
                values.append(value if value and len(value.strip()) > 0 else None)
            else:
                values.append(value)

        return values

    @staticmethod
    def getId(row):
        """
        Gets id for this row. Builds one from the title if no body content is available.

        Args:
            row: input row

        Returns:
            sha1 hash ids
        """

        # Use sha1 provided, if available
        uid = row["sha"].split("; ")[0] if row["sha"] else None
        if not uid:
            # Fallback to sha1 of title
            uid = hashlib.sha1(row["title"].encode("utf-8")).hexdigest()

        return uid

    @staticmethod
    def getDate(row):
        """
        Parses the publish date from the input row.

        Args:
            row: input row

        Returns:
            publish date
        """

        date = row["publish_time"]

        if date:
            try:
                if date.isdigit() and len(date) == 4:
                    # Default entries with just year to Jan 1
                    date += "-01-01"

                return parser.parse(date)

            # pylint: disable=W0702
            except:
                # Skip parsing errors
                return None

        return None

    @staticmethod
    def getTags(sections):
        """
        Searches input sections for matching keywords. If found, returns the keyword tag.

        Args:
            sections: list of text sections

        Returns:
            tags
        """

        keywords = ["2019-ncov", "2019 novel coronavirus", "coronavirus 2019", "coronavirus disease 19", "covid-19", "covid 19", "ncov-2019",
                    "sars-cov-2", "wuhan coronavirus", "wuhan pneumonia", "wuhan virus"]

        tags = None
        for _, text in sections:
            if any(x in text.lower() for x in keywords):
                tags = "COVID-19"

        return tags

    @staticmethod
    def filtered(sections):
        """
        Returns a filtered list of text sections. Duplicate and boilerplate text strings are removed.

        Args:
            sections: input sections

        Returns:
            filtered list of sections
        """

        # Use list to preserve insertion order
        unique = []
        keys = set()

        for name, text in sections:
            if not text in keys and not "COVID-19 resource centre" in text:
                unique.append((name, text))
                keys.add(text)

        return unique

    @staticmethod
    def getSections(row, directory):
        """
        Reads title, abstract and body text for a given row. Text is returned as a list of sections.

        Args:
            row: input row
            directory: input directory

        Returns:
            list of text sections
        """

        sections = []

        # Get ids and subset
        uids = row["sha"].split("; ") if row["sha"] else None
        subset = row["full_text_file"]

        # Add title and abstract sections
        for name in ["title", "abstract"]:
            text = row[name]
            if text:
                # Remove leading and trailing []
                text = re.sub(r"^\[", "", text)
                text = re.sub(r"\]$", "", text)

                sections.extend([(name.upper(), x) for x in sent_tokenize(text)])

        if uids and subset:
            for uid in uids:
                # Build article path. Path has subset directory twice.
                article = os.path.join(directory, subset, subset, uid + ".json")

                try:
                    with open(article) as jfile:
                        data = json.load(jfile)

                        # Extract text from each section
                        for section in data["body_text"]:
                            # Section name
                            name = section["section"].upper() if len(section["section"].strip()) > 0 else None

                            # Split text into sentences and add to sections
                            sections.extend([(name, x) for x in sent_tokenize(section["text"])])

                # pylint: disable=W0703
                except Exception as ex:
                    print("Error processing text file: {}".format(article), ex)

        # Filter sections and return
        return Etl.filtered(sections)

    @staticmethod
    def stream(directory):
        """
        Generator that yields rows from a metadata.csv file. The directory is also included.

        Args:
            directory
        """

        with open(os.path.join(directory, "metadata.csv"), mode="r") as csvfile:
            for row in csv.DictReader(csvfile):
                yield (row, directory)

    @staticmethod
    def process(params):
        """
        Processes a single row

        Args:
            params: (row, directory)

        Returns:
            (id, article, sections)
        """

        # Get grammar handle
        grammar = getGrammar()

        # Unpack parameters
        row, directory = params

        # Get uid
        uid = Etl.getId(row)

        # Published date
        date = Etl.getDate(row)

        # Get text sections
        sections = Etl.getSections(row, directory)

        # Get tags
        tags = Etl.getTags(sections)

        if tags:
            # Convert text to NLP token list
            sections = [(name, text, grammar.parse(text)) for name, text in sections]

            # Derive metadata fields
            loe, sample = Metadata.parse(sections)

            # Build labels column
            sections = [(name, text, grammar.label(tokens)) for name, text, tokens in sections]
        else:
            # Untagged section, create None default placeholders
            loe, sample = None, None

            # Extend sections with None columns
            sections = [(name, text, None) for name, text in sections]

        # Article row - id, source, published, publication, authors, title, tags, reference
        article = (uid, row["source_x"], date, row["journal"], row["authors"], row["title"], tags, loe, sample, row["url"])

        return (uid, article, sections, tags)

    @staticmethod
    def run(directory, output):
        """
        Main execution method.

        Args:
            directory: input directory
            output: output directory path
        """

        print("Building articles.sqlite from {}".format(directory))

        # Initialize database
        db = Etl.init(output)

        # Article and section indices
        aindex = 0
        sindex = 0

        # List of processed ids
        ids = set()

        with Pool(os.cpu_count()) as pool:
            for uid, article, sections, tags in pool.imap(Etl.process, Etl.stream(directory)):
                # Skip rows with ids that have already been processed
                if uid not in ids:
                    Etl.insert(db, Etl.ARTICLES, "articles", article)

                    # Increment number of articles processed
                    aindex += 1
                    if aindex % 1000 == 0:
                        print("Inserted {} articles".format(aindex))

                    for name, text, labels in sections:
                        # Section row - id, article, name, text, tags, labels
                        Etl.insert(db, Etl.SECTIONS, "sections", (sindex, uid, name, text, tags, labels))
                        sindex += 1

                    # Store article id as processed
                    ids.add(uid)

        print("Total articles inserted: {}".format(aindex))

        # Commit changes and close
        db.commit()
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        Etl.run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
