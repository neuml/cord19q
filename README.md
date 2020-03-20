cord19q: Exploring and indexing the CORD-19 dataset
======

![CORD19](https://pages.semanticscholar.org/hs-fs/hubfs/covid-image.png?width=300&name=covid-image.png)

COVID-19 Open Research Dataset (CORD-19) is a free resource of over 29,000 scholarly articles, including over 13,000 with full text, about COVID-19 and the coronavirus family of viruses for use by the global research community. The dataset can be found on [Semantic Scholar](https://pages.semanticscholar.org/coronavirus-research) and there is an active competition on [Kaggle](https://www.kaggle.com/allen-institute-for-ai/CORD-19-research-challenge).

This project is a Python project that builds a sentence embeddings index with FastText + BM25. Background on this method can be found in this [Medium article](https://towardsdatascience.com/building-a-sentence-embedding-index-with-fasttext-and-bm25-f07e7148d240) and an existing repository using this method [codequestion](https://github.com/neuml/codequestion).

### Tasks
The following files show queries for the Top 10 matches for each task provided in the CORD-19-research-challenge competition using this method.

* [What is known about transmission, incubation, and environmental stability?](./tasks/transmission.md)
* [What do we know about COVID-19 risk factors?](./tasks/risk-factors.md)
* [What do we know about virus genetics, origin, and evolution?](./tasks/virus-genome.md)
* [What do we know about non-pharmaceutical interventions?](./tasks/interventions.md)
* [What do we know about vaccines and therapeutics?](./tasks/vaccines.md)
* [What has been published about medical care?](./tasks/medical-care.md)
* [What has been published about information sharing and inter-sectoral collaboration?](./tasks/sharing.md)
* [What has been published about ethical and social science considerations?](./tasks/ethics.md)
* [What do we know about diagnostics and surveillance?](./tasks/diagnostics.md)

### Installation
You can use Git to clone the repository from GitHub and install it. It is recommended to do this in a Python Virtual Environment. 

    git clone https://github.com/neuml/cord19q.git
    cd cord19q
    pip install .

Python 3.5+ is supported

### Building a model
Download all the files in the Download CORD-19 section on [Semantic Scholar](https://pages.semanticscholar.org/coronavirus-research). Go the directory with the files
and run the following commands.

    cd <download_path>
    mv all_sources_metadata*.csv metadata.csv
    mkdir articles

For each tar.gz file run the following
    tar -xvzf <file.tar.gz>
    mv <extracted_directory>/* articles

Once completed, there should be a file called metadata.csv and an articles/ directory with all json articles.

To build the model locally:

    python -m cord19q.etl.execute <download_path>
    python -m cord19q.vectors
    python -m cord19q.index

The model will be stored in ~/.cord19

### Running queries
The fastest way to run queries is to start a cord19q shell

    cord19q

A prompt will come up. Queries can be typed directly into the console.

### Building a report file
A report file is simply a markdown file created from a list of queries. An example:

    python -m cord19q.report tasks/diagnostics.txt

Once complete a file named tasks/diagnostics.md will be created.