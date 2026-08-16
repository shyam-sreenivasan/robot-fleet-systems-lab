import math
import time

from simulator.controllers.controller import Controller

from simulator.missions.cookie_collection.planning.rrt import (
    RRTPlanner,
)

from simulator.missions.cookie_collection.edge.event import (
    MissionEvent,
)


class CookieCollectorController(Controller):
    """
    Robot-side mission controller.

    Responsibilities:
    - obtain the robot's current cookie assignment
    - plan a path using RRT
    - follow the resulting waypoints
    - detect when the current path becomes invalid
    - trigger replanning
    - retry transient planning failures
    - publish planning events to the edge event bus

    Physical cookie collection itself is validated by
    CookieMissionEnvironment.
    """

    def __init__(
        self,
        robot,
        task_controller,
        environment,
        event_bus,
        run_id,
        planner_seed=42,
        waypoint_tolerance=1.0,
        heading_tolerance_degrees=8.0,
        retry_plan_after_ticks=15,
    ):
        self.robot = robot
        self.task_controller = task_controller
        self.environment = environment
        self.event_bus = event_bus
        self.run_id = run_id

        self.planner = RRTPlanner(
            environment=environment,
            step_size=3.0,
            goal_sample_rate=0.20,
            max_iterations=2000,
            collision_check_resolution=0.5,
            seed=planner_seed,
        )

        self.waypoint_tolerance = (
            waypoint_tolerance
        )

        self.heading_tolerance = (
            math.radians(
                heading_tolerance_degrees
            )
        )

        self.current_cookie_id = None

        self.path = None
        self.waypoint_index = 0

        # --------------------------------------------------------------
        # Local counters
        #
        # These remain useful for debugging, but the edge event stream
        # will eventually be the source from which platform metrics
        # are derived.
        # --------------------------------------------------------------

        self.replan_count = 0
        self.planning_failures = 0

        # --------------------------------------------------------------
        # Failed-plan recovery
        # --------------------------------------------------------------

        self.failed_plan_wait_ticks = 0

        self.retry_plan_after_ticks = (
            retry_plan_after_ticks
        )

    def step(self):
        """
        Called every simulation tick.
        """

        cookie = (
            self.task_controller.get_assignment(
                self.robot.robot_id
            )
        )

        # --------------------------------------------------------------
        # No mission
        # --------------------------------------------------------------

        if cookie is None:
            self._clear_path()
            return

        # --------------------------------------------------------------
        # New cookie assignment
        # --------------------------------------------------------------

        if (
            cookie.cookie_id
            != self.current_cookie_id
        ):
            self.current_cookie_id = (
                cookie.cookie_id
            )

            self._plan(
                cookie,
                is_replan=False,
            )

        # --------------------------------------------------------------
        # Previous planning attempt failed
        #
        # The world is dynamic. A planning failure does not necessarily
        # mean that the task is impossible.
        #
        # Wait briefly and try again.
        # --------------------------------------------------------------

        if not self.path:

            self.failed_plan_wait_ticks += 1

            if (
                self.failed_plan_wait_ticks
                >= self.retry_plan_after_ticks
            ):
                self.failed_plan_wait_ticks = 0

                self._plan(
                    cookie,
                    is_replan=True,
                )

            return

        # --------------------------------------------------------------
        # Finished path
        # --------------------------------------------------------------

        if (
            self.waypoint_index
            >= len(self.path)
        ):
            return

        waypoint = self.path[
            self.waypoint_index
        ]

        dx = (
            waypoint.x
            - self.robot.state.x
        )

        dy = (
            waypoint.y
            - self.robot.state.y
        )

        distance = math.hypot(
            dx,
            dy,
        )

        # --------------------------------------------------------------
        # Waypoint reached
        # --------------------------------------------------------------

        if (
            distance
            <= self.waypoint_tolerance
        ):
            self.waypoint_index += 1

            if (
                self.waypoint_index
                >= len(self.path)
            ):
                return

            waypoint = self.path[
                self.waypoint_index
            ]

            dx = (
                waypoint.x
                - self.robot.state.x
            )

            dy = (
                waypoint.y
                - self.robot.state.y
            )

        # --------------------------------------------------------------
        # Dynamic path validation
        #
        # A path may have been valid when RRT generated it, but another
        # robot or cookie may have moved/appeared in the segment between
        # this robot and the next waypoint.
        # --------------------------------------------------------------

        segment_is_free = (
            self.planner.segment_is_free(
                robot=self.robot,

                start_x=self.robot.state.x,
                start_y=self.robot.state.y,

                end_x=waypoint.x,
                end_y=waypoint.y,
            )
        )

        if not segment_is_free:

            self._plan(
                cookie,
                is_replan=True,
                replan_reason="PATH_BLOCKED",
            )

            return

        # --------------------------------------------------------------
        # Heading control
        # --------------------------------------------------------------

        desired_heading = math.atan2(
            dy,
            dx,
        )

        heading_error = (
            desired_heading
            - self.robot.state.theta
        )

        # Normalize to [-pi, pi].
        heading_error = (
            heading_error
            + math.pi
        ) % (
            2 * math.pi
        ) - math.pi

        if (
            abs(heading_error)
            > self.heading_tolerance
        ):
            if heading_error > 0:
                self.robot.turn_left()
            else:
                self.robot.turn_right()

            return

        # --------------------------------------------------------------
        # Move toward waypoint
        # --------------------------------------------------------------

        self.robot.move_forward(
            speed_scale=1.0
        )

    def _plan(
        self,
        cookie,
        is_replan=False,
        replan_reason=None,
    ):
        """
        Attempt to produce a path from the robot's current state
        to its assigned cookie.
        """

        # --------------------------------------------------------------
        # Replan event
        # --------------------------------------------------------------

        if is_replan:

            self.replan_count += 1

            replan_event = MissionEvent.create(
                event_type="REPLAN_TRIGGERED",
                mission_id="cookie_collection",
                robot_id=self.robot.robot_id,
                run_id=self.run_id,

                state=(
                    self._robot_state_snapshot()
                ),

                metadata={
                    "cookie_id":
                        cookie.cookie_id,

                    "reason":
                        replan_reason
                        or "PLAN_RETRY",

                    "replan_count":
                        self.replan_count,

                    "goal": {
                        "x": cookie.x,
                        "y": cookie.y,
                    },
                },
            )

            self.event_bus.publish(
                replan_event
            )

        # --------------------------------------------------------------
        # PLAN_STARTED
        # --------------------------------------------------------------

        plan_started_event = (
            MissionEvent.create(
                event_type="PLAN_STARTED",
                mission_id="cookie_collection",
                robot_id=self.robot.robot_id,
                run_id=self.run_id, 

                state=(
                    self._robot_state_snapshot()
                ),

                metadata={
                    "cookie_id":
                        cookie.cookie_id,

                    "goal": {
                        "x": cookie.x,
                        "y": cookie.y,
                    },

                    "is_replan":
                        is_replan,

                    "planner": {
                        "type": "RRT",
                        "version": "rrt_v1",
                        "step_size":
                            self.planner.step_size,
                        "goal_sample_rate":
                            self.planner.goal_sample_rate,
                        "max_iterations":
                            self.planner.max_iterations,
                    },
                },
            )
        )

        self.event_bus.publish(
            plan_started_event
        )

        # --------------------------------------------------------------
        # Execute planner
        # --------------------------------------------------------------

        plan_started_at = (
            time.perf_counter()
        )

        path = self.planner.plan(
            robot=self.robot,
            goal_x=cookie.x,
            goal_y=cookie.y,
        )

        planning_latency_ms = (
            (
                time.perf_counter()
                - plan_started_at
            )
            * 1000.0
        )

        # --------------------------------------------------------------
        # PLAN_FAILED
        # --------------------------------------------------------------

        if path is None:

            self.planning_failures += 1

            failure_event = (
                MissionEvent.create(
                    event_type="PLAN_FAILED",
                    mission_id="cookie_collection",
                    robot_id=self.robot.robot_id,
                    run_id=self.run_id, 

                    state=(
                        self._robot_state_snapshot()
                    ),

                    metadata={
                        "cookie_id":
                            cookie.cookie_id,

                        "goal": {
                            "x": cookie.x,
                            "y": cookie.y,
                        },

                        "planning_latency_ms":
                            planning_latency_ms,

                        "planning_failure_count":
                            self.planning_failures,

                        "replan_count":
                            self.replan_count,

                        "is_replan":
                            is_replan,

                        # Snapshot of relevant system state.
                        #
                        # Later this lets us ask questions such as:
                        #
                        # - Do failures increase with congestion?
                        # - Do failures correlate with cookie density?
                        # - Are failures concentrated on specific robots?
                        #
                        "environment": {
                            "active_cookie_count":
                                len(
                                    self.environment.get_cookies()
                                ),

                            "robot_count":
                                len(
                                    self.environment.robots
                                ),

                            "open_cookie_count":
                                len(
                                    self.task_controller.open_cookies
                                ),

                            "active_assignment_count":
                                len(
                                    self.task_controller.assignments
                                ),
                        },

                        "planner": {
                            "type":
                                "RRT",

                            "version":
                                "rrt_v1",

                            "step_size":
                                self.planner.step_size,

                            "goal_sample_rate":
                                self.planner.goal_sample_rate,

                            "max_iterations":
                                self.planner.max_iterations,
                        },
                    },
                )
            )

            self.event_bus.publish(
                failure_event
            )

            self.path = None
            self.waypoint_index = 0

            return

        # --------------------------------------------------------------
        # PLAN_SUCCEEDED
        # --------------------------------------------------------------

        self.failed_plan_wait_ticks = 0

        success_event = (
            MissionEvent.create(
                event_type="PLAN_SUCCEEDED",
                mission_id="cookie_collection",
                robot_id=self.robot.robot_id,
                run_id=self.run_id, 
                state=(
                    self._robot_state_snapshot()
                ),

                metadata={
                    "cookie_id":
                        cookie.cookie_id,

                    "goal": {
                        "x": cookie.x,
                        "y": cookie.y,
                    },

                    "planning_latency_ms":
                        planning_latency_ms,

                    "waypoint_count":
                        len(path),

                    "is_replan":
                        is_replan,

                    "replan_count":
                        self.replan_count,

                    "planner": {
                        "type":
                            "RRT",

                        "version":
                            "rrt_v1",
                    },
                },
            )
        )

        self.event_bus.publish(
            success_event
        )

        # --------------------------------------------------------------
        # Store new path
        # --------------------------------------------------------------

        self.path = path

        # First point is the robot's current position.
        self.waypoint_index = min(
            1,
            len(path) - 1,
        )

    def _robot_state_snapshot(
        self,
    ):
        """
        Capture robot state at the instant an event occurs.
        """

        return {
            "x":
                self.robot.state.x,

            "y":
                self.robot.state.y,

            "theta":
                self.robot.state.theta,
        }

    def _clear_path(
        self,
    ):
        self.current_cookie_id = None

        self.path = None
        self.waypoint_index = 0

        self.failed_plan_wait_ticks = 0