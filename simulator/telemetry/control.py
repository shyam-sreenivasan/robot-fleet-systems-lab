import time
from threading import Lock


class TelemetryControl:
    """
    Controls whether telemetry from individual robots
    is allowed to leave the simulator.

    This represents the controllable network/telemetry
    boundary for experiments.

    It does not publish telemetry itself.
    """

    def __init__(self):
        self._disabled_until = {}
        self._lock = Lock()

    def disable_for(
        self,
        robot_id: str,
        duration_seconds: float,
    ):
        if duration_seconds <= 0:
            raise ValueError(
                "duration_seconds must be greater than zero."
            )

        with self._lock:
            self._disabled_until[robot_id] = (
                time.monotonic()
                + duration_seconds
            )

        print(
            f"[TELEMETRY CONTROL] "
            f"{robot_id} disabled for "
            f"{duration_seconds:.1f}s"
        )

    def enable(
        self,
        robot_id: str,
    ):
        with self._lock:
            self._disabled_until.pop(
                robot_id,
                None,
            )

        print(
            f"[TELEMETRY CONTROL] "
            f"{robot_id} enabled"
        )

    def can_publish(
        self,
        robot_id: str,
    ) -> bool:
        with self._lock:

            disabled_until = (
                self._disabled_until.get(
                    robot_id
                )
            )

            if disabled_until is None:
                return True

            if (
                time.monotonic()
                >= disabled_until
            ):
                del self._disabled_until[
                    robot_id
                ]

                print(
                    f"[TELEMETRY CONTROL] "
                    f"{robot_id} automatically restored"
                )

                return True

            return False