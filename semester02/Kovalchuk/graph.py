from itertools import chain


class _Gen(object):
    def __init__(self):
        self.__value = 0

    def __call__(self):
        self.__value += 1
        return self.__value


class Node(object):
    def __init__(self, id_, weight):
        self._id = id_
        self._weight = weight
        self._incoming = {}
        self._outgoing = {}

    @property
    def id(self):
        return self._id

    @property
    def weight(self):
        return self._weight

    def connect(self, target, weight):
        if target.id in self._outgoing:
            raise ValueError(f'{self} is already connected to {target}')
        edge = Edge(self, target, weight)
        self._outgoing[target.id] = edge
        target._incoming[self.id] = edge

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
        self._weight = weight

    @property
    def id(self):
        return (self._source.id, self._target.id)

    @property
    def weight(self):
        return self._weight

    @property
    def source(self):
        return self._source

    @property
    def target(self):
        return self._target


class Graph(object):
    def __init__(self):
        self._gen = _Gen()
        self._nodes = {}
        self._frozen = False

    @classmethod
    def from_graph(cls, graph):
        g = cls()
        id_map = {}
        for node in graph:
            id_map[node.id] = g.add_node(node.weight)
        for node in graph:
            for edge in node.connections_out:
                g.connect(id_map[edge.source.id], id_map[edge.target.id],
                          edge.weight)
        return g

    def add_node(self, weight):
        if self._frozen:
            raise ValueError('Cannot add node to the frozen graph')
        node = Node(self._gen(), weight=weight)
        self._nodes[node.id] = node
        return node.id

    def del_node(self, node):
        if self._frozen:
            raise ValueError('Cannot del node from the frozen graph')
        if isinstance(node, int):
            node = self._nodes[node]
        for other in node.connections:
            node.disconnect(other)
        del self._nodes[node.id]

    def connect(self, source, target, weight):
        if self._frozen:
            raise ValueError('Cannot make conns in the frozen graph')
        if isinstance(source, int):
            source = self._nodes[source]
        if isinstance(target, int):
            target = self._nodes[target]
        source.connect(target, weight)

    def disconnect(self, source, target):
        if self._frozen:
            raise ValueError('Cannot del conns in the frozen graph')
        if isinstance(source, int):
            source = self._nodes[source]
        if isinstance(target, int):
            target = self._nodes[target]
        source.disconnect(target)

    def freeze(self):
        self._frozen = True
        self._reindex()
        self._start_nodes = tuple(n for n in self._nodes.values()
                                  if n.is_start_node)
        self._end_nodes = tuple(n for n in self._nodes.values()
                                if n.is_end_node)

    def _reindex(self):
        gen = _Gen()
        mapping = {node.id: gen() for node in self._nodes.values()}
        for node in self._nodes.values():
            node._id = mapping[node.id]
            node._outgoing = {
                mapping[id_]: node._outgoing[id_]
                for id_ in node._outgoing.keys()
            }
            node._incoming = {
                mapping[id_]: node._incoming[id_]
                for id_ in node._incoming.keys()
            }
        self._nodes = {node.id: node for node in self._nodes.values()}

    @property
    def start_nodes(self):
        if self._frozen:
            return self._start_nodes
        else:
            return tuple(n for n in self._nodes.values() if n.is_start_node)

    @property
    def end_nodes(self):
        if self._frozen:
            return self._end_nodes
        else:
            return tuple(n for n in self._nodes.values() if n.is_end_node)

    @property
    def frozen(self):
        return self._frozen

    def __getitem__(self, item_id):
        return self._nodes[item_id]

    def __iter__(self):
        return iter(self._nodes.values())

    def __len__(self):
        return len(self._nodes)

    def __str__(self):
        node_descs = []
        edge_descs = []

        for node in self._nodes.values():
            node_descs.append(
                f'\tNode_{node.id} [label="{node.id} ({node.weight})"];'
            )
            for edge in node.connections_out:
                edge_descs.append(
                    f'\tNode_{edge.source.id} -> Node_{edge.target.id} '
                    f'[label="{edge.weight}"];'
                )
        return '\n'.join([
            'digraph TaskGraph {',
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
    g.connect(1, 4, 1)
    g.connect(2, 4, 1)
    g.connect(2, 6, 1)
    g.connect(3, 5, 1)
    g.connect(4, 6, 1)
    g.connect(6, 7, 1)
    g.connect(6, 8, 1)
    print(g)
