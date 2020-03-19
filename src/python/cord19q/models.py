"""
Models module
"""

import os
import os.path

class Models(object):
    """
    Common methods for generating data paths.
    """

    @staticmethod
    def basePath(create=False):
        """
        Base data path - ~/.cord19

        Args:
            create: if directory should be created

        Returns:
            path
        """

        # Get model cache path
        path = os.path.join(os.path.expanduser("~"), ".cord19")

        # Create directory if required
        if create:
            os.makedirs(path, exist_ok=True)

        return path

    @staticmethod
    def modelPath(create=False):
        """
        Model path for name

        Args:
            create: if directory should be created

        Returns:
            path
        """

        path = os.path.join(Models.basePath(), "models")

        # Create directory if required
        if create:
            os.makedirs(path, exist_ok=True)

        return path

    @staticmethod
    def testPath(source, name):
        """
        Builds path to a test data file.

        Args:
            source: test source name
            name: file name

        Returns:
            path
        """

        return os.path.join(Models.basePath(), "test", source, name)

    @staticmethod
    def vectorPath(name, create=False):
        """
        Vector path for name

        Args:
            name: vectors name
            create: if directory should be created

        Returns:
            path
        """

        path = os.path.join(Models.basePath(), "vectors")

        # Create directory path if required
        if create:
            os.makedirs(path, exist_ok=True)

        # Append file name to path
        return os.path.join(path, name)
