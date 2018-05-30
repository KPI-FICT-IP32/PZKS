from collections import defaultdict
from queue import Queue


FAKE_NODE_ID = None
PATH_END = 'critical_path_end'
PATH_END_NODE = 'critical_path_end_node'
PATH_START = 'critical_path_start'
PATH_START_NODE = 'critical_path_start_node'
CONN_IN = 'conn_in'
CONN_OUT = 'conn_out'
CONN = 'conn'
EARLY_START = 'early_start'
LATE_START = 'late_start'


class TaskGraph(object):
    def __init__(self, graph):
        # assert g.frozen
        self.g = graph
        self._nodes = defaultdict(dict)
        self._critical_graph = 0
        self._critical_graph_nodes = 0
        self._make_metrics()

    def _make_metrics(self):
        start_nodes = self.g.start_nodes
        end_nodes = self.g.end_nodes

        todo = Queue()

        for node in end_nodes:
            todo.put((FAKE_NODE_ID, node))
        while not todo.empty():
            (next_id, n) = todo.get()
            path_end = self._nodes[next_id].get(PATH_END, 0) + n.weight
            path_end_node = self._nodes[next_id].get(PATH_END_NODE, 0) + 1

            self._nodes[n.id][PATH_END] = max(
                self._nodes[n.id].get(PATH_END, 0),
                path_end,
            )
            self._nodes[n.id][PATH_END_NODE] = max(
                self._nodes[n.id].get(PATH_END_NODE, 0),
                path_end_node,
            )

            for prev in n.connections_in:
               todo.put((n.id, prev.source))

        for node in start_nodes:
            todo.put((FAKE_NODE_ID, node))
        while not todo.empty():
            (pid, n) = todo.get()
            if n.is_start_node:
                path_start = 0
            else:
                prev = self.g[pid]
                path_start = self._nodes[pid].get(PATH_START, 0) + prev.weight
            path_start_node = self._nodes[pid].get(PATH_START_NODE, 0) + 1

            self._nodes[n.id][PATH_START] = max(
                self._nodes[n.id].get(PATH_START, 0),
                path_start,
            )
            self._nodes[n.id][PATH_START_NODE] = max(
                self._nodes[n.id].get(PATH_START_NODE, 0),
                path_start_node,
            )

            for next_ in n.connections_out:
               todo.put((n.id, next_.target))
        del self._nodes[FAKE_NODE_ID]

        self._critical_graph = max(
            map(lambda n: n[PATH_END], self._nodes.values())
        )
        self._critical_graph_nodes = max(
            map(lambda n: n[PATH_END_NODE], self._nodes.values())
        )

        for nid in self._nodes:
            node = self.g[nid]
            self._nodes[nid][CONN_IN] = node.conns_in
            self._nodes[nid][CONN_OUT] = node.conns_out
            self._nodes[nid][CONN] = node.conns
            self._nodes[nid][EARLY_START] = self._nodes[nid][PATH_START] + 1
            self._nodes[nid][LATE_START] = (
                self._critical_graph - self._nodes[nid][PATH_END] + 1
            )
    
    @property
    def critical_path(self):
        return self._critical_graph

    @property
    def critical_path_node(self):
        return self._critical_graph_nodes

    def prioritize_nodes(self, alg):
        return sorted([
            (self.g[node_id], alg(*self[node_id]))
            for node_id in self._nodes
        ], key=lambda x: x[1])

    def __getitem__(self, key):
        return (self.g[key], self._nodes[key])

    def __str__(self):
        node_descs = []
        edge_descs = []

        for node_id in self._nodes:
            (node, metrics) = self[node_id]
            metrics_desc = '\\n'.join(f'{k}: {v}' for k, v in metrics.items())
            node_desc = (
                f'\tNode_{node.id} '
                f'[label="{node.id} ({node.weight})\\n{metrics_desc}"];'
            )
            node_descs.append(node_desc)
            for edge in node.connections_out:
                edge_descs.append(
                    f'\tNode_{edge.source.id} -> Node_{edge.target.id} '
                    f'[label="{edge.weight}"];'
                )
        return '\n'.join([
            'digraph GraphWithMetrics {',
            '\n'.join(node_descs),
            '\n'.join(edge_descs),
            '}'
        ])


def alg_diff_late_early(node, metrics):
    """Algorithm 2"""
    return metrics[LATE_START] - metrics[EARLY_START]


def alg_node_connectivity(node, metrics):
    """Algorithm 10"""
    return -metrics[CONN]


def alg_critical_path_start(node, metrics):
    """Algorithm 16"""
    return metrics[PATH_START]


if __name__ == '__main__':
    from graph import Graph
    g = Graph()
    g.add_node(3)
    g.add_node(2)
    g.add_node(6)
    g.add_node(1)
    g.add_node(8)
    g.connect(1, 4, 12)
    g.connect(2, 1, 2)
    g.connect(2, 3, 12)
    g.connect(2, 4, 5)
    g.connect(3, 4, 9)
    g.freeze()
    tg = TaskGraph(g)
    print(tg)
    # print(tg.prioritize_nodes(alg_diff_late_early))
    # print(tg.prioritize_nodes(alg_node_connectivity))
    # print(tg.prioritize_nodes(alg_critical_path_start))
    # g = Graph()
    # g.add_node(2)
    # g.add_node(3)
    # g.add_node(1)
    # g.add_node(3)
    # g.add_node(1)
    # g.add_node(1)
    # g.add_node(1)
    # g.add_node(4)
    # g.connect(1, 4, 1)
    # g.connect(2, 4, 1)
    # g.connect(2, 6, 1)
    # g.connect(3, 5, 1)
    # g.connect(4, 6, 1)
    # g.connect(6, 7, 1)
    # g.connect(6, 8, 1)
    # g.freeze()
    # tg = TaskGraph(g)
    # print(tg)
    # print(tg.prioritize_nodes(alg_diff_late_early))
    # print(tg.prioritize_nodes(alg_node_connectivity))
    # print(tg.prioritize_nodes(alg_critical_path_start))
