"""
Sample module
"""

from .loe import LOE

class Sample(object):
    """
    Methods to extract the sample size of a study.
    """

    BASE = ["participants", "individuals", "men", "women", "children", "patients", "samples", "total"]
    CASES = ["cases", "sequences"] + BASE
    TRIALS = ["trials", "participants", "patients", "total"]

    KEYWORDS = {1: ["studies", "articles", "total"],
                2: TRIALS,
                3: TRIALS,
                4: CASES,
                5: CASES,
                6: CASES,
                7: CASES,
                8: BASE}

    @staticmethod
    def extract(sections, loe):
        """
        Attempts to extract the sample size for a given full-text document.

        Args:
            sections: list of sections
            loe: level of evidence for the study
        """

        if loe in Sample.KEYWORDS:
            keywords = Sample.KEYWORDS[loe]

            # Process full-text only if text meets certain criteria
            if LOE.accept(sections):
                # Score each section - filter to allowed sections
                scores = [(text, Sample.score(tokens, keywords)) for name, text, tokens in sections if not name or LOE.filter(name.lower())]

                # Filter to sections with a score > 0
                scores = [(text, score) for text, score in scores if score > 0]

                # Return top scored section
                return sorted(scores, key=lambda x: x[1], reverse=True)[0][0] if scores else None

        return None

    @staticmethod
    def score(tokens, keywords):
        """
        Scores keywords against tokens.

        Args:
            tokens: NLP tokens
            keywords: list of keywords to match

        Returns:
            score for section
        """

        # Rate NLP tokens matches
        score = sum([Sample.match(token, keywords) for token in tokens])
        if score:
            # Score action words
            actions = ["analyze", "collect", "include", "obtain", "review", "study"]
            score += sum([sum([1 if action in token.text.lower() else 0 for action in actions]) for token in tokens])

        return score

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
            return len([c for c in token.children if Sample.isnumber(c)]) > 0

        return False

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
