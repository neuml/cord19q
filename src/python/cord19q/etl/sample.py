"""
Sample module
"""

from word2number import w2n

from .design import Design

class Sample(object):
    """
    Methods to extract the sample size of a study.
    """

    BASE = ["participants", "individuals", "men", "women", "children", "patients", "samples", "total"]
    CASES = ["cases", "sequences"] + BASE
    TRIALS = ["trials", "participants", "patients", "total"]

    KEYWORDS = {1: ["studies", "articles", "publications", "total"],
                2: TRIALS,
                3: TRIALS,
                4: CASES,
                5: BASE,
                6: CASES,
                7: BASE,
                8: CASES,
                9: CASES,
                10: BASE}

    SIZE_ACTIONS = ["analyze", "collect", "enroll", "include", "observe", "obtain", "recruit", "results", "review", "study", "studied"]
    METHOD_ACTIONS = ["collect", "enroll", "include", "method", "observe", "obtain", "recruit"]

    @staticmethod
    def extract(sections, design):
        """
        Attempts to extract the sample size for a given full-text document.

        Args:
            sections: list of sections
            design: study design type

        Returns:
            (sample size, sample section, sample method)
        """

        if design in Sample.KEYWORDS:
            keywords = Sample.KEYWORDS[design]

            # Process full-text only if text meets certain criteria
            if Design.accept(sections):
                size = Sample.size(sections, keywords)
                method = Sample.method(sections)

                return size + method

        return (None, None, None)

    @staticmethod
    def size(sections, keywords):
        """
        Extracts a sample size string and sample section

        Args:
            sections: input sections
            keywords: list of keywords to search

        Returns:
            (sample size, sample section)
        """

        # Score each section - filter to allowed sections
        scores = [Sample.score(tokens, keywords, Sample.SIZE_ACTIONS) + (text, ) \
                 for name, text, tokens in sections if not name or Design.filter(name.lower())]

        # Filter to sections with a score > 0
        scores = [(score, sample, text) for score, sample, text in scores if score > 0]

        # Return top scored section (sample size, sample section)
        return sorted(scores, key=lambda x: x[0], reverse=True)[0][1:] if scores else (None, None)

    @staticmethod
    def method(sections):
        """
        Extracts a sample method section.

        Args:
            sections: input sections

        Returns:
            (sample method)
        """

        # Score each section - filter to allowed sections
        scores = [Sample.score(tokens, None, Sample.METHOD_ACTIONS) + (text, ) \
                 for name, text, tokens in sections if not name or Design.filter(name.lower())]

        # Filter to sections with a score > 0
        scores = [(score, sample, text) for score, sample, text in scores if score > 0 and len(text) >= 10]

        # Return top scored section (method)
        return sorted(scores, key=lambda x: x[0], reverse=True)[0][2:] if scores else (None, )

    @staticmethod
    def score(tokens, keywords, actions):
        """
        Scores keywords against tokens.

        Args:
            tokens: NLP tokens
            keywords: list of keywords to match

        Returns:
            score for section
        """

        # Rate NLP tokens matches
        if keywords:
            # Extract matches and filter out empty results
            matches = [Sample.match(token, keywords) for token in tokens]
            matches = [match for match in matches if match]
        else:
            matches = False

        score = 1 if matches else 0
        if not keywords or score:
            score += sum([sum([1 if action in token.text.lower() else 0 for action in actions]) for token in tokens])

        # Return the score and sample size if any
        return (score, matches[0][0] if matches else None)

    @staticmethod
    def match(token, keywords):
        """
        Determines if token is in keywords. This also scans the NLP tokens dependency tree to see
        if it has at least one dependent number.

        Args:
            token: NLP token
            keywords: list of keywords to match

        Returns:
            True if token matches keywords
        """

        if token.text.lower() in keywords:
            return [Sample.tonumber(c.text) for c in token.children if Sample.isnumber(c)]

        return None

    @staticmethod
    def isnumber(token):
        """
        Determines if token represents a number.

        Args:
            token: input token

        Returns:
            True if this represents a number, False otherwise
        """

        # Returns true if following conditions are met:
        #  - Token POS is a number of it's all digits
        #  - Token DEP is in [amod, nummod]
        #  - None of the children are brackets (ignore citations [1], [2], etc)
        return (token.text.isdigit() or token.pos_ == "NUM") and token.dep_ in ["amod", "nummod"] and not any([c.text == "[" for c in token.children])

    @staticmethod
    def tonumber(token):
        """
        Attempts to convert a string to a number. Returns raw token if unsuccessful.

        Args:
            token: input token

        Returns:
            parsed token
        """

        try:
            return "%d" % w2n.word_to_num(token.replace(",", ""))
        # pylint: disable=W0702
        except:
            pass

        return token
