"""
Transforms raw CORD-19 data into an articles.sqlite SQLite database.
"""

import csv
import hashlib
import json
import os.path
import re
import sqlite3

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

class Execute(object):
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
        'Keywords': 'TEXT',
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
        Execute.create(db, Execute.ARTICLES, "articles")

        # Create sections table
        Execute.create(db, Execute.SECTIONS, "sections")

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
        create = Execute.CREATE_TABLE.format(table=name, fields=", ".join(columns))

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
        insert = Execute.INSERT_ROW.format(table=name,
                                           columns=", ".join(columns),
                                           values=("?, " * len(columns))[:-2])

        try:
            # Execute insert statement
            db.execute(insert, Execute.values(table, row, columns))
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

        # Keyword patterns to search for
        keywords = [r"2019[\-\s]?n\s?cov", "2019 novel coronavirus", r"coronavirus 2019", r"coronavirus disease (?:20)?19",
                    r"covid(?:[\- ]19)?", r"n\s?cov 2019", "sars-cov-2", r"wuhan (?:coronavirus|pneumonia)"]

        # Build regular expression for each keyword. Wrap term in word boundaries
        regex = "|".join(["\\b%s\\b" % keyword.lower() for keyword in keywords])

        tags = None
        for _, text in sections:
            # Look for at least one keyword match
            if re.findall(regex, text.lower()):
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

        # Boilerplate text to ignore
        boilerplate = ["COVID-19 resource centre", "permission to make all its COVID", "WHO COVID database"]

        for name, text in sections:
            # Add unique text that isn't boilerplate text
            if not text in keys and not any([x in text for x in boilerplate]):
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

        # Determine file location based on parse type
        location = "pdf_json" if row["has_pdf_parse"] else "pmc_json"

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
                article = os.path.join(directory, subset, subset, location, uid + ".json")

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
        return Execute.filtered(sections)

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
        uid = Execute.getId(row)

        # Published date
        date = Execute.getDate(row)

        # Get text sections
        sections = Execute.getSections(row, directory)

        # Get tags
        tags = Execute.getTags(sections)

        if tags:
            # Convert text to NLP token list
            sections = [(name, text, grammar.parse(text)) for name, text in sections]

            # Derive metadata fields
            loe, keywords, sample = Metadata.parse(sections)

            # Build labels column
            sections = [(name, text, grammar.label(tokens)) for name, text, tokens in sections]
        else:
            # Untagged section, create None default placeholders
            loe, keywords, sample = None, None, None

            # Extend sections with None columns
            sections = [(name, text, None) for name, text in sections]

        # Article row - id, source, published, publication, authors, title, tags, reference
        article = (uid, row["source_x"], date, row["journal"], row["authors"], row["title"], tags, loe, keywords, sample, row["url"])

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
        db = Execute.init(output)

        # Article and section indices
        aindex = 0
        sindex = 0

        # List of processed ids
        ids = set()

        with Pool(os.cpu_count()) as pool:
            for uid, article, sections, tags in pool.imap(Execute.process, Execute.stream(directory)):
                # Skip rows with ids that have already been processed
                if uid not in ids:
                    Execute.insert(db, Execute.ARTICLES, "articles", article)

                    # Increment number of articles processed
                    aindex += 1
                    if aindex % 1000 == 0:
                        print("Inserted {} articles".format(aindex))

                    for name, text, labels in sections:
                        # Section row - id, article, name, text, tags, labels
                        Execute.insert(db, Execute.SECTIONS, "sections", (sindex, uid, name, text, tags, labels))
                        sindex += 1

                    # Store article id as processed
                    ids.add(uid)

        print("Total articles inserted: {}".format(aindex))

        # Commit changes and close
        db.commit()
        db.close()
