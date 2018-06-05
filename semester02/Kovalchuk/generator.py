#!/usr/bin/env python

import random

from itertools import combinations
from graph import Graph


class GraphBuilder(object):
    def __init__(self, rand=None):
        self._random = rand if rand is not None else random.Random()
        self._num_nodes = 10
        self._correlation = 0.5
        self._min_node_weight = 1
        self._max_node_weight = 100
        self._min_link_weight = 1
        self._max_link_weight = 100

    def _validate(self):
        assert self._num_nodes > 0
        assert 0 < self._correlation <= 1
        assert 0 < self._min_node_weight <= self._max_node_weight
        assert 0 < self._min_link_weight <= self._max_link_weight

    def set_num_nodes(self, num_nodes):
        self._num_nodes = int(num_nodes)
        return self

    def set_correlation(self, correlation):
        self._correlation = correlation
        return self

    def set_node_weight(self, min_weight=None, max_weight=None):
        assert 0 < int(min_weight) <= int(max_weight)
        if min_weight is not None:
            self._min_node_weight = int(min_weight)
        if max_weight is not None:
            self._max_node_weight = int(max_weight)
        return self

    def set_link_weight(self, min_weight=None, max_weight=None):
        assert 0 < int(min_weight) <= int(max_weight)
        if min_weight is not None:
            self._min_link_weight = int(min_weight)
        if max_weight is not None:
            self._max_link_weight = int(max_weight)
        return self

    def build(self) -> Graph:
        self._validate()
        rand = self._random
        all_links = list(combinations(range(self._num_nodes), 2))
        rand.shuffle(all_links)

        nodes = [
            rand.randint(self._min_node_weight, self._max_node_weight)
            for _ in range(self._num_nodes)
        ]
        nodes_weight = sum(nodes)
        links_weight = round(
            nodes_weight * (1 - self._correlation)
            / self._correlation
        )
        links_aux = links_weight
        links = []
        while links_aux > 0:
            if links_aux < self._min_link_weight:
                links_aux += links.pop()              
                continue
            link = random.randint(self._min_link_weight, self._max_link_weight)
            if link > links_aux:
                link = links_aux
            links_aux -= link
            links.append(link)
        g = Graph()
        for weight in nodes:
            g.add_node(weight)
        for (src, tgt) in all_links:
            if len(links) > 0:
                g.connect(src+1, tgt+1, links.pop())
            else:
                break
        return g

if __name__ == '__main__':
    from argparse import ArgumentParser

    ap = ArgumentParser()
    ap.add_argument('--nodes', type=int, help='Number of nodes in task graph',
                    default=10)
    ap.add_argument('--min-node-weight', type=int, help='Min weight of node',
                    default=1)
    ap.add_argument('--max-node-weight', type=int, help='Max weight of node',
                    default=100)
    ap.add_argument('--min-link-weight', type=int, help='Min weight of link',
                    default=1)
    ap.add_argument('--max-link-weight', type=int, help='Max weight of link',
                    default=100)
    ap.add_argument('--correlation', type=float, help='Graph correlation',
                    default=0.5)
    ap.add_argument('--output', '-o', help='Write output to file')
    opts = ap.parse_args()
    g = (
        GraphBuilder()
        .set_num_nodes(opts.nodes)
        .set_node_weight(opts.min_node_weight, opts.max_node_weight)
        .set_link_weight(opts.min_link_weight, opts.max_link_weight)
        .set_correlation(opts.correlation)
        .build()
    )
    if (opts.output) is not None:
        with open(opts.output, 'w') as f:
            f.write(str(g))
    else:
        print(g)
