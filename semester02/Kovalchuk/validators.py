class CycleDetectedException(Exception):
    pass


def validate_acyclic(graph):
    start_nodes = list(graph.start_nodes)
    if len(start_nodes) == 0:
        start_nodes.append(next(iter(graph)))

    for node in start_nodes:
        cycle = find_cycle(graph, node)
        if cycle:
            raise CycleDetectedException(f'Cycle detected: {cycle}')


def find_cycle(graph, start, visited=None):
    if visited is None:
        visited = []

    if start.id in visited:
        cycle = visited[visited.index(start.id):]
        return cycle
    visited.append(start.id)
    for edge in start.connections_out:
        cycle = find_cycle(graph, edge.target, visited)
        if cycle:
            return cycle
    visited.pop()
    return None


if __name__ == '__main__':
    from graph import Graph
    g = Graph()
    g.add_node(1)
    g.add_node(2)
    g.add_node(3)
    g.add_node(4)
    g.add_node(5)
    g.add_node(6)
    g.connect(1, 2, 1)
    g.connect(2, 3, 1)
    g.connect(3, 4, 1)
    g.connect(4, 5, 1)
    g.connect(5, 6, 1)
    g.connect(6, 1, 1)
    validate_acyclic(g)
