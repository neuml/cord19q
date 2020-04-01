"""
Metadata module. Derives additional metadata fields.

Credit to https://www.kaggle.com/savannareid for providing keywords and analysis.

Background can be found in these discussions:
https://www.kaggle.com/allen-institute-for-ai/CORD-19-research-challenge/discussion/139355
https://www.kaggle.com/allen-institute-for-ai/CORD-19-research-challenge/discussion/140185
"""

import regex as re

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

    return "|".join([r"\b%s\b" % term.lower() for term in terms])

class Metadata(object):
    """
    Methods to derive additional metadata fields for a study contained within an article.
    """

    @staticmethod
    def parse(sections):
        """
        Parses metadata fields contained within an article.

        Args:
            sections: list of text sections

        Returns:
            metadata fields as tuple
        """

        # Level of Evidence
        loe = LOE.label(sections)

        # Extract best candidate sentence with study sample
        sample = Sample.extract(sections, loe)

        return (loe, sample)

class LOE(object):
    """
    Methods to determine the type of level of evidence contained within an article.
    """

    SYSTEMATIC_REVIEW = ["systematic review", "meta-analysis", "pooled odds ratio", "Cohen's d", "difference in means", "difference between means",
                         "d-pooled", "pooled adjusted odds ratio", "pooled or", "pooled aor", "pooled risk ratio", "pooled rr",
                         "pooled relative risk"]

    RANDOMIZED_CONTROL_TRIAL = ["treatment arm", "placebo", "blind", "double-blind", "control arm", "rct", "randomized", "treatment effect"]

    GENERIC_L3 = ["risk factor analysis", "risk factors", "etiology", "logistic regression", "odds ratio", "adjusted odds ratio", "aor",
                  "log odds", "incidence", "exposure status", "electronic medical records", "chart review", "medical records review"]

    RETROSPECTIVE_COHORT = ["cohort", "retrospective cohort", "retrospective chart review", "association between", "associated with"]

    GENERIC_CASE_CONTROL = ["data collection instrument", "survey instrument", "association between", "associated with", "response rate",
                            "questionnaire development", "psychometric evaluation of instrument", "eligibility criteria", "recruitment",
                            "potential confounders", "non-response bias"]

    MATCHED_CASE_CONTROL = ["cohort", "number of controls per case", "matching criteria"]

    CROSS_SECTIONAL_CASE_CONTROL = ["prevalence survey"]

    TIME_SERIES_ANALYSIS = ["survival analysis", "time-to-event analysis", "weibull", "gamma", "lognormal", "estimation", "kaplan-meier",
                            "hazard ratio", "cox proportional hazards", "etiology", "median time to event", "cohort", "censoring", "truncated",
                            "right-censored", "non-comparative study", "longitudinal"]

    PREVALENCE_STUDY = ["prevalence", "syndromic surveillance", "surveillance", "registry data", "frequency", "risk factors", "etiology",
                        "cross-sectional survey", "logistic regression", "odds ratio", "log odds", "adjusted odds ratio", "aor",
                        "data collection instrument", "survey instrument", "association", "associated with"]

    COMPUTER_MODEL = ["mathematical model", "mathematical modeling", "computer model", "computer modeling", "model simulation"]

    # Regular expression for full text sections
    SYSTEMATIC_REVIEW_REGEX = regex(SYSTEMATIC_REVIEW)
    RANDOMIZED_CONTROL_TRIAL_REGEX = regex(RANDOMIZED_CONTROL_TRIAL)
    PSEUDO_RANDOMIZED_CONTROL_TRIAL_REGEX = None
    RETROSPECTIVE_COHORT_REGEX = regex(GENERIC_L3 + RETROSPECTIVE_COHORT)
    MATCHED_CASE_CONTROL_REGEX = regex(GENERIC_L3 + GENERIC_CASE_CONTROL + MATCHED_CASE_CONTROL)
    CROSS_SECTIONAL_CASE_CONTROL_REGEX = regex(GENERIC_L3 + GENERIC_CASE_CONTROL + CROSS_SECTIONAL_CASE_CONTROL)
    TIME_SERIES_ANALYSIS_REGEX = regex(TIME_SERIES_ANALYSIS)
    PREVALENCE_STUDY_REGEX = regex(PREVALENCE_STUDY)
    COMPUTER_MODEL_REGEX = regex(COMPUTER_MODEL)

    # Keywords for study names in titles
    TITLE_REGEX = [(regex(["systematic review", "meta-analysis"]), 1), (regex(["randomized control"]), 2),
                   (regex(["pseudo randomized"]), 3), (regex(["retrospective cohort"]), 4),
                   (regex(["matched case control"]), 5), (regex(["cross sectional"]), 6),
                   (regex(["time series analysis"]), 7), (regex(["prevalence study"]), 8),
                   (regex(["mathematical model"]), 9)]

    # List of evidence categories
    CATEGORIES = [(COMPUTER_MODEL_REGEX, 1), (PREVALENCE_STUDY_REGEX, 1), (TIME_SERIES_ANALYSIS_REGEX, 1),
                  (CROSS_SECTIONAL_CASE_CONTROL_REGEX, 2), (MATCHED_CASE_CONTROL_REGEX, 2), (RETROSPECTIVE_COHORT_REGEX, 2),
                  (PSEUDO_RANDOMIZED_CONTROL_TRIAL_REGEX, 2), (RANDOMIZED_CONTROL_TRIAL_REGEX, 3), (SYSTEMATIC_REVIEW_REGEX, 4)]

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

        Args:
            sections: list of text sections

        Returns:
            level of evidence (int) or None if no matches found
        """

        # Search titles for exact keyword match
        title = [text for name, text, _ in sections if name and name.lower() == "title"]
        title = " ".join(title).replace("\n", " ").lower()

        for regex, loe in LOE.TITLE_REGEX:
            if LOE.count(regex, title):
                return loe

        # Process full-text only if text meets certain criteria
        if LOE.accept(sections):
            # Filter to allowed sections and build full text copy of sections
            text = [text for name, text, _ in sections if not name or LOE.filter(name.lower())]
            text = " ".join(text).replace("\n", " ").lower()

            if text:
                # Score text by keyword category
                counts = [(LOE.count(keywords, text), minimum) for keywords, minimum in LOE.CATEGORIES]

                # Require at least minimum matches, which is set per category
                counts = [count if count >= minimum else 0 for count, minimum in counts]

                # Get level of design label if there are keyword matches
                return len(counts) - counts.index(max(counts)) if max(counts) > 0 else None

        return None

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

        # Skip introduction, background, discussion and references sections
        return not re.search(r"introduction|background|discussion|reference", name)

    @staticmethod
    def count(keywords, text):
        """
        Counts the number of times a list of keywords. Wraps keywords in word boundaries to prevent
        partial matching of a word.

        Args:
            keywords: keywords regex
            text: text to search
        """

        if keywords:
            return len(re.findall(keywords, text, overlapped=True))

        return 0

class Sample(object):
    """
    Methods to extract the sample size of a study.
    """

    BASE = ["participants", "individuals", "children", "patients", "samples", "total"]
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
            score += sum([token.text.lower() in actions for token in tokens])

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

        # True if POS is a number of it's all digits and none of the children are brackets
        # scispacy model is detecting 2019-ncov as a number
        return (token.text.isdigit() or token.pos_ == "NUM") and not any([c.text == "[" for c in token.children])
