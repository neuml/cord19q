"""
Database module
"""

import os
import sqlite3

class Database(object):
    """
    Defines data structures and methods to store article content in SQLite.
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
        'Design': 'INTEGER',
        'Size': 'TEXT',
        'Sample': 'TEXT',
        'Method': 'TEXT',
        'Reference': 'TEXT',
        "Entry": 'DATETIME'
    }

    # Sections schema
    SECTIONS = {
        'Id': 'INTEGER PRIMARY KEY',
        'Article': 'TEXT',
        'Tags': 'TEXT',
        'Design': 'INTEGER',
        'Name': 'TEXT',
        'Text': 'TEXT',
        'Labels': 'TEXT'
    }

    # Stats schema
    STATS = {
        'Id': 'INTEGER PRIMARY KEY',
        'Article': 'TEXT',
        'Section': 'INTEGER',
        'Name': 'TEXT',
        'Value': 'TEXT'
    }

    # Citations schema
    CITATIONS = {
        'Title': 'TEXT PRIMARY KEY',
        'Mentions': 'INTEGER'
    }

    # SQL statements
    CREATE_TABLE = "CREATE TABLE IF NOT EXISTS {table} ({fields})"
    INSERT_ROW = "INSERT INTO {table} ({columns}) VALUES ({values})"
    CREATE_INDEX = "CREATE INDEX section_article ON sections(article)"

    def __init__(self, outdir):
        """
        Connects initializes a new output SQLite database.

        Args:
            outdir: output directory, if None uses default path
        """

        # Output database file
        dbfile = os.path.join(outdir, "articles.sqlite")

        # Delete existing file
        if os.path.exists(dbfile):
            os.remove(dbfile)

        # Create output database
        self.db = sqlite3.connect(dbfile)

        # Create database cursor
        self.cur = self.db.cursor()

        # Create articles table
        self.create(Database.ARTICLES, "articles")

        # Create sections table
        self.create(Database.SECTIONS, "sections")

        # Create stats table
        self.create(Database.STATS, "stats")

        # Create citations table
        self.create(Database.CITATIONS, "citations")

        # Start transaction
        self.cur.execute("BEGIN")

    def transaction(self):
        """
        Commits current transaction and creates a new one.
        """

        self.db.commit()
        self.cur.execute("BEGIN")

    def close(self):
        """
        Commits and closes the database.
        """

        self.db.commit()
        self.db.close()

    def create(self, table, name):
        """
        Creates a SQLite table.

        Args:
            table: table schema
            name: table name
        """

        columns = ['{0} {1}'.format(name, ctype) for name, ctype in table.items()]
        create = Database.CREATE_TABLE.format(table=name, fields=", ".join(columns))

        # pylint: disable=W0703
        try:
            self.cur.execute(create)
        except Exception as e:
            print(create)
            print("Failed to create table: " + e)

    def execute(self, sql):
        """
        Executes SQL statement against open cursor.

        Args:
            sql: SQL statement
        """

        self.cur.execute(sql)

    def insert(self, table, name, row):
        """
        Builds and inserts a row.

        Args:
            table: table object
            name: table name
            row: row to insert
        """

        # Build insert prepared statement
        columns = [name for name, _ in table.items()]
        insert = Database.INSERT_ROW.format(table=name,
                                            columns=", ".join(columns),
                                            values=("?, " * len(columns))[:-2])

        try:
            # Execute insert statement
            self.cur.execute(insert, self.values(table, row, columns))
        # pylint: disable=W0703
        except Exception as ex:
            print("Error inserting row: {}".format(row), ex)

    def values(self, table, row, columns):
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
            elif table[column].startswith("BOOLEAN"):
                values.append(1 if value == "TRUE" else 0)
            elif table[column].startswith("TEXT"):
                # Clean empty text and replace with None
                values.append(value if value and len(value.strip()) > 0 else None)
            else:
                values.append(value)

        return values
