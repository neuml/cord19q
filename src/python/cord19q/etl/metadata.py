"""
Metadata module. Derives additional metadata fields.

Credit to https://www.kaggle.com/savannareid for providing keywords and analysis.

Background can be found in these discussions:
https://www.kaggle.com/allen-institute-for-ai/CORD-19-research-challenge/discussion/139355
https://www.kaggle.com/allen-institute-for-ai/CORD-19-research-challenge/discussion/140185
"""

from .design import Design
from .sample import Sample

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
        sample = Sample.extract(sections, design)

        return (design, keywords, sample)
