from itertools import chain

import graph as gr


class Node(gr.Node):
    def __init__(self, id_, weight):
        self._id = id_
        self._weight = weight
        self._incoming = {}
        self._outgoing = {}

    def connect(self, target, weight):
        if target.id in self._outgoing:
            raise ValueError(f'{self} is already connected to {target}')
        edge = Edge(self, target, weight)
        backwards = Edge(target, self, weight)
        self._outgoing[target.id] = edge
        self._incoming[target.id] = backwards
        target._incoming[self.id] = edge
        target._outgoing[self.id] = backwards

    def disconnect(self, target):
        if target.id in self._incoming:
            del self._incoming[target.id]
            del target._outgoing[self.id]
        if target.id in self._outgoing:
            del self._outgoing[target.id]
            del target._incoming[self.id]

    @property
    def is_start_node(self):
        return len(self._incoming) == 0

    @property
    def is_end_node(self):
        return len(self._outgoing) == 0

    @property
    def conns(self):
        return self.conns_in + self.conns_out

    @property
    def conns_in(self):
        return len(self._incoming)

    @property
    def conns_out(self):
        return len(self._outgoing)

    @property
    def connections(self):
        return chain(self._incoming.values(), self._outgoing.values())

    @property
    def connections_in(self):
        return iter(self._incoming.values())

    @property
    def connections_out(self):
        return iter(self._outgoing.values())

    def __str__(self):
        return f'Node_{self._id}({self._weight})'

    def __repr__(self):
        return str(self)


class Edge(object):
    def __init__(self, source, target, weight):
        self._source = source
        self._target = target
        self._weight = None

    @property
    def id(self):
        return tuple(sorted((self._source.id, self._target.id)))

    @property
    def weight(self):
        return self._weight

    @property
    def source(self):
        return self._source

    @property
    def target(self):
        return self._target


class Graph(gr.Graph):
    def connect(self, source, target, weight=None):
        return super().connect(source, target, weight)

    def add_node(self, weight):
        if self._frozen:
            raise ValueError('Cannot add node to the frozen graph')
        node = Node(self._gen(), weight=weight)
        self._nodes[node.id] = node
        return node.id

    def __str__(self):
        node_descs = []
        edge_descs = []
        described_edges = set()

        for node in self._nodes.values():
            node_descs.append(
                f'\tNode_{node.id} [label="{node.id} ({node.weight})"];'
            )
            for edge in node.connections_out:
                if edge.id not in described_edges:
                    edge_descs.append(
                        f'\tNode_{edge.source.id} -- Node_{edge.target.id};'
                    )
                described_edges.add(edge.id)
        return '\n'.join([
            'graph SystemGraph {',
            '\n'.join(node_descs),
            '\n'.join(edge_descs),
            '}'
        ])


if __name__ == '__main__':
    g = Graph()
    g.add_node(2)
    g.add_node(3)
    g.add_node(1)
    g.add_node(3)
    g.add_node(1)
    g.add_node(1)
    g.add_node(1)
    g.add_node(4)
    g.connect(1, 4)
    g.connect(2, 4)
    g.connect(2, 6)
    g.connect(3, 5)
    g.connect(4, 6)
    g.connect(6, 7)
    g.disconnect(1, 4)
    g.connect(6, 8)
    print(g)
