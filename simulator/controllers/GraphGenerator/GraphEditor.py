import tkinter as tk
import json
import math

import JsonToWbt

canvas_size = 800
relation_height_length = 330 / 280

half_canvas = canvas_size / 2
quarter_canvas = canvas_size / 4
three_quarters_canvas = canvas_size * 3 / 4
height_diff = (quarter_canvas - three_quarters_canvas) / 4

node_middle_y = half_canvas
node_middle_x = half_canvas
node_bottom_y = three_quarters_canvas
node_top_y = quarter_canvas
node_left_x = node_middle_x - quarter_canvas / relation_height_length
node_right_x = node_middle_x + quarter_canvas / relation_height_length
node_side_bottom_y = three_quarters_canvas + height_diff
node_side_top_y = quarter_canvas - height_diff
node_between_x = node_left_x + (node_right_x - node_left_x) / 4


nodes = {
    'A': (node_middle_x, node_bottom_y),
    'B': (node_left_x, node_side_bottom_y),
    'C': (node_right_x, node_side_bottom_y),
    'D': (node_middle_x, node_middle_y),
    'E': (node_between_x, node_side_top_y),
    'F': (node_left_x, node_side_top_y),
    'G': (node_right_x, node_side_top_y),
    'H': (node_middle_x, node_top_y)
}

edges = [
    ('A', 'B'),
    ('A', 'C'),
    ('A', 'D'),
    ('B', 'D'),
    ('B', 'F'),
    ('B', 'E'),
    ('C', 'D'),
    ('C', 'G'),
    ('D', 'E'),
    ('D', 'G'),
    ('E', 'F'),
    ('E', 'G'),
    ('E', 'H'),
    ('F', 'H'),
    ('H', 'G')
]


max_graph_size = canvas_size / 1.25
min_length = max_graph_size / 9
max_length = min_length * 4
min_orientation_diff = 5
pixel_meter_relation = 4.5 / max_graph_size


class GraphEditor:
    def __init__(self, root):

        self.root = root
        self.root.title("Graph Editor")
        self.canvas = tk.Canvas(root, width=canvas_size, height=canvas_size, bg="white")
        self.canvas.pack()

        self.node_radius = 10
        self.node_shapes = {}
        self.edge_shapes = {}
        self.edge_obstacles = {}
        self.selected_edge = None
        self.hovered_edge = None
        self.selected_node = None
        self.non_traversable_edges = set()
        self.blocked_nodes = set()
        self.target_node = 'H'
        self.draw_graph()

        # Event bindings
        self.canvas.bind("<Motion>", self.on_hover)
        self.canvas.bind("<ButtonPress-1>", self.on_node_press)
        self.canvas.bind("<B1-Motion>", self.on_node_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_node_release)
        self.canvas.bind("<ButtonPress-3>", self.toggle_traversable)
        self.root.bind("<b>", self.toggle_blocked_node)
        self.root.bind("<s>", self.export_to_json)
        self.root.bind("<r>", self.check_rules)
        self.root.bind("<t>", self.set_target_node)
        self.root.bind("<o>", self.toggle_obstacle)

    def scale_numbers(self, input_dict):
        scaled_dict = {
            key: tuple(value * pixel_meter_relation for value in values)
            for key, values in input_dict.items()
        }
        return scaled_dict

    def draw_graph(self):

        for edge in edges:
            node1, node2 = edge
            x1, y1 = nodes[node1]
            x2, y2 = nodes[node2]
            line = self.canvas.create_line(x1, y1, x2, y2, fill="black", width=2)
            self.edge_shapes[edge] = line
            self.edge_obstacles[edge] = None

        for node, (x, y) in nodes.items():
            self.draw_node(node)

    def draw_node(self, node_name):
        x, y = nodes[node_name]
        if node_name == 'A':
            color = 'green'
        elif node_name == self.target_node:
            color = "blue"
        elif node_name in self.blocked_nodes:
            color = "red"
        else:
            color = "black"
        oval = self.canvas.create_oval(
            x - self.node_radius, y - self.node_radius,
            x + self.node_radius, y + self.node_radius,
            fill=color, outline=color
        )
        self.node_shapes[node_name] = oval

    def update_edges(self):
        for edge in edges:
            node1, node2 = edge
            x1, y1 = nodes[node1]
            x2, y2 = nodes[node2]
            line_style = "dashed" if edge in self.non_traversable_edges else "solid"
            self.canvas.itemconfig(self.edge_shapes[edge], dash=(4, 4) if line_style == "dashed" else ())
            self.canvas.coords(self.edge_shapes[edge], x1, y1, x2, y2)

    def on_node_press(self, event):
        for node, oval in self.node_shapes.items():
            x, y = nodes[node]
            if (x - self.node_radius < event.x < x + self.node_radius and
                    y - self.node_radius < event.y < y + self.node_radius):
                self.selected_node = node
                break

    def on_node_drag(self, event):
        if self.selected_node:
            nodes[self.selected_node] = (event.x, event.y)
            self.canvas.coords(self.node_shapes[self.selected_node],
                               event.x - self.node_radius, event.y - self.node_radius,
                               event.x + self.node_radius, event.y + self.node_radius)
            self.update_edges()

    def on_node_release(self, event):
        self.selected_node = None
        self.check_rules()

    def toggle_blocked_node(self, event):
        for node, oval in self.node_shapes.items():
            x, y = nodes[node]
            if (x - self.node_radius < event.x < x + self.node_radius and
                    y - self.node_radius < event.y < y + self.node_radius):
                if node in self.blocked_nodes:
                    self.blocked_nodes.remove(node)
                else:
                    self.blocked_nodes.add(node)
                self.redraw_node(node)

    def redraw_node(self, node_name):
        self.canvas.delete(self.node_shapes[node_name])
        self.draw_node(node_name)

    def set_target_node(self, event):
        for node, oval in self.node_shapes.items():
            x, y = nodes[node]
            if (x - self.node_radius < event.x < x + self.node_radius and
                    y - self.node_radius < event.y < y + self.node_radius):
                if node in {'F', 'G', 'H'}:  # Only allow F, G, or H to be target nodes
                    self.target_node = node
                    self.redraw_graph()
                else:
                    print(f"Node {node} cannot be a target node.")
                break

    def redraw_graph(self):

        self.canvas.delete("all")
        self.node_shapes.clear()
        self.edge_shapes.clear()
        self.edge_obstacles.clear()
        self.draw_graph()

    def on_hover(self, event):
        closest_edge = None

        for edge, line in self.edge_shapes.items():
            x1, y1 = nodes[edge[0]]
            x2, y2 = nodes[edge[1]]


            if self.is_point_near_line(event.x, event.y, x1, y1, x2, y2):
                closest_edge = edge
                break


        if closest_edge != self.hovered_edge:
            if self.hovered_edge is not None:

                self.canvas.itemconfig(self.edge_shapes[self.hovered_edge], fill="black")
            self.hovered_edge = closest_edge
            if self.hovered_edge is not None:

                self.canvas.itemconfig(self.edge_shapes[self.hovered_edge], fill="blue")

    def is_point_near_line(self, px, py, x1, y1, x2, y2, threshold=10):

        if x1 == x2 and y1 == y2:
            return abs(px - x1) <= threshold and abs(py - y1) <= threshold

        distance = abs((y2 - y1) * px - (x2 - x1) * py + x2 * y1 - y2 * x1) / ((y2 - y1) ** 2 + (x2 - x1) ** 2) ** 0.5

        within_bounds = min(x1, x2) - threshold <= px <= max(x1, x2) + threshold and \
                        min(y1, y2) - threshold <= py <= max(y1, y2) + threshold
        return distance <= threshold and within_bounds

    def toggle_obstacle(self, event):

        if self.hovered_edge:
            edge = self.hovered_edge
            if self.edge_obstacles[edge] is None:

                x1, y1 = nodes[edge[0]]
                x2, y2 = nodes[edge[1]]
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2

                obstacle_radius = 5
                obstacle = self.canvas.create_oval(
                    mid_x - obstacle_radius, mid_y - obstacle_radius,
                    mid_x + obstacle_radius, mid_y + obstacle_radius,
                    fill="orange", outline="orange"
                )
                self.edge_obstacles[edge] = obstacle
                print(f"Obstacle added to edge {edge}")
            else:

                self.canvas.delete(self.edge_obstacles[edge])
                self.edge_obstacles[edge] = None
                print(f"Obstacle removed from edge {edge}")



    def toggle_traversable(self, event):

        for edge, line in self.edge_shapes.items():
            x1, y1, x2, y2 = self.canvas.coords(line)
            if min(x1, x2) <= event.x <= max(x1, x2) and min(y1, y2) <= event.y <= max(y1, y2):
                if edge in self.non_traversable_edges:
                    self.non_traversable_edges.remove(edge)
                else:
                    self.non_traversable_edges.add(edge)
                self.update_edges()
                self.check_rules()
                break

    def calculate_edge_length(self, node1, node2):
        x1, y1 = nodes[node1]
        x2, y2 = nodes[node2]
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def check_rules(self, event=None):
        for edge, line in self.edge_shapes.items():
            node1, node2 = edge
            if node1 in self.blocked_nodes or node2 in self.blocked_nodes:
                self.canvas.itemconfig(line, fill="gray")
                continue

            length = self.calculate_edge_length(node1, node2)
            if length < min_length or length > max_length:
                self.canvas.itemconfig(line, fill="red")
            else:
                self.canvas.itemconfig(line, fill="black")
    def mirror_nodes(self, node):
        mirror_nodes = {
        key: (x, canvas_size - y)
        for key, (x, y) in nodes.items()
        }
        return mirror_nodes

    def export_to_json(self, event=None):
        graph_data = {
            "nodes": self.scale_numbers(self.mirror_nodes(nodes)),
            "edges": [
                {
                    "node1": edge[0],
                    "node2": edge[1],
                    "length": self.calculate_edge_length(*edge),
                    "obstacle": self.edge_obstacles[edge] is not None
                }
                for edge in edges
            ],
            "non_traversable_edges": list(self.non_traversable_edges),
            "blocked_nodes": list(self.blocked_nodes),
            "target_node": self.target_node
        }
        with open("graph.json", "w") as file:
            json.dump(graph_data, file, indent=4)
        JsonToWbt.generate_wbt("graph.json", "graph_world.wbt")
        print("Graph exported successfully.")


if __name__ == "__main__":
    root = tk.Tk()
    editor = GraphEditor(root)
    root.mainloop()
