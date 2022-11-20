# cord19q: COVID-19 Open Research Dataset (CORD-19) Analysis

*This repository is an archive of work done with the CORD-19 challenge in 2020. If you'd like to programatically process medical literature, see [paperai](https://github.com/neuml/paperai)*

COVID-19 Open Research Dataset (CORD-19) is a free resource of scholarly articles, aggregated by a coalition of leading research groups, covering COVID-19 and the coronavirus family of viruses. The dataset can be found on [Semantic Scholar](https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/historical_releases.html) and [Kaggle](https://www.kaggle.com/allen-institute-for-ai/CORD-19-research-challenge).

The cord19q project builds an index over the CORD-19 dataset to assist with analysis and data discovery. A series of COVID-19 related research topics were explored to identify relevant articles and help find answers to key scientific questions.

### Tasks
A full list of Kaggle CORD-19 Challenge tasks can be found in this [notebook](https://www.kaggle.com/davidmezzetti/cord-19-analysis-with-sentence-embeddings). This notebook and corresponding report notebooks won 🏆 7 awards 🏆 in the Kaggle CORD-19 Challenge.

The latest tasks are also stored in the [cord19q repository](https://github.com/neuml/cord19q/tree/master/tasks).

## Installation
cord19q can be installed directly from GitHub using pip. Using a Python Virtual Environment is recommended.

    pip install git+https://github.com/neuml/cord19q

Python 3.6+ is supported

## Building a model
cord19q relies on [paperetl](https://github.com/neuml/paperetl) to parse and load the CORD-19 dataset into a SQLite database. [paperai](https://github.com/neuml/paperai) is then used to run an AI-Powered Literature Review over the CORD-19 dataset for a list of query tasks. 

The following links show how to parse, load and index CORD-19.

- [Build CORD-19 articles database](https://github.com/neuml/paperetl#load-cord-19-into-sqlite)
- [Build CORD-19 index](https://github.com/neuml/paperai#building-a-model)

The model will be stored in ~/.cord19

## Building a report file
A report file is simply a markdown file created from a list of queries. An example:

    python -m paperai.report tasks/risk-factors.yml

Once complete a file named tasks/risk-factors.md will be created.

## Running queries
The fastest way to run queries is to start a paperai shell

    paperai

A prompt will come up. Queries can be typed directly into the console.
