from controller import Supervisor


class SetWebotsColor:


    @staticmethod
    def set_node_color(node, color: list[float]):
        color = list(color)
        if not node:
            print(f"Node not found. Skipping...")
            return


        # Get the first child of the Pose node
        children_field = node.getField("children")
        shape_node = children_field.getMFNode(0)  # Get the first Shape node

        # Access the appearance field of the Shape node
        appearance_field = shape_node.getField("appearance")
        appearance_node = appearance_field.getSFNode()  # PBRAppearance node

        # Access and set the baseColor field
        color_field = appearance_node.getField("baseColor")

        if color_field.getTypeName() == "SFColor":
            color_field.setSFColor(color)

        else:
            print(f"Field 'baseColor' is not of type SFColor. Skipping node: {node.getDef()}")


    @staticmethod
    def set_webots_color(webots_names: list[str], supervisor: Supervisor, step_time_ms: int = 32, color: list[float] = (0.0,1.0,0.0)) -> None:
        time_step: int = 32  # Default Webots time step (in ms)
        steps_per_delay: int = step_time_ms // time_step  # Number of steps to match the desired delay
        for name in webots_names:
            target_node = supervisor.getFromDef(name)
            SetWebotsColor.set_node_color(node = target_node, color = color)
            for _ in range(steps_per_delay):
                supervisor.step(time_step)

