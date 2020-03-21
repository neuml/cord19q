"""
Highlights module
"""

import itertools

import networkx

from .tokenizer import Tokenizer

class Highlights(object):
    """
    Methods to extract highlights from a list of text sections.
    """

    @staticmethod
    def build(sections, n=5):
        """
        Extracts highlights from a list of sections. This method uses textrank to find sections with the highest
        importance across the input list.

        Args:
            sections: input sections
            n: top n results to return

        Results:
            top n sections
        """

        # Run textrank algorithm and return best N matches
        uids = [uid for uid, _ in Highlights.textrank(sections)][:n]

        # Get related text for each match
        return [text for uid, text in sections if uid in uids]

    @staticmethod
    def textrank(sections):
        """
        Runs the textrank algorithm against the list of sections. Orders the list into descending order of importance
        given the list.

        Args:
            sections: list of sentences

        Returns:
            sorted list using the textrank algorithm
        """

        # Build the graph network
        graph = Highlights.buildGraph(sections)

        # Run pagerank
        rank = networkx.pagerank(graph, weight="weight")

        # Return items sorted by highest score first
        return sorted(list(rank.items()), key=lambda x: x[1], reverse=True)

    @staticmethod
    def buildGraph(nodes):
        """
        Builds a graph of nodes using input.

        Args:
            nodes: input graph nodes

        Returns:
            graph
        """

        graph = networkx.Graph()
        graph.add_nodes_from([uid for (uid, _) in nodes])

        # Tokenize nodes, store uid and tokens
        vectors = []
        for (uid, text) in nodes:
            tokens = set(Tokenizer.tokenize(text))

            if len(tokens) >= 3:
                vectors.append((uid, tokens))

        pairs = list(itertools.combinations(vectors, 2))

        # add edges to the graph
        for pair in pairs:
            node1, tokens1 = pair[0]
            node2, tokens2 = pair[1]

            # Add a graph edge and compute the cosine similarity for the weight
            graph.add_edge(node1, node2, weight=Highlights.jaccardIndex(tokens1, tokens2))

        return graph

    @staticmethod
    def jaccardIndex(set1, set2):
        """
        Jaccard index calculation used for similarity.

        Args:
            set1: input 1
            set2: input 2

        Returns:
            jaccard index
        """

        n = len(set1.intersection(set2))
        return n / float(len(set1) + len(set2) - n) if n > 0 else 0
