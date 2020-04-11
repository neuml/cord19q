"""
Query module
"""

import datetime
import re
import sys

import html2text
import mdv

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
    def search(embeddings, cur, query, topn):
        """
        Executes an embeddings search for the input query. Each returned result is resolved
        to the full section row.

        Args:
            embeddings: embeddings model
            cur: database cursor
            query: query text
            topn: number of results to return

        Returns:
            search results
        """

        results = []

        # Tokenize search query
        query = Tokenizer.tokenize(query)

        for uid, score in embeddings.search(query, topn):
            if score >= 0.6:
                cur.execute("SELECT Article, Text FROM sections WHERE id = ?", [uid])
                results.append((uid, score) + cur.fetchone())

        return results

    @staticmethod
    def highlights(results, topn):
        """
        Builds a list of highlights for the search results. Returns top ranked sections by importance
        over the result list.

        Args:
            results: search results
            topn: number of highlights to extract

        Returns:
            top ranked sections
        """

        sections = {}
        for uid, score, _, text in results:
            # Filter out lower scored results
            if score >= 0.35:
                sections[text] = (uid, text)

        return Highlights.build(sections.values(), topn)

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
    def authors(authors):
        """
        Formats a short authors string

        Args:
            authors: full authors string

        Returns:
            short author string
        """

        if authors:
            authors = authors.split("; ")[0]
            if "," in authors:
                authors = authors.split(",")[0]
            else:
                authors = authors.split()[-1]

            return "%s et al" % authors

        return None

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

            return date.strftime("%Y-%m-%d")

        return None

    @staticmethod
    def text(text):
        """
        Formats match text.

        Args:
            text: input text

        Returns:
            formatted text
        """

        if text:
            # Remove reference links ([1], [2], etc)
            text = re.sub(r"\s*[\[(][0-9, ]+[\])]\s*", " ", text)

            # Remove •
            text = text.replace("•", "")

            # Remove http links
            text = re.sub(r"http.+?\s", " ", text)

            # Remove boilerplate text
            text = re.sub(r"doi\s?:\s?(bioRxiv|medRxiv) preprint", " ", text)
            text = text.replace("All Rights Reserved", " ")

        return text

    @staticmethod
    def design(design):
        """
        Formats a study design field.

        Args:
            design: study design integer

        Returns:
            Study Design string
        """

        # Study design type mapping
        mapping = {0:"Unknown", 1:"Meta analysis", 2:"Randomized control trial", 3:"Non-randomized trial",
                   4:"Ecological regression", 5:"Prospective cohort", 6:"Time series analysis", 7:"Retrospective cohort",
                   8:"Cross-sectional", 9:"Case control", 10: "Case study", 11:"Simulation"}

        return mapping[design]

    @staticmethod
    def sample(size, text):
        """
        Formats a sample string.

        Args:
            size: Sample size
            text: Sample text

        Returns:
            Formatted sample text
        """

        return "[%s] %s" % (size, Query.text(text)) if size else Query.text(text)

    @staticmethod
    def stat(cur, article, name):
        """
        Looks up the named stat for an article.

        Args:
            article: article id
            name: stat name

        Returns:
            stat string if found
        """

        name = "%" + name + "%"
        cur.execute("SELECT Value FROM stats WHERE article = ? AND (name LIKE ? or value LIKE ?)", [article, name, name])
        stat = cur.fetchone()
        return stat[0] if stat else None

    @staticmethod
    def query(embeddings, db, query, topn):
        """
        Executes a query against the embeddings model.

        Args:
            embeddings: embeddings model
            db: open SQLite database
            query: query string
            n: number of query results
        """

        # Default to 10 results if not specified
        topn = topn if topn else 10

        cur = db.cursor()

        print(Query.render("#Query: %s" % query, theme="729.8953") + "\n")

        # Query for best matches
        results = Query.search(embeddings, cur, query, topn)

        # Extract top sections as highlights
        print(Query.render("# Highlights"))
        for highlight in Query.highlights(results, int(topn / 5)):
            print(Query.render("## - %s" % Query.text(highlight)))

        print()

        # Get results grouped by document
        documents = Query.documents(results)

        print(Query.render("# Articles") + "\n")

        # Print each result, sorted by max score descending
        for uid in sorted(documents, key=lambda k: sum([x[0] for x in documents[k]]), reverse=True):
            cur.execute("SELECT Title, Published, Publication, Design, Size, Sample, Method, Id, Reference FROM articles WHERE id = ?", [uid])
            article = cur.fetchone()

            print("Title: %s" % article[0])
            print("Published: %s" % Query.date(article[1]))
            print("Publication: %s" % article[2])
            print("Design: %s" % Query.design(article[3]))
            print("Severity: %s" % Query.stat(cur, article[6], query))
            print("Sample: %s" % Query.sample(article[4], article[5]))
            print("Method: %s" % Query.text(article[6]))
            print("Id: %s" % article[7])
            print("Reference: %s" % article[8])

            # Print top matches
            for score, text in documents[uid]:
                print(Query.render("## - (%.4f): %s" % (score, Query.text(text)), html=False))

            print()

    @staticmethod
    def run(query, topn=None, path=None):
        """
        Executes a query against an index.

        Args:
            query: input query
            topn: number of results
            path: model path
        """

        # Load model
        embeddings, db = Models.load(path)

        # Query the database
        Query.query(embeddings, db, query, topn)

        # Free resources
        Models.close(db)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        Query.run(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None, sys.argv[3] if len(sys.argv) > 3 else None)
