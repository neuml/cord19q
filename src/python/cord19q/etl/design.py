"""
Design module
"""

from collections import Counter

import regex as re

from .vocab import Vocab

def regex(terms):
    """
    Builds a regular expression OR matched string from the terms. Each string is wrapped in
    word boundary (\b) flags to only allow complete phrase matches. Module level function used
    to allow calling from class body.

    Args:
        terms: list of terms

    Returns:
        terms regex
    """

    # Build regular expression for each term. Wrap term in word boundaries
    return "|".join(["\\b%s\\b" % term.lower() for term in set(terms)])

class Design(object):
    """
    Methods to determine the study design within an article.
    """

    # Systematic Review / Meta-Analysis
    SYSTEMATIC_REVIEW_REGEX = regex(Vocab.SYSTEMATIC_REVIEW)

    # Experimental Studies
    RANDOMIZED_REGEX = regex(Vocab.RANDOMIZED)
    NON_RANDOMIZED_REGEX = regex(Vocab.NON_RANDOMIZED)

    # Prospective Studies
    ECOLOGICAL_REGRESSION_REGEX = regex(Vocab.ECOLOGICAL_REGRESSION)
    PROSPECTIVE_COHORT_REGEX = regex(Vocab.PROSPECTIVE_COHORT)
    TIME_SERIES_REGEX = regex(Vocab.TIME_SERIES)

    # Retrospective Studies
    RETROSPECTIVE_COHORT_REGEX = regex(Vocab.RETROSPECTIVE_COHORT)
    CROSS_SECTIONAL_REGEX = regex(Vocab.CROSS_SECTIONAL)
    CASE_CONTROL_REGEX = regex(Vocab.CASE_CONTROL)

    # Case Studies
    CASE_STUDY_REGEX = regex(Vocab.CASE_STUDY)

    # Computer Simulations
    SIMULATION_REGEX = regex(Vocab.SIMULATION)

    # Keywords for study names in titles
    TITLE_REGEX = [(regex(["systematic review", "meta-analysis"]), 1), (regex(["randomized"]), 2), (r"non[\-\s]randomized", 3),
                   (regex(["ecological regression"]), 4), (regex(["prospective cohort"]), 5), (r"\btime[\-\s]?series\b", 6),
                   (regex(["retrospective cohort"]), 7), (r"\bcross[\-\s]?sectional\b", 8), (r"\bcase[\-\s]control\b", 9),
                   (regex(["case study"]), 10)]

    # List of evidence categories
    CATEGORIES = [(SIMULATION_REGEX, 1, None), (CASE_STUDY_REGEX, 2, None), (CASE_CONTROL_REGEX, 2, None),
                  (CROSS_SECTIONAL_REGEX, 2, None), (RETROSPECTIVE_COHORT_REGEX, 2, None), (TIME_SERIES_REGEX, 2, None),
                  (PROSPECTIVE_COHORT_REGEX, 2, None), (ECOLOGICAL_REGRESSION_REGEX, 2, None), (NON_RANDOMIZED_REGEX, 3, ["random"]),
                  (RANDOMIZED_REGEX, 3, ["random"]), (SYSTEMATIC_REVIEW_REGEX, 4, ["systematic review", "meta-analysis"])]

    @staticmethod
    def label(sections):
        """
        Analyzes text fields of an article to determine the level of evidence.

        Labels definitions:

         1 - Systematic Review
         2 - Experimental Study (Randomized)
         3 - Experimental Study (Non-Randomized)
         4 - Ecological Regression
         5 - Prospective Cohort
         6 - Time Series Analysis
         7 - Retrospective Cohort
         8 - Cross Sectional
         9 - Case Control
        10 - Case Study
        11 - Simulation
         0 - Unknown Design (Default for no match)

        Args:
            sections: list of text sections

        Returns:
            (level of evidence (int), keyword match counts)
        """

        # Design label, keywords
        label = (0, None)

        # Search titles for exact keyword match
        title = [text for name, text, _ in sections if name and name.lower() == "title"]
        title = " ".join(title).replace("\n", " ").lower()

        for regex, design in Design.TITLE_REGEX:
            count, keywords = Design.matches(regex, title)

            # Return design and the keywords for title matches
            if count:
                return (design, Design.format(keywords))

        # Process full-text only if text meets certain criteria
        if Design.accept(sections):
            # Filter to allowed sections and build full text copy of sections
            text = [text for name, text, _ in sections if not name or Design.filter(name.lower())]
            text = " ".join(text).replace("\n", " ").lower()

            # Evaluate text against design rules engine
            if text:
                return Design.evaluate(text)

        # Check title for simulation and label if no other labels applied (label = 0)
        if not label:
            # Allow partial matches
            count, keywords = Design.matches(r"computer|estimate|forecast|mathematical", title)
            if count:
                # Return size of categories. Labels are inverted and computer models are first element. (1 indexed)
                label = (len(Design.CATEGORIES), Design.format(keywords))

        return label

    @staticmethod
    def accept(sections):
        """
        Requires at least one instance of the word method or result in the text of the article.

        Args:
            sections: sections

        Returns:
            True if word method or result present in text
        """

        return any([Design.find(section, "method") or Design.find(section, "result") for section in sections])

    @staticmethod
    def find(section, token):
        """
        Searches section for the occurance of a token. Accepts partial word matches.

        Args:
            section: input section
            token: token to search for

        Returns:
            True if token found, False otherwise
        """

        # Unpack section
        name, text, _ = section

        return (name and token in name.lower()) or (text and token in text.lower())

    @staticmethod
    def filter(name):
        """
        Filters a section name. Returns True if name is a title, method or results section.

        Args:
            name: section name

        Returns:
            True if section should be analyzed, False otherwise
        """

        # Skip background, introduction and reference sections
        # Skip discussion unless it's a results and discussion
        return not re.search(r"background|(?<!.*?results.*?)discussion|introduction|reference", name)

    @staticmethod
    def evaluate(text):
        """
        Evaluates design matches for text. This method will find a count of matches per category and run
        a set of results to determine if the matches should be accepted.

        Args:
            text: text to evaluate

        Returns:
            list (count, keyword matches) for each design category
        """

        results = []

        for keywords, minimum, requirements in Design.CATEGORIES:
            # Score by keyword counts
            count, matches = Design.matches(keywords, text)
            accepted = False

            # Proceed if count is >= to the minimum required matches for the category
            if count and count >= minimum:
                # Accept if matches meet requirements or there are no requirements
                if not requirements or any([x in text for x in requirements]):
                    accepted = True

            results.append((count, matches) if accepted else (0, None))

        # Derive best match
        return Design.top(results)

    @staticmethod
    def matches(keywords, text):
        """
        Finds all keyword matches within a block of text. Wraps keywords in word boundaries to prevent
        partial matching of a word.

        Args:
            keywords: keywords regex
            text: text to search

        Returns:
            list of matches
        """

        if keywords:
            matches = re.findall(keywords, text, overlapped=True)
            if matches:
                return (len(matches), matches)

        return (0, None)

    @staticmethod
    def top(matches):
        """
        Searches a matches list and returns the top match by count. If no match with
        a count > 0 is found, 0 is returned.

        Args:
            matches: list of (count, keywords)

        Returns:
            top (label, keywords) match or (0, None) if no matches found
        """

        label = (0, None)

        counts = [count for count, _ in matches]
        best = max(counts)
        if best:
            # Get index of best match
            index = counts.index(best)
            match = matches[index]

            # Label is inverted index of CATEGORIES list (1 indexed)
            label = (len(matches) - index, Design.format(match[1]))

        return label

    @staticmethod
    def format(match):
        """
        Builds a formatted match string from match.

        Args:
            match: list of matching keyword

        Returns:
            formatting string of 'keyword match': count
        """

        # Build keyword match string
        counts = sorted(Counter(match).items(), key=lambda x: x[1], reverse=True)
        return ", ".join(["'%s': %d" % (key, value) for key, value in counts])
