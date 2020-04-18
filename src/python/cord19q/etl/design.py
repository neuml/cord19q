"""
Design module

Labels definitions:

  1 - Meta analysis
  2 - Randomized control trial
  3 - Non-randomized trial
  4 - Prospective cohort
  5 - Time-series analysis
  6 - Retrospective cohort
  7 - Cross-sectional
  8 - Case control
  9 - Case study
 10 - Simulation
  0 - Other
"""

import csv
import os
import sys

from itertools import groupby

import regex as re

from sklearn.ensemble import RandomForestClassifier

from ..models import Models

from .study import StudyModel

class Design(StudyModel):
    """
    Prediction model used to classify study designs.
    """

    def __init__(self):
        """
        Builds a new Design model.

        Args:
            training: path to training data
            models: path to models
        """

        super(Design, self).__init__()

        # Keywords to use as features
        self.keywords = StudyModel.getKeywords()

    def predict(self, sections):
        # Build features array for document
        features = [self.features(sections)]

        return self.model.predict(features)[0]

    def create(self):
        return RandomForestClassifier(n_estimators=110, max_depth=22, max_features=0.24, random_state=0)

    def hyperparams(self):
        return {"n_estimators": range(100, 200),
                "max_depth": range(15, 30),
                "max_features": [x / 100 for x in range(15, 30)],
                "random_state": 0}

    def data(self, training):
        # Unique ids
        uids = {}

        # Features
        features = []
        labels = []

        # Unpack training data
        training, db = training
        cur = db.cursor()

        # Read training data, convert to features
        with open(training, mode="r") as csvfile:
            for row in csv.DictReader(csvfile):
                uids[row["id"]] = int(row["label"])

            # Build id list for each uid batch
            for idlist in self.batch(list(uids.keys()), 999):
                # Get section text and transform to features
                cur.execute("SELECT name, text, article FROM sections WHERE article in (%s) ORDER BY id" % ",".join(["?"] * len(idlist)), idlist)
                f, l = self.transform(cur.fetchall(), uids)

                # Combine lists from each batch
                features.extend(f)
                labels.extend(l)

        print("Loaded %d rows" % len(features))

        return features, labels

    def batch(self, uids, size):
        """
        Splits uids into batches.

        Args:
            uids: uids
            size: batch size

        Returns:
            list of lists split into batch size
        """

        return [uids[x:x + size] for x in range(0, len(uids), size)]

    def transform(self, rows, uids):
        """
        Transforms a list of rows into features and labels.

        Args:
            rows: input rows
            uids: uid to label mapping

        Returns:
            (features, labels)
        """

        features = []
        labels = []

        # Retrieve all rows and group by article id
        for uid, sections in groupby(rows, lambda x: x[2]):
            # Get sections as list
            sections = list(sections)

            # Save features and label
            features.append(self.features(sections))
            labels.append(uids[uid])

        return features, labels

    def features(self, sections):
        """
        Builds a features vector from input text.

        Args:
            sections: list of sections

        Returns:
            features vector as a list
        """

        # Build full text from sections
        text = [text for name, text, _ in sections if not name or StudyModel.filter(name.lower())]
        text = " ".join(text).replace("\n", " ").lower()

        # Build feature vector from regular expressions of common study design terms
        vector = []
        for keyword in self.keywords:
            vector.append(len(re.findall("\\b%s\\b" % keyword.lower(), text)))

        return vector

    @staticmethod
    def run(training, path, optimize):
        """
        Trains a new model.

        Args:
            training: path to training file
            path: models path
            optimize: if hyperparameter optimization should be enabled
        """

        # Default path as it's used for both reading input and the model output path
        if not path:
            path = Models.modelPath()

        # Load models path
        _, db = Models.load(path)

        try:
            # Train the model
            model = Design()
            model.train((training, db), optimize)

            # Save the model
            print("Saving model to %s" % path)
            model.save(os.path.join(path, "design"))

        finally:
            Models.close(db)

if __name__ == "__main__":
    Design.run(sys.argv[1] if len(sys.argv) > 1 else None,
               sys.argv[2] if len(sys.argv) > 2 else None,
               sys.argv[3] == "1" if len(sys.argv) > 3 else False)
