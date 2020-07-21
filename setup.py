# pylint: disable = C0111
from setuptools import find_packages, setup

with open("README.md", "r") as f:
    DESCRIPTION = f.read()

setup(name="cord19q",
      version="3.0.0",
      author="NeuML",
      description="CORD-19 Analysis",
      long_description=DESCRIPTION,
      long_description_content_type="text/markdown",
      url="https://github.com/neuml/cord19q",
      project_urls={
          "Documentation": "https://github.com/neuml/cord19q",
          "Issue Tracker": "https://github.com/neuml/cord19q/issues",
          "Source Code": "https://github.com/neuml/cord19q",
      },
      license="Apache 2.0: http://www.apache.org/licenses/LICENSE-2.0",
      keywords="search embedding machine-learning nlp covid-19 medical scientific papers",
      python_requires=">=3.6",
      install_requires=[
          "paperetl @ git+https://github.com/neuml/paperetl",
          "paperai @ git+https://github.com/neuml/paperai"
      ],
      classifiers=[
          "License :: OSI Approved :: Apache Software License",
          "Operating System :: OS Independent",
          "Programming Language :: Python :: 3",
          "Topic :: Software Development",
          "Topic :: Text Processing :: Indexing",
          "Topic :: Utilities"
      ])
