import math

from simulator.arena import Arena, RobotState


class Robot:
    """
    Simple circular 2D robot.

    The Robot owns its current state and receives commands.

    It computes an intended next state, submits that proposed
    state to the Arena, and adopts whatever state the Arena
    determines is physically valid.
    """

    def __init__(
        self,
        robot_id,
        arena: Arena,
        x,
        y,
        theta=0.0,
        linear_step=1.0,
        angular_step=math.radians(10),
        radius=2.0,
        lidar=None,
    ):
        self.robot_id = robot_id
        self.arena = arena

        self.linear_step = linear_step
        self.angular_step = angular_step

        self.radius = radius
        self.lidar = lidar

        initial_state = RobotState(
            x=x,
            y=y,
            theta=theta,
        )

        if not self.arena.contains(
            initial_state,
            self.radius,
        ):
            raise ValueError(
                f"Initial robot position ({x}, {y}) "
                f"is invalid for radius {radius}."
            )

        self.state = initial_state

        # Register the robot in the physical world.
        self.arena.add_robot(self)

    def scan(self):
        if self.lidar is None:
            return []

        return self.lidar.scan(
            arena=self.arena,
            robot=self,
        )

    def move_forward(
        self,
        speed_scale: float = 1.0,
    ) -> RobotState:
        """
        Move forward relative to the robot's current heading.
        """

        step = (
            self.linear_step
            * speed_scale
        )

        proposed_state = RobotState(
            x=(
                self.state.x
                + step
                * math.cos(self.state.theta)
            ),
            y=(
                self.state.y
                + step
                * math.sin(self.state.theta)
            ),
            theta=self.state.theta,
        )

        return self._apply_transition(
            proposed_state
        )

    def move_backward(
        self,
        speed_scale: float = 1.0,
    ) -> RobotState:
        """
        Move backward relative to the robot's current heading.
        """

        step = (
            self.linear_step
            * speed_scale
        )

        proposed_state = RobotState(
            x=(
                self.state.x
                - step
                * math.cos(self.state.theta)
            ),
            y=(
                self.state.y
                - step
                * math.sin(self.state.theta)
            ),
            theta=self.state.theta,
        )

        return self._apply_transition(
            proposed_state
        )

    def turn_left(self) -> RobotState:
        """
        Rotate counter-clockwise in place.
        """

        proposed_state = RobotState(
            x=self.state.x,
            y=self.state.y,
            theta=self._normalize_angle(
                self.state.theta
                + self.angular_step
            ),
        )

        return self._apply_transition(
            proposed_state
        )

    def turn_right(self) -> RobotState:
        """
        Rotate clockwise in place.
        """

        proposed_state = RobotState(
            x=self.state.x,
            y=self.state.y,
            theta=self._normalize_angle(
                self.state.theta
                - self.angular_step
            ),
        )

        return self._apply_transition(
            proposed_state
        )

    def _apply_transition(
        self,
        proposed_state: RobotState,
    ) -> RobotState:
        """
        Submit the proposed state to the Arena.

        The Robot does not decide whether the transition is
        physically possible. The Arena does.
        """

        resolved_state = (
            self.arena.resolve_transition(
                robot_id=self.robot_id,
                current_state=self.state,
                proposed_state=proposed_state,
                radius=self.radius,
            )
        )

        self.state = resolved_state

        return self.state

    @staticmethod
    def _normalize_angle(
        theta: float,
    ) -> float:
        """
        Normalize heading into [0, 2π).
        """

        return theta % (2 * math.pi)