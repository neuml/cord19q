"""
Extractor module
"""

import string

import regex as re

from transformers.pipelines import pipeline

from ..index import Index
from ..tokenizer import Tokenizer

class Extractor(object):
    """
    Class that uses an extractive question-answering model to extract content from a given text context.
    """

    def __init__(self, embeddings, cur):
        """
        Builds a new extractor.

        Args:
            embeddings: embeddings model
            cur: database cursor
        """

        path = "/data/sources/cord19/docs/bert/test"
        self.model = pipeline("question-answering", model=path, tokenizer=path)

        self.embeddings = embeddings
        self.cur = cur

    def extract(self, uid, queue):
        """
        Extracts answers to input questions for a document. This method runs queries against a single document,
        finds the top n best matches and uses that as the question context. A question-answering model is then run against
        the context for the input question, with the answer returned.

        Args:
            uid: document id
            queue: input queue (name, query, question)

        Returns:
            extracted answer
        """

        # Retrieve indexed document text for article
        self.cur.execute(Index.SECTION_QUERY + " AND article = ?", [uid])

        # Tokenize text
        sections, tokenlist = [], []
        for sid, name, text in self.cur.fetchall():
            if not name or not re.search(Index.SECTION_FILTER, name.lower()):
                tokens = Tokenizer.tokenize(text)
                if tokens:
                    sections.append((sid, text))
                    tokenlist.append(tokens)

        # Build question-context pairs
        names, questions, contexts, results = [], [], [], []
        for name, query, question in queue:
            query = Tokenizer.tokenize(query)
            matches = []

            scores = self.embeddings.similarity(query, tokenlist)
            for x, score in enumerate(scores):
                matches.append(sections[x] + (score,))

            # Build context using top n best matching sections
            topn = sorted(matches, key=lambda x: x[2], reverse=True)[:3]
            context = " ".join([text for _, text, _ in sorted(topn, key=lambda x: x[0])])

            names.append(name)
            questions.append(question)
            contexts.append(context)

        # Run pipeline, require output to be a list
        answers = self.model(question=questions, context=contexts)
        if not isinstance(answers, list):
            answers = [answers]

        # Extract and format answer
        for x, answer in enumerate(answers):
            if answer["score"] >= 0.05:
                results.append((names[x], answer["answer"].strip(string.punctuation)))
            else:
                results.append((names[x], ""))

            print(contexts[x], "\n  ", questions[x], "\n  ", answer)

        print("\n\n")

        return results
