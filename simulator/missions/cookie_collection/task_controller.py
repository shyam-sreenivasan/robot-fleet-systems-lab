from collections import deque
import time
from simulator.missions.cookie_collection.edge.event import (
    MissionEvent,
)


class TaskController:
    """
    Edge-side mission/task controller.

    Owns:
    - open task queue
    - robot availability
    - robot -> cookie assignments
    - mission completion state

    Phase 1 output is console-only.
    """

    def __init__(
        self,
        environment,
        event_bus,
        run_id
    ):
        self.environment = (
            environment
        )

        self.event_bus = event_bus

        self.open_cookies = deque()

        self.available_robots = deque()

        # robot_id -> cookie_id
        self.assignments = {}

        self.collected_count = 0
        self.run_id = run_id

    def register_robot(
        self,
        robot,
    ):
        self.available_robots.append(
            robot.robot_id
        )

    def on_cookie_spawned(
        self,
        cookie,
    ):
        self.open_cookies.append(
            cookie.cookie_id
        )

        self.schedule()

    def schedule(self):

        while (
            self.open_cookies
            and self.available_robots
        ):
            cookie_id = (
                self.open_cookies.popleft()
            )

            robot_id = (
                self.available_robots.popleft()
            )

            # Cookie may have disappeared for some reason.
            cookie = self.environment.get_cookie(
                cookie_id
            )

            if cookie is None:
                continue

            self.assignments[
                robot_id
            ] = cookie_id

            self.environment.assign_cookie(
                cookie_id=cookie_id,
                robot_id=robot_id,
            )

            event = MissionEvent.create(
            event_type="COOKIE_ASSIGNED",
            mission_id="cookie_collection",
            robot_id=robot_id,
            run_id=self.run_id, 
            metadata={
                "cookie_id": cookie_id,
                "cookie_x": cookie.x,
                "cookie_y": cookie.y,
            },
        )

            self.event_bus.publish(
                event
            )

    def get_assignment(
        self,
        robot_id: str,
    ):
        cookie_id = (
            self.assignments.get(
                robot_id
            )
        )

        if cookie_id is None:
            return None

        return self.environment.get_cookie(
            cookie_id
        )

    def handle_collection(
        self,
        robot,
        cookie,
    ):
        expected_cookie_id = (
            self.assignments.get(
                robot.robot_id
            )
        )

        if (
            expected_cookie_id
            != cookie.cookie_id
        ):
            raise RuntimeError(
                f"{robot.robot_id} collected "
                f"{cookie.cookie_id}, but was assigned "
                f"{expected_cookie_id}."
            )

        del self.assignments[
            robot.robot_id
        ]

        self.collected_count += 1

        timestamp = time.time()

        event = MissionEvent.create(
        event_type="COOKIE_COLLECTED",
        mission_id="cookie_collection",
        robot_id=robot.robot_id,
        run_id=self.run_id, 
        state={
            "x": robot.state.x,
            "y": robot.state.y,
            "theta": robot.state.theta,
        },
        metadata={
            "cookie_id": cookie.cookie_id,
            "total_collected": self.collected_count,
        },
    )

        self.event_bus.publish(
            event
        )

        # Completion implicitly means the robot is free.
        self.available_robots.append(
            robot.robot_id
        )

        self.schedule()