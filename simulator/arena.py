from dataclasses import dataclass


@dataclass(frozen=True)
class RobotState:
    x: float
    y: float
    theta: float


class Arena:
    """
    Rectangular 2D environment.

    The Arena owns the rules of the physical world and knows
    which robots currently exist in it.

    A robot proposes a next state. The Arena evaluates whether
    that proposed state is physically valid in the context of
    the whole system.
    """

    def __init__(self, width: float, height: float):
        if width <= 0:
            raise ValueError(
                "Arena width must be greater than zero."
            )

        if height <= 0:
            raise ValueError(
                "Arena height must be greater than zero."
            )

        self.width = width
        self.height = height

        # robot_id -> Robot
        self.robots = {}

    def add_robot(self, robot):
        """
        Register a robot as a physical entity in the Arena.
        """

        if robot.robot_id in self.robots:
            raise ValueError(
                f"Robot '{robot.robot_id}' already exists in the arena."
            )

        # Initial robot placement must also be collision-free.
        if self.overlaps_robot(
            robot_id=robot.robot_id,
            proposed_state=robot.state,
            radius=robot.radius,
        ):
            raise ValueError(
                f"Robot '{robot.robot_id}' overlaps another robot "
                f"at its initial position."
            )

        self.robots[robot.robot_id] = robot

    def remove_robot(self, robot_id: str):
        """
        Remove a robot from the Arena.
        """

        self.robots.pop(robot_id, None)

    def get_robot(self, robot_id: str):
        """
        Return one robot by ID.
        """

        return self.robots.get(robot_id)

    def get_robots(self):
        """
        Return all robots currently registered in the Arena.
        """

        return list(self.robots.values())

    def contains(
        self,
        state: RobotState,
        radius: float = 0.0,
    ) -> bool:
        """
        Returns True if the complete circular footprint of the robot
        lies within the Arena.
        """

        return (
            radius <= state.x <= self.width - radius
            and radius <= state.y <= self.height - radius
        )

    def overlaps_robot(
        self,
        robot_id: str,
        proposed_state: RobotState,
        radius: float,
    ) -> bool:
        """
        Returns True if the proposed circular footprint overlaps
        any other registered robot.

        Two circular robots overlap when:

            distance_between_centers < radius_a + radius_b
        """

        for other_robot in self.robots.values():

            # A robot should not collide with itself.
            if other_robot.robot_id == robot_id:
                continue

            dx = (
                proposed_state.x
                - other_robot.state.x
            )

            dy = (
                proposed_state.y
                - other_robot.state.y
            )

            distance_squared = (
                dx * dx
                + dy * dy
            )

            minimum_distance = (
                radius
                + other_robot.radius
            )

            minimum_distance_squared = (
                minimum_distance
                * minimum_distance
            )

            if (
                distance_squared
                < minimum_distance_squared
            ):
                return True

        return False

    def resolve_transition(
        self,
        robot_id: str,
        current_state: RobotState,
        proposed_state: RobotState,
        radius: float,
    ) -> RobotState:
        """
        Evaluate a robot's proposed state transition.

        Current world rules:

        1. A robot's entire circular footprint must remain
           inside the Arena.

        2. A robot's physical footprint may not overlap
           another registered robot.

        3. If translation would create an invalid world state,
           the translation is rejected.

        4. Rotation is still allowed, because a circular robot
           does not change its physical footprint when rotating.
        """

        inside_arena = self.contains(
            proposed_state,
            radius,
        )

        collision_free = not self.overlaps_robot(
            robot_id=robot_id,
            proposed_state=proposed_state,
            radius=radius,
        )

        if (
            inside_arena
            and collision_free
        ):
            return proposed_state

        # Reject translation but allow the proposed rotation.
        return RobotState(
            x=current_state.x,
            y=current_state.y,
            theta=proposed_state.theta,
        )