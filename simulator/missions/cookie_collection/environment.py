import math

from simulator.arena import Arena, RobotState
from simulator.missions.cookie_collection.cookie import Cookie


class CookieMissionEnvironment(Arena):
    """
    Mission-specific extension of the generic Arena.

    Arena:
        owns robot/world physics.

    CookieMissionEnvironment:
        additionally owns physical cookie entities and
        cookie collection rules.
    """

    def __init__(
        self,
        width: float,
        height: float,
    ):
        super().__init__(
            width=width,
            height=height,
        )

        self.cookies = {}

    def add_cookie(
        self,
        cookie: Cookie,
    ):
        if cookie.cookie_id in self.cookies:
            raise ValueError(
                f"Cookie '{cookie.cookie_id}' already exists."
            )

        if not self.can_spawn_cookie(
            cookie.x,
            cookie.y,
            cookie.radius,
        ):
            raise ValueError(
                f"Invalid cookie position: "
                f"({cookie.x}, {cookie.y})"
            )

        self.cookies[cookie.cookie_id] = cookie

    def remove_cookie(
        self,
        cookie_id: str,
    ):
        return self.cookies.pop(
            cookie_id,
            None,
        )

    def get_cookie(
        self,
        cookie_id: str,
    ):
        return self.cookies.get(
            cookie_id
        )

    def get_cookies(self):
        return list(
            self.cookies.values()
        )

    def assign_cookie(
        self,
        cookie_id: str,
        robot_id: str,
    ):
        cookie = self.get_cookie(
            cookie_id
        )

        if cookie is None:
            raise ValueError(
                f"Unknown cookie: {cookie_id}"
            )

        cookie.assigned_robot_id = (
            robot_id
        )

    def can_spawn_cookie(
        self,
        x: float,
        y: float,
        radius: float,
    ) -> bool:

        # Keep the complete cookie inside the arena.
        if not (
            radius <= x <= self.width - radius
            and radius <= y <= self.height - radius
        ):
            return False

        # Do not spawn on a robot.
        for robot in self.robots.values():

            dx = x - robot.state.x
            dy = y - robot.state.y

            minimum_distance = (
                radius
                + robot.radius
                + 1.0
            )

            if (
                dx * dx + dy * dy
                < minimum_distance * minimum_distance
            ):
                return False

        # Do not spawn cookies on top of each other.
        for cookie in self.cookies.values():

            dx = x - cookie.x
            dy = y - cookie.y

            minimum_distance = (
                radius
                + cookie.radius
                + 1.0
            )

            if (
                dx * dx + dy * dy
                < minimum_distance * minimum_distance
            ):
                return False

        return True

    def _overlaps_blocking_cookie(
        self,
        robot_id: str,
        proposed_state: RobotState,
        robot_radius: float,
    ) -> bool:

        for cookie in self.cookies.values():

            # The robot assigned to this cookie is allowed
            # to physically approach / overlap its target.
            if (
                cookie.assigned_robot_id
                == robot_id
            ):
                continue

            dx = (
                proposed_state.x
                - cookie.x
            )

            dy = (
                proposed_state.y
                - cookie.y
            )

            minimum_distance = (
                robot_radius
                + cookie.radius
            )

            if (
                dx * dx + dy * dy
                < minimum_distance * minimum_distance
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

        # First apply all normal Arena physics:
        # boundaries + robot/robot collision.
        resolved = super().resolve_transition(
            robot_id=robot_id,
            current_state=current_state,
            proposed_state=proposed_state,
            radius=radius,
        )

        # The base Arena may already have rejected translation.
        translation_accepted = (
            resolved.x == proposed_state.x
            and resolved.y == proposed_state.y
        )

        if not translation_accepted:
            return resolved

        # Now apply cookie collision semantics.
        if self._overlaps_blocking_cookie(
            robot_id=robot_id,
            proposed_state=resolved,
            robot_radius=radius,
        ):
            return RobotState(
                x=current_state.x,
                y=current_state.y,
                theta=proposed_state.theta,
            )

        return resolved

    def collect_if_reached(
        self,
        robot,
    ):
        """
        Environment is the authority on whether physical
        collection actually occurred.
        """

        for cookie in self.cookies.values():

            if (
                cookie.assigned_robot_id
                != robot.robot_id
            ):
                continue

            dx = (
                robot.state.x
                - cookie.x
            )

            dy = (
                robot.state.y
                - cookie.y
            )

            distance = math.sqrt(
                dx * dx + dy * dy
            )

            # Robot only needs its center to reach roughly
            # the cookie center/collection region.
            collection_distance = (
                robot.radius * 0.5
                + cookie.radius
            )

            if distance <= collection_distance:

                return self.remove_cookie(
                    cookie.cookie_id
                )

        return None

    def is_position_free_for_robot(
        self,
        robot,
        x: float,
        y: float,
    ) -> bool:

        radius = robot.radius

        # Arena boundary.
        if not (
            radius <= x <= self.width - radius
            and radius <= y <= self.height - radius
        ):
            return False

        # Other robots.
        for other_robot in self.robots.values():

            if (
                other_robot.robot_id
                == robot.robot_id
            ):
                continue

            dx = (
                x
                - other_robot.state.x
            )

            dy = (
                y
                - other_robot.state.y
            )

            minimum_distance = (
                radius
                + other_robot.radius
            )

            if (
                dx * dx + dy * dy
                < minimum_distance
                * minimum_distance
            ):
                return False

        # Cookies.
        for cookie in self.cookies.values():

            # Assigned cookie is the goal,
            # therefore this robot may approach it.
            if (
                cookie.assigned_robot_id
                == robot.robot_id
            ):
                continue

            dx = (
                x
                - cookie.x
            )

            dy = (
                y
                - cookie.y
            )

            minimum_distance = (
                radius
                + cookie.radius
            )

            if (
                dx * dx + dy * dy
                < minimum_distance
                * minimum_distance
            ):
                return False

        return True