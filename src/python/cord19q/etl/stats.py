"""
Extracts study statistics. Statistics include numerical measurements included within the study.
"""

import re

class Stats(object):
    """
    Methods to extract study statistics.
    """

    @staticmethod
    def extract(tokens):
        """
        Attempts to extract a risk factor from a list of tokens.

        Args:
            tokens: list of tokens

        Returns:
            list of risk factor stats or None if not found
        """

        risks = []

        for entity in tokens.ents:
            stat = Stats.getStat(tokens, entity)
            if stat:
                risks.append((entity.text, stat))

        return risks

    @staticmethod
    def getStat(tokens, entity):
        """
        Extracts a statistic within a list of tokens.

        Args:
            tokens: list of tokens
            entity: entity text

        Returns:
            statistic
        """

        stat = []

        index = None
        if len(tokens) > entity.end and tokens[entity.end].is_left_punct:
            index = entity.end
        if len(tokens) > (entity.end + 1) and tokens[entity.end + 1].is_left_punct:
            index = entity.end + 1

        while index and index < len(tokens):
            if not tokens[index].text.isspace():
                # Append token to stat
                stat.append(tokens[index].text)

            if tokens[index].is_right_punct:
                break

            index += 1

        text = " ".join(stat)
        if Stats.hasRiskStat(text) and re.search(r"(\d\.)+", text):
            # Remove leading and training parens/brackets
            return re.sub(r"^[(\[]|[)\]]$", "", text).strip()

        return None

    @staticmethod
    def hasRiskStat(text):
        """
        Determines if text represents a risk measurement.

        Args:
            text: input text

        Returns:
            True if text represents a measurement, False otherwise
        """

        return re.search(r"\bOR\b|\bHR\b|\bCI\b", text) or re.search("\baor\b|\bodds ratio\b|\bhazard ratio\b", text.lower())
