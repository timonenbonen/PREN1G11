from typing import Dict, List
from Cylinder import Cylinder
from Box import Box
from Shape import Shape
import heapq


class Graph:
    def __init__(self, starting_node: Cylinder, target_node: Cylinder, nodes: Dict[str, Cylinder] = None,
                 edges: Dict[str, Box] = None):
        self.nodes: Dict[str, Cylinder] = nodes  # {node_id: (x, y)}
        self.edges: Dict[str, Box] = edges
        self.target_node: Cylinder = target_node  # Target node IDs
        self.target_node.set_base_color((0, 0, 1))
        self.starting_node: Cylinder = starting_node

    def change_target(self, new_target_node) -> None:
        self.target_node.set_base_color((1, 1, 1))
        self.target_node = new_target_node
        self.target_node.set_base_color((0, 0, 1))

    def get_edges(self) -> Dict[str, Box]:
        return self.edges

    def mirror_y_axis(self, coordination_system_size: float) -> None:
        for cylinder in self.nodes.values():
            cylinder.mirror_y_axis(coordination_system_size)

    def scale_graph(self, scaling_factor: float) -> None:
        for cylinder in self.nodes.values():
            old_coordinates: tuple[float, float] = cylinder.get_x_y()
            cylinder.set_x_y(old_coordinates[0] * scaling_factor, old_coordinates[1] * scaling_factor)

    def calculate_size(self) -> tuple[float, float]:
        """
        Calculate the size of the graph in terms of width and height.

        :return: A tuple (width, height) representing the graph's dimensions.
        """
        if not self.nodes:
            return 0.0, 0.0

        # Get all x and y coordinates from the nodes
        x_coords = [node.get_x_y()[0] for node in self.nodes.values()]
        y_coords = [node.get_x_y()[1] for node in self.nodes.values()]

        # Calculate width and height
        width = max(x_coords) - min(x_coords)
        height = max(y_coords) - min(y_coords)

        return width, height

    def calculate_shortest_path(self, max_velocity_in_ms: float, acceleration_in_ms2: float,
                                breaking_speed_in_ms2: float, align_time_in_s:float) -> tuple[list, list]:
        """
        Calculates the shortest path between starting_node and target_node using Dijkstra's algorithm.

        :return: A list alternating between node IDs and edge IDs in the shortest path order.
        """
        # Create adjacency list, skipping blocked nodes
        adjacency_list: dict[str, list] = {node: [] for node in self.nodes if not self.nodes[node].is_blocked}
        for edge_id, edge in self.edges.items():
            if not edge.is_removed:  # Ignore removed edges
                node1: str = edge.node1.get_name()
                node2: str = edge.node2.get_name()
                if not edge.node1.is_blocked and not edge.node2.is_blocked:  # Skip edges connected to blocked nodes
                    time_to_traverse = edge.calculate_traversal_time_edge(max_speed=max_velocity_in_ms,
                                                                          acceleration=acceleration_in_ms2,
                                                                          braking_speed=breaking_speed_in_ms2,
                                                                          align_time=align_time_in_s)  # Get length of the edge
                    adjacency_list[node1].append((node2, time_to_traverse))
                    adjacency_list[node2].append((node1, time_to_traverse))

        # Dijkstra's algorithm setup
        priority_queue = [(0, self.starting_node.get_name(), [])]  # (distance, current_node, path_so_far)
        visited = set()
        algorithm_sequence = []

        while priority_queue:
            current_distance, current_node, path = heapq.heappop(priority_queue)

            if current_node in visited:
                continue

            visited.add(current_node)
            edge_name: str = ""
            # Add the current node to the path
            if path:
                # Add the edge name between the last node in the path and the current node
                last_node = path[-1]
                edge_name = f"{last_node}_{current_node}"
                if edge_name not in self.edges:
                    edge_name = f"{current_node}_{last_node}"  # Check reversed edge
                algorithm_sequence.append(edge_name)
            algorithm_sequence.append(current_node)

            path = path + [edge_name] + [current_node] if path else [current_node]

            # If target node is reached, return the path with edges
            if current_node == self.target_node.get_name():
                return algorithm_sequence, path

            # Explore neighbors
            for neighbor, weight in adjacency_list.get(current_node, []):
                if neighbor not in visited:
                    heapq.heappush(priority_queue, (current_distance + weight, neighbor, path))

        # If no path is found, return an empty list
        return [], []

    def to_vrml(self) -> list[str]:
        vrml: list[str] = []
        for node in self.nodes.values():
            vrml.append(node.blocked_to_vrml())
            vrml.append(node.to_vrml())

        for edge in self.edges.values():
            vrml.append(edge.to_vrml())
            vrml.append(edge.obstacle_to_vrml())

        return vrml
