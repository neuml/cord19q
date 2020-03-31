"""
Study module.

Credit to https://www.kaggle.com/savannareid for providing keywords and analysis.

Background can be found in this discussion
https://www.kaggle.com/allen-institute-for-ai/CORD-19-research-challenge/discussion/139355
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

class Study(object):
    """
    Methods to determine the type of study/level of evidence contained within an article.
    """

    GENERIC_L1 = ["pooled odds ratio", "Cohen's d", "difference in means", "difference between means",
                  "d-pooled", "pooled adjusted odds ratio", "pooled or", "pooled aor", "pooled risk ratio", "pooled rr",
                  "pooled relative risk"]

    SYSTEMATIC_REVIEW = ["systematic review", "meta-analysis"]

    RANDOMIZED_CONTROL_TRIAL = ["treatment arm", "placebo", "blind", "double-blind", "control arm", "rct", "randomized", "treatment effect"]

    GENERIC_L3 = ["risk factor analysis", "risk factors", "etiology", "logistic regression", "odds ratio", "adjusted odds ratio", "aor", "β",
                  "log odds", "incidence", "exposure status", "electronic medical records", "chart review", "medical records review"]

    RETROSPECTIVE_COHORT = ["cohort", "retrospective cohort", "retrospective chart review", "association", "associated with"]

    GENERIC_CASE_CONTROL = ["data collection instrument", "survey instrument", "association", "associated with", "response rate",
                            "questionnaire development", "psychometric evaluation of instrument", "eligibility criteria", "recruitment",
                            "potential confounders", "non-response bias"]

    MATCHED_CASE_CONTROL = ["cohort", "number of controls per case", "matching criteria"]

    CROSS_SECTIONAL_CASE_CONTROL = ["prevalence survey"]

    TIME_SERIES_ANALYSIS = ["survival analysis", "time-to-event analysis", "weibull", "gamma", "lognormal", "estimation", "kaplan-meier",
                            "hazard ratio", "cox proportional hazards", "etiology", "median time to event", "cohort", "censoring", "truncated",
                            "right-censored", "non-comparative study", "longitudinal"]

    PREVALENCE_STUDY = ["prevalence", "syndromic surveillance", "surveillance", "registry data", "frequency", "risk factors", "etiology",
                        "cross-sectional survey", "logistic regression", "odds ratio", "log odds", "adjusted odds ratio", "aor", "β",
                        "data collection instrument", "survey instrument", "association", "associated with"]

    # Regular expression for full text sections
    SYSTEMATIC_REVIEW_REGEX = regex(GENERIC_L1 + SYSTEMATIC_REVIEW)
    RANDOMIZED_CONTROL_TRIAL_REGEX = regex(RANDOMIZED_CONTROL_TRIAL)
    PSEUDO_RANDOMIZED_CONTROL_TRIAL_REGEX = None
    RETROSPECTIVE_COHORT_REGEX = regex(GENERIC_L3 + RETROSPECTIVE_COHORT)
    MATCHED_CASE_CONTROL_REGEX = regex(GENERIC_L3 + GENERIC_CASE_CONTROL + MATCHED_CASE_CONTROL)
    CROSS_SECTIONAL_CASE_CONTROL_REGEX = regex(GENERIC_L3 + GENERIC_CASE_CONTROL + CROSS_SECTIONAL_CASE_CONTROL)
    TIME_SERIES_ANALYSIS_REGEX = regex(TIME_SERIES_ANALYSIS)
    PREVALENCE_STUDY_REGEX = regex(PREVALENCE_STUDY)

    # Regular expressions for titles
    TITLE_SYSTEMATIC_REVIEW_REGEX = regex(SYSTEMATIC_REVIEW)

    # List of evidence categories
    CATEGORIES = [(PREVALENCE_STUDY_REGEX, 1), (TIME_SERIES_ANALYSIS_REGEX, 1), (CROSS_SECTIONAL_CASE_CONTROL_REGEX, 2),
                  (MATCHED_CASE_CONTROL_REGEX, 2), (RETROSPECTIVE_COHORT_REGEX, 2), (PSEUDO_RANDOMIZED_CONTROL_TRIAL_REGEX, 2),
                  (RANDOMIZED_CONTROL_TRIAL_REGEX, 3), (SYSTEMATIC_REVIEW_REGEX, 4)]

    @staticmethod
    def label(sections):
        """
        Analyzes text fields of an article to determine the study design/level of evidence.

        Labels definitions:

        1 - I. Systematic Review
        2 - II. Randomized Controlled Trial
        3 - III-1. Pseudo-Randomized Controlled Trial. Not currently detected.
        4 - III-2. Retrospective Cohort
        5 - III-2. Matched Case Control
        6 - III-2. Cross Sectional Control
        7 - III-3. Time Series Analysis
        8 - IV. Prevalence Study

        Args:
            sections: list of text sections

        Returns:
            study label (int) or None if no matches found
        """

        # If Systematic Review or Meta-Analysis in title, return a 1 label
        title = [text for name, text in sections if name and name.lower() == "title"]
        title = " ".join(title).replace("\n", " ").lower()

        if Study.count(Study.TITLE_SYSTEMATIC_REVIEW_REGEX, title):
            return 1

        # Process full-text only if text meets certain criteria
        if Study.accept(sections):
            # Filter to allowed sections and build full text copy of sections
            text = [text for name, text in sections if not name or Study.filter(name.lower())]
            text = " ".join(text).replace("\n", " ").lower()

            if text:
                # Score text by keyword category
                counts = [(Study.count(keywords, text), minimum) for keywords, minimum in Study.CATEGORIES]

                # Require at least minimum matches, which is set per category
                counts = [count if count >= minimum else 0 for count, minimum in counts]

                # Get level of evidence label if there are keyword matches
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

        return any([Study.find(section, "method") or Study.find(section, "result") for section in sections])

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
        name, text = section

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
