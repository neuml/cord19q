"""
Query module
"""

import datetime
import os
import os.path
import re
import sqlite3
import sys

import html2text
import mdv

# pylint: disable = E0401
from .embeddings import Embeddings
from .highlights import Highlights
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
    def search(embeddings, cur, query, n=10):
        """
        Executes an embeddings search for the input query. Each returned result is resolved
        to the full section row.

        Args:
            embeddings: embeddings model
            cur: database cursor
            query: query text
            n: number of results to return

        Returns:
            search results
        """

        results = []

        # Tokenize search query
        query = Tokenizer.tokenize(query)

        for uid, score in embeddings.search(query, n):
            cur.execute("SELECT Article, Text FROM sections WHERE id = ?", [uid])
            results.append((uid, score) + cur.fetchone())

        return results

    @staticmethod
    def highlights(results, n=2):
        """
        Builds a list of highlights for the search results. Returns top ranked sections by importance
        over the result list.

        Args:
            results: search results
            n: number of highlights to extract

        Returns:
            top ranked sections
        """

        sections = {}
        for uid, score, _, text in results:
            # Filter out lower scored results
            if score >= 0.35:
                sections[text] = (uid, text)

        return Highlights.build(sections.values(), n)

    @staticmethod
    def documents(results):
        """
        Processes search results and groups by article.

        Args:
            results: search results

        Returns:
            results grouped by article
        """

        documents = {}

        # Group by article
        for _, score, article, text in results:
            if article not in documents:
                documents[article] = set()

            documents[article].add((score, text))

        # Sort based on section id, which preserves original order
        for uid in documents:
            documents[uid] = sorted(list(documents[uid]), reverse=True)

        return documents

    @staticmethod
    def date(date):
        """
        Formats a date string.

        Args:
            date: input date string

        Returns:
            formatted date
        """

        if date:
            date = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

            # 1/1 dates had no month/day specified, use only year
            if date.month == 1 and date.day == 1:
                return date.strftime("%Y")

            return date.strftime("%b %d, %Y")

    @staticmethod
    def text(text):
        """
        Formats match text.

        Args:
            text: input text

        Returns:
            formatted text
        """

        # Remove reference links ([1], [2], etc)
        text = re.sub(r"\s*[\[(][0-9, ]+[\])]\s*", " ", text)

        # Remove •
        text = text.replace("•", "")

        return text

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

        print(Query.render("#Query: %s" % query, theme="729.8953") + "\n")

        # Query for best matches
        results = Query.search(embeddings, cur, query)

        # Extract top sections as highlights
        print(Query.render("# Highlights"))
        for highlight in Query.highlights(results):
            print(Query.render("## - %s" % Query.text(highlight)))

        print()

        # Get results grouped by document
        documents = Query.documents(results)

        print(Query.render("# Articles") + "\n")

        # Print each result, sorted by max score descending
        for uid in sorted(documents, key=lambda k: sum([x[0] for x in documents[k]]), reverse=True):
            cur.execute("SELECT Title, Authors, Published, Publication, Id, Reference from articles where id = ?", [uid])
            article = cur.fetchone()

            print("Title: %s" % article[0])
            print("Authors: %s" % article[1])
            print("Published: %s" % article[2])
            print("Publication: %s" % article[3])
            print("Id: %s" % article[4])
            print("Reference: %s" % article[5])

            # Print top matches
            for score, text in documents[uid]:
                print(Query.render("## - (%.4f): %s" % (score, text), html=False))

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
