"""
LOE module
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
    return "|".join(["\\b%s\\b" % term.lower() for term in terms])

class LOE(object):
    """
    Methods to determine the type of level of evidence contained within an article.
    """

    # Regular expressions for full text sections
    SYSTEMATIC_REVIEW_REGEX = regex(Vocab.SYSTEMATIC_REVIEW)
    RANDOMIZED_CONTROL_TRIAL_REGEX = regex(Vocab.RANDOMIZED_CONTROL_TRIAL)
    PSEUDO_RANDOMIZED_CONTROL_TRIAL_REGEX = regex(Vocab.PSEUDO_RANDOMIZED_CONTROL_TRIAL)
    RETROSPECTIVE_COHORT_REGEX = regex(Vocab.GENERIC_L3 + Vocab.RETROSPECTIVE_COHORT)
    MATCHED_CASE_CONTROL_REGEX = regex(Vocab.GENERIC_L3 + Vocab.GENERIC_CASE_CONTROL + Vocab.MATCHED_CASE_CONTROL)
    CROSS_SECTIONAL_CASE_CONTROL_REGEX = regex(Vocab.GENERIC_L3 + Vocab.GENERIC_CASE_CONTROL + Vocab.CROSS_SECTIONAL_CASE_CONTROL)
    TIME_SERIES_ANALYSIS_REGEX = regex(Vocab.TIME_SERIES_ANALYSIS)
    PREVALENCE_STUDY_REGEX = regex(Vocab.PREVALENCE_STUDY)
    COMPUTER_MODEL_REGEX = regex(Vocab.COMPUTER_MODEL)

    # Keywords for study names in titles
    TITLE_REGEX = [(regex(["systematic review", "meta-analysis"]), 1), (regex(["randomized control"]), 2),
                   (regex(["pseudo-randomized"]), 3), (regex(["retrospective cohort"]), 4),
                   (regex(["matched case"]), 5), (r"\bcross[\-\s]?sectional\b", 6),
                   (r"\btime[\-\s]?series\b", 7), (regex(["prevalence"]), 8)]

    # List of evidence categories
    CATEGORIES = [(COMPUTER_MODEL_REGEX, 1, None), (PREVALENCE_STUDY_REGEX, 1, None), (TIME_SERIES_ANALYSIS_REGEX, 2, None),
                  (CROSS_SECTIONAL_CASE_CONTROL_REGEX, 2, None), (MATCHED_CASE_CONTROL_REGEX, 2, ["match"]),
                  (RETROSPECTIVE_COHORT_REGEX, 2, ["retrospective"]), (PSEUDO_RANDOMIZED_CONTROL_TRIAL_REGEX, 3, ["random"]),
                  (RANDOMIZED_CONTROL_TRIAL_REGEX, 3, ["random"]), (SYSTEMATIC_REVIEW_REGEX, 4, ["systematic review", "meta-analysis"])]

    @staticmethod
    def label(sections):
        """
        Analyzes text fields of an article to determine the level of evidence.

        Labels definitions:

        1 - I. Systematic Review
        2 - II. Randomized Controlled Trial
        3 - III-1. Pseudo-Randomized Controlled Trial
        4 - III-2. Retrospective Cohort
        5 - III-2. Matched Case Control
        6 - III-2. Cross Sectional Control
        7 - III-3. Time Series Analysis
        8 - IV. Prevalence Study
        9 - IV. Computer Model
        0 - IV. Other (Default for no match)

        Args:
            sections: list of text sections

        Returns:
            (level of evidence (int), keyword match counts)
        """

        # LOE label, keywords
        label = (0, None)

        # Search titles for exact keyword match
        title = [text for name, text, _ in sections if name and name.lower() == "title"]
        title = " ".join(title).replace("\n", " ").lower()

        for regex, loe in LOE.TITLE_REGEX:
            count, keywords = LOE.matches(regex, title)

            # Return LOE and the keywords for title matches
            if count:
                return (loe, LOE.format(keywords))

        # Process full-text only if text meets certain criteria
        if LOE.accept(sections):
            # Filter to allowed sections and build full text copy of sections
            text = [text for name, text, _ in sections if not name or LOE.filter(name.lower())]
            text = " ".join(text).replace("\n", " ").lower()

            # Evaluate text against LOE rules engine
            if text:
                return LOE.evaluate(text)

        # Check title for mathematical/computer and label if no other labels applied (label = 0)
        if not label:
            # Allow partial matches
            count, keywords = LOE.matches(r"mathematical|computer|forecast", title)
            if count:
                # Return size of categories. Labels are inverted and computer models are first element. (1 indexed)
                label = (len(LOE.CATEGORIES), LOE.format(keywords))

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

        return any([LOE.find(section, "method") or LOE.find(section, "result") for section in sections])

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

        # Skip introduction, background and references sections
        # Skip discussion unless it's a results and discussion
        return not re.search(r"introduction|(?<!.*?results.*?)discussion|background|reference", name)

    @staticmethod
    def evaluate(text):
        """
        Evaluates LOE matches for text. This method will find a count of matches per category and run
        a set of results to determine if the matches should be accepted.

        Args:
            text: text to evaluate

        Returns:
            list (count, keyword matches) for each loe category
        """

        results = []

        for keywords, minimum, requirements in LOE.CATEGORIES:
            # Score by keyword counts
            count, matches = LOE.matches(keywords, text)
            accepted = False

            # Proceed if count is >= to the minimum required matches for the category
            if count and count >= minimum:
                # Accept if matches meet requirements or there are no requirements
                if not requirements or any([x in text for x in requirements]):
                    accepted = True

            results.append((count, matches) if accepted else (0, None))

        # Derive best match
        return LOE.top(results)

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
            label = (len(matches) - index, LOE.format(match[1]))

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
