"""
Transforms raw CORD-19 data into an articles.sqlite SQLite database.
"""

import csv
import hashlib
import json
import os.path
import re
import sqlite3

from collections import Counter
from multiprocessing import Pool

from dateutil import parser
from nltk.tokenize import sent_tokenize

from .grammar import Grammar
from .metadata import Metadata
from .schema import Schema

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
        Execute.create(db, Schema.ARTICLES, "articles")

        # Create sections table
        Execute.create(db, Schema.SECTIONS, "sections")

        # Create stats table
        Execute.create(db, Schema.STATS, "stats")

        # Create citations table
        Execute.create(db, Schema.CITATIONS, "citations")

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
            sha1 hash id
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
        keywords = [r"2019[\-\s]?n[\-\s]?cov", "2019 novel coronavirus", "coronavirus 2019", r"coronavirus disease (?:20)?19",
                    r"covid(?:[\-\s]?19)?", r"n\s?cov[\-\s]?2019", r"sars-cov-?2", r"wuhan (?:coronavirus|cov|pneumonia)"]

        # Build regular expression for each keyword. Wrap term in word boundaries
        regex = "|".join(["\\b%s\\b" % keyword.lower() for keyword in keywords])

        tags = None
        for _, text in sections:
            # Look for at least one keyword match
            if re.findall(regex, text.lower()):
                tags = "COVID-19"

        return tags

    @staticmethod
    def filtered(sections, citations):
        """
        Returns a filtered list of text sections and citations. Duplicate and boilerplate text strings are removed.

        Args:
            sections: input sections
            citations: input citations

        Returns:
            filtered list of sections, citations
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

        return unique, list(set(citations))

    @staticmethod
    def files(row, uids):
        """
        Build a list of json file locations and names to parse.

        Args:
            row: input row
            uids: list of sha1 ids

        Returns:
            list of (directory, file name)
        """

        # Parse both PMC and PDF json if available, sections will be de-duplicated
        paths = [("pdf_json", uid + ".json") for uid in uids]
        if row["has_pmc_xml_parse"].lower() == "true":
            paths.append(("pmc_json", row["pmcid"] + ".xml.json"))

        return paths

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
        citations = []

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
            for location, filename in Execute.files(row, uids):
                # Build article path. Path has subset directory twice.
                article = os.path.join(directory, subset, subset, location, filename)

                try:
                    with open(article) as jfile:
                        data = json.load(jfile)

                        # Extract text from each section
                        for section in data["body_text"]:
                            # Section name and text
                            name = section["section"].upper() if len(section["section"].strip()) > 0 else None
                            text = section["text"].replace("\n", " ")

                            # Split text into sentences and add to sections
                            sections.extend([(name, x) for x in sent_tokenize(text)])

                        # Extract text from each citation
                        citations.extend([entry["title"] for entry in data["bib_entries"].values()])

                # pylint: disable=W0703
                except Exception as ex:
                    print("Error processing text file: {}".format(article), ex)

        # Filter sections and return
        return Execute.filtered(sections, citations)

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
        sections, citations = Execute.getSections(row, directory)

        # Get tags
        tags = Execute.getTags(sections)

        if tags:
            # Build NLP tokens for sections
            tokenslist = grammar.parse([text for _, text in sections])

            # Join NLP tokens with sections
            sections = [(name, text, tokenslist[x]) for x, (name, text) in enumerate(sections)]

            # Derive metadata fields
            design, keywords, size, sample, method, labels, risks = Metadata.parse(sections)

            # Add additional fields to each section
            sections = [(name, text, labels[x] if labels[x] else grammar.label(tokens), risks[x]) for x, (name, text, tokens) in enumerate(sections)]
        else:
            # Untagged section, create None default placeholders
            design, keywords, size, sample, method = None, None, None, None, None

            # Extend sections with empty columns
            sections = [(name, text, None, []) for name, text in sections]

            # Clear citations when not a tagged entry
            citations = None

        # Article row - id, source, published, publication, authors, title, tags, design, keywords, sample size
        #               sample section, samplemethod, reference
        article = (uid, row["source_x"], date, row["journal"], row["authors"], row["title"], tags, design, keywords, size,
                   sample, method, row["url"])

        return (uid, article, sections, tags, design, citations)

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

        # Article, section, stats indices
        aindex = 0
        sindex = 0
        tindex = 0

        # List of processed ids
        ids = set()
        citations = Counter()

        with Pool(os.cpu_count()) as pool:
            for uid, article, sections, tags, design, cite in pool.imap(Execute.process, Execute.stream(directory)):
                # Skip rows with ids that have already been processed
                if uid not in ids:
                    Execute.insert(db, Schema.ARTICLES, "articles", article)

                    citations.update(cite)

                    # Increment number of articles processed
                    aindex += 1
                    if aindex % 1000 == 0:
                        print("Inserted {} articles".format(aindex))

                    for name, text, labels, stats in sections:
                        # Section row - id, article, tags, design, name, text, labels
                        Execute.insert(db, Schema.SECTIONS, "sections", (sindex, uid, tags, design, name, text, labels))

                        for name, value in stats:
                            # Stats row - id, article, section, name, value
                            Execute.insert(db, Schema.STATS, "stats", (tindex, uid, sindex, name, value))
                            tindex += 1

                        sindex += 1

                    # Store article id as processed
                    ids.add(uid)

        for citation in citations.items():
            Execute.insert(db, Schema.CITATIONS, "citations", citation)

        print("Total articles inserted: {}".format(aindex))

        # Commit changes and close
        db.commit()
        db.close()
