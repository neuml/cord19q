"""
Metadata module. Derives additional metadata fields.
"""

from .design import Design
from .sample import Sample
from .stats import Stats

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

        # Study design type
        design, keywords = Design.label(sections)

        # Extract best candidate sentence with study sample
        size, sample, method = Sample.extract(sections, design)

        # Label each section
        labels = []
        stats = []
        for _, text, tokens in sections:
            label, stat = Stats.extract(tokens)

            if text == sample:
                label = "SAMPLE_SIZE"
            elif text == method:
                label = "SAMPLE_METHOD"

            labels.append(label)
            stats.append(stat)

        return (design, keywords, size, sample, method, labels, stats)
