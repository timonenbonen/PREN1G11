from controller import Supervisor

from Graph import Graph
from Box import Box
from Cylinder import Cylinder
import math

class Roboter(Supervisor):
    def __init__(self, supervisor, graph: Graph, max_velocity_in_ms: float, acceleration_in_ms2: float,
                                breaking_speed_in_ms2: float, align_time_in_s:float):
        self.graph: Graph = graph
        self.align_time_in_s:float = align_time_in_s
        self.max_velocity_in_ms:float = max_velocity_in_ms
        self.acceleration_in_ms2:float = acceleration_in_ms2
        self.breaking_speed_in_ms2:float = breaking_speed_in_ms2
        self.timestep = int(supervisor.getBasicTimeStep())


    def navigate_over_edge(self, supervisor, edge_name: str):
        edge: Box = self.graph.edges[edge_name]

        length, angle = edge.get_length_and_angle()
        robot = supervisor.getFromDef("MyRobot")
        position_field = robot.getField("translation")
        old_position:list[float] = position_field.getSFVec3f()
        is_on_node2: bool = old_position[0] == edge.node2.position[0] and old_position[1] == edge.node2.position[1]
        if is_on_node2:
            self.align_to_edge(supervisor, angle+math.pi)
        else:
            self.align_to_edge(supervisor, angle)

        if edge.has_obstacle:
            self.handle_obstacle(supervisor, edge_name, edge)
            #Turn
        if is_on_node2:
            self.move_to_point(supervisor, edge.node1.position)
        else:

            self.move_to_point(supervisor, edge.node2.position)



    def align_to_edge(self,supervisor, angle: float):
        robot = supervisor.getFromDef("MyRobot")
        orientation_field = robot.getField("rotation")
        old_orientation = orientation_field.getSFVec3f()
        new_orientation: list[float] = [0.0,0,1,angle]
        # Calculate the rotation difference
        angle_difference = new_orientation[3] - old_orientation[3]
        if angle_difference > math.pi:
            angle_difference -= 2 * math.pi
        elif angle_difference < -math.pi:
            angle_difference += 2 * math.pi

        total_steps = int(self.align_time_in_s * 1000 / self.timestep)
        angle_step = angle_difference / total_steps
        for step in range(total_steps):
            # Update the orientation incrementally
            new_angle = old_orientation[3] + angle_step * step
            orientation_field.setSFRotation([0, 0, 1, new_angle])

            # Step the simulation
            supervisor.step(self.timestep)

        # Set the final orientation to ensure precision
        orientation_field.setSFRotation(new_orientation)


    def move_to_point(self, supervisor, position: tuple[float, float, float]):


        """Gradually move to a target position."""
        # Get the translation field
        robot = supervisor.getFromDef("MyRobot")
        position_field = robot.getField("translation")
        old_position = position_field.getSFVec3f()
        target_position = list(position)
        # Calculate the distance
        distance = ((target_position[0] - old_position[0])**2 +
                    (target_position[1] - old_position[1])**2 +
                    (target_position[2] - old_position[2])**2)**0.5
        # Movement phases
        acceleration_time = self.max_velocity_in_ms / self.acceleration_in_ms2
        deceleration_time = self.max_velocity_in_ms / self.breaking_speed_in_ms2
        acceleration_distance = 0.5 * self.acceleration_in_ms2 * (acceleration_time**2)
        deceleration_distance = 0.5 * self.breaking_speed_in_ms2 * (deceleration_time**2)
        # Adjust for short distances
        if distance < acceleration_distance + deceleration_distance:
            max_velocity = (self.acceleration_in_ms2 * distance /
                            (1 + self.acceleration_in_ms2 / self.breaking_speed_in_ms2))**0.5
            acceleration_time = max_velocity / self.acceleration_in_ms2
            deceleration_time = max_velocity / self.breaking_speed_in_ms2
            acceleration_distance = 0.5 * self.acceleration_in_ms2 * (acceleration_time**2)
            deceleration_distance = 0.5 * self.breaking_speed_in_ms2 * (deceleration_time**2)

            # Start moving
        velocity = 0.0
        covered_distance = 0.0
        epsilon = 0.01  # Tolerance for stopping

        while covered_distance + epsilon < distance:


            if covered_distance < acceleration_distance:
                # Accelerate
                velocity += self.acceleration_in_ms2 * (self.timestep / 1000.0)
                velocity = min(velocity, self.max_velocity_in_ms)
            elif distance - covered_distance <= deceleration_distance:
                # Decelerate
                velocity -= self.breaking_speed_in_ms2 * (self.timestep / 1000.0)
                velocity = max(velocity, 0.01)  # Ensure a small velocity to avoid stalling

            # Move a step
            step_distance = velocity * (self.timestep / 1000.0)
            covered_distance += step_distance
            ratio = min(covered_distance / distance, 1.0)

            current_position = [
                old_position[i] + ratio * (target_position[i] - old_position[i])
                for i in range(3)
            ]

            position_field.setSFVec3f(current_position)

            # Step the simulation
            if supervisor.step(self.timestep) == -1:
                print("Simulation stopped unexpectedly")
                break

        # Ensure exact final position
        position_field.setSFVec3f(target_position)

    def handle_obstacle(self, supervisor, edge_name: str, edge: Box):
        obstacle_name = f"{edge_name}_obstacle"
        obstacle = supervisor.getFromDef(obstacle_name)

        if not obstacle:
            print(f"Obstacle {obstacle_name} not found in Webots!")
            return
        transparency_field = obstacle.getField("children").getMFNode(0).getField("appearance").getSFNode().getField("transparency")
        # Get obstacle translation field
        obstacle_position_field = obstacle.getField("translation")
        robot = supervisor.getFromDef("MyRobot")
        robot_position_field = robot.getField("translation")
        robot_position = robot_position_field.getSFVec3f()
        # Move in front of the obstacle
        obstacle_position = obstacle_position_field.getSFVec3f()
        approach_position = [
            robot_position[0]+0.8*(obstacle_position[0]-robot_position[0]),  # Adjust this offset as needed
            robot_position[1]+0.8*(obstacle_position[1]-robot_position[1]),
            obstacle_position[2]
        ]
        turn_position = [
            robot_position[0] + 1.2 * (obstacle_position[0] - robot_position[0]),  # Adjust this offset as needed
            robot_position[1] + 1.2 * (obstacle_position[1] - robot_position[1]),
            obstacle_position[2]
        ]

        self.move_to_point(supervisor, tuple(approach_position))

        # Lift the obstacle (move it upwards)
        self.change_robot_appearance(robot, "../../chassis_with_obstacle.obj")

        transparency_field.setSFFloat(1.0)
        print(obstacle_position_field.getSFFloat())

        # Carry the obstacle by moving with the robot

        self.move_to_point(supervisor, tuple(turn_position))  # Move to node1 for simplicity

        # Rotate the robot 180 degrees
        current_rotation = robot.getField("rotation").getSFRotation()
        self.align_to_edge(supervisor,current_rotation[3] + math.pi)
        supervisor.step(self.timestep)

        # Place the obstacle
        self.change_robot_appearance(robot, "../../chassis_without_obstacle.obj")
        transparency_field.setSFFloat(0.0)

        # Rotate back to the original direction
        self.align_to_edge(supervisor,current_rotation[3])
        supervisor.step(self.timestep)

    @staticmethod
    def change_robot_appearance(robot, obj_path: str):
        # Access the 'children' field of the robot
        children_field = robot.getField("children")

        # Get the first child node (assuming it's the Solid node)
        solid_node = children_field.getMFNode(0)

        # Access the 'children' field of the Solid node
        solid_children_field = solid_node.getField("children")

        # Get the CadShape node (assuming it's the first child of Solid)
        shape_node = solid_children_field.getMFNode(0)

        # Access the geometry node of the Shape
        shape_node.getField("url").setMFString(0, obj_path)




    @staticmethod
    def is_node(name:str):
        return "_" not in name
    @staticmethod
    def is_edge(name:str):
        return "_" in name

    def traverse_graph(self, supervisor, path:list[str]):


        edges_in_path = list(filter(self.is_edge, path))
        for edge_name in edges_in_path:
            self.navigate_over_edge(supervisor, edge_name)


