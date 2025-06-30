from roboter_final.Graph import Graph_loader
from roboter_final.Graph.Graph import Graph

if __name__ == "__main__":
    nodes, edges = Graph_loader.load_nodes_and_edges()

    graph = Graph(target_node="A")

    graph.adjust_graph_with_canvas()
