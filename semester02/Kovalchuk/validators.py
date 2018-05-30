from queue import Queue


class ValidationError(Exception):
    pass


class CycleDetectedException(ValidationError):
    pass


class NotConnectedException(ValidationError):
    pass


class EmptyException(ValidationError):
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


def validate_connected(graph):
    visited = set()
    todo = Queue()
    todo.put(next(iter(graph)))
    while not todo.empty():
        node = todo.get()
        visited.add(node.id)
        for edge in node.connections_out:
            if edge.target.id not in visited:
                todo.put(edge.target)
    all_nodes = set(node.id for node in graph)
    if all_nodes != visited:
        not_connected_nodes = all_nodes - visited
        raise NotConnectedException(f'Not connected: {not_connected_nodes}')


def validate_not_empty(graph):
    if len(graph) <= 0:
        raise EmptyException(f'Graph is empty!')


if __name__ == '__main__':
    from graph import Graph
    # g = Graph()
    # g.add_node(1)
    # g.add_node(2)
    # g.add_node(3)
    # g.add_node(4)
    # g.add_node(5)
    # g.add_node(6)
    # g.connect(1, 2, 1)
    # g.connect(2, 3, 1)
    # g.connect(3, 4, 1)
    # g.connect(4, 5, 1)
    # g.connect(5, 6, 1)
    # g.connect(6, 1, 1)
    # validate_acyclic(g)
    # validate_connected(g)
