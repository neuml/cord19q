"""
Query module
"""

import os
import os.path
import sqlite3
import sys

import html2text
import mdv

# pylint: disable = E0401
from .embeddings import Embeddings
from .models import Models
from .tokenizer import Tokenizer

class Query(object):
    """
    Methods to query an embeddings index.
    """

    @staticmethod
    def escape(text):
        """
        Escapes text to work around issues with mdv double escaping characters.

        Args:
            text: input text

        Returns:
            escaped text
        """

        text = text.replace("<", "¿")
        text = text.replace(">", "Ñ")
        text = text.replace("&", "ž")

        return text

    @staticmethod
    def unescape(text):
        """
        Un-escapes text to work around issues with mdv double escaping characters.

        Args:
            text: input text

        Returns:
            unescaped text
        """

        text = text.replace("¿", "<")
        text = text.replace("Ñ", ">")
        text = text.replace("ž", "&")

        return text

    @staticmethod
    def render(text, theme="592.2129", html=True, tab_length=0):
        """
        Renders input text to formatted text ready to send to the terminal.

        Args:
            text: input html text

        Returns:
            text formatted for print to terminal
        """

        if html:
            # Convert HTML
            parser = html2text.HTML2Text()
            parser.body_width = 0
            text = parser.handle(text)

            text = Query.escape(text)

        text = mdv.main(text, theme=theme, c_theme="953.3567", cols=180, tab_length=tab_length)

        if html:
            text = Query.unescape(text)

        return text.strip()

    @staticmethod
    def load(path):
        """
        Loads an embeddings model and db database.

        Args:
            path: model path, if None uses default path

        Returns:
            (embeddings, db handle)
        """

        # Default path if not provided
        if not path:
            path = Models.modelPath()

        dbfile = os.path.join(path, "articles.db")

        if os.path.isfile(os.path.join(path, "config")):
            print("Loading model from %s" % path)
            embeddings = Embeddings()
            embeddings.load(path)
        else:
            print("ERROR: loading model: ensure model is present")
            raise FileNotFoundError("Unable to load model from %s" % path)

        # Connect to database file
        db = sqlite3.connect(dbfile)

        return (embeddings, db)

    @staticmethod
    def query(embeddings, db, query):
        """
        Executes a query against the embeddings model.

        Args:
            embeddings: embeddings model
            db: open SQLite database
            query: query string
        """

        cur = db.cursor()

        query = Tokenizer.tokenize(query)
        print(Query.render("#Query: %s" % query, theme="729.8953"))

        for uid, score in embeddings.search(query, 10):
            cur.execute("SELECT Article, Text FROM sections WHERE id = ?", [uid])
            section = cur.fetchone()

            if score >= 0.0:
                # Unpack match
                article, text = section

                cur.execute("SELECT Title, Authors, Published, Publication, Id, Reference from articles where id = ?", [article])
                article = cur.fetchone()

                print("Title: %s" % article[0])
                print("Authors: %s" % article[1])
                print("Published: %s" % article[2])
                print("Publication: %s" % article[3])
                print("Id: %s" % article[4])
                print("Reference: %s" % article[5])
                print(Query.render("#Match (%.4f): %s" % (score, text), html=False))

                print()

    @staticmethod
    def close(db):
        """
        Closes a SQLite database database.

        Args:
            db: open database
        """

        # Free database resources
        db.close()

    @staticmethod
    def run(query, path):
        """
        Executes a query against an index.

        Args:
            query: input query
            path: model path
        """

        # Load model
        embeddings, db = Query.load(path)

        # Query the database
        Query.query(embeddings, db, query)

        # Free resources
        Query.close(db)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        Query.run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
