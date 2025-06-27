import Graph_loader
from Graph import Graph

if __name__ == "__main__":
    nodes, edges = Graph_loader.load_nodes_and_edges()

    graph = Graph(
        target_node="A",
        nodes=nodes,
        edges=edges
    )

    graph.adjust_graph_with_canvas()