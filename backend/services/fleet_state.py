import time
from threading import Lock

from backend.models.robot_state import RobotFleetState
from backend.models.telemetry import TelemetryPayload


class FleetState:
    """
    Stores the backend's latest known state for every robot.

    This is intentionally in-memory for V1.
    """

    def __init__(self):
        self._robots = {}
        self._lock = Lock()

    def update_from_telemetry(
        self,
        telemetry: TelemetryPayload,
    ):
        """
        Update the latest known state for a robot.

        Any received telemetry means the backend can currently
        consider that robot ACTIVE.
        """

        now = time.time()

        with self._lock:

            existing = self._robots.get(
                telemetry.robot_id
            )

            previous_status = (
                existing.status
                if existing is not None
                else None
            )

            self._robots[
                telemetry.robot_id
            ] = RobotFleetState(
                robot_id=telemetry.robot_id,

                x=telemetry.x,
                y=telemetry.y,
                theta=telemetry.theta,

                source_timestamp=telemetry.timestamp,
                last_seen=now,

                status="ACTIVE",
            )

            return previous_status

    def mark_unknown(
        self,
        robot_id: str,
    ) -> bool:
        """
        Mark a robot UNKNOWN.

        Returns True only if a state transition actually occurred.
        """

        with self._lock:

            robot = self._robots.get(
                robot_id
            )

            if robot is None:
                return False

            if robot.status == "UNKNOWN":
                return False

            robot.status = "UNKNOWN"

            return True

    def get_robot(
        self,
        robot_id: str,
    ):
        with self._lock:

            robot = self._robots.get(
                robot_id
            )

            if robot is None:
                return None

            return self._to_dict(
                robot
            )

    def get_all(self):
        with self._lock:

            return [
                self._to_dict(robot)
                for robot in self._robots.values()
            ]

    def get_all_internal(self):
        """
        Used by backend services such as HealthMonitor.

        Returns copies so callers don't mutate FleetState directly.
        """

        with self._lock:

            return [
                RobotFleetState(
                    robot_id=robot.robot_id,
                    x=robot.x,
                    y=robot.y,
                    theta=robot.theta,
                    source_timestamp=robot.source_timestamp,
                    last_seen=robot.last_seen,
                    status=robot.status,
                )
                for robot in self._robots.values()
            ]

    def summary(self):
        with self._lock:

            robot_count = len(
                self._robots
            )

            active_count = sum(
                1
                for robot in self._robots.values()
                if robot.status == "ACTIVE"
            )

            unknown_count = sum(
                1
                for robot in self._robots.values()
                if robot.status == "UNKNOWN"
            )

            return {
                "robot_count": robot_count,
                "active_count": active_count,
                "unknown_count": unknown_count,
            }

    @staticmethod
    def _to_dict(robot):
        return {
            "robot_id": robot.robot_id,

            "x": robot.x,
            "y": robot.y,
            "theta": robot.theta,

            "source_timestamp": robot.source_timestamp,
            "last_seen": robot.last_seen,

            "status": robot.status,
        }