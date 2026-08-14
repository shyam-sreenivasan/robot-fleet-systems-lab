import threading
import time


class HealthMonitor:
    """
    Periodically checks telemetry freshness.

    If a robot has not been seen within the configured timeout,
    it transitions from ACTIVE -> UNKNOWN.
    """

    def __init__(
        self,
        fleet_state,
        alert_service,
        event_bus,
        timeout_seconds=3.0,
        check_interval_seconds=1.0,
    ):
        self.fleet_state = fleet_state
        self.alert_service = alert_service
        self.event_bus = event_bus

        self.timeout_seconds = timeout_seconds
        self.check_interval_seconds = (
            check_interval_seconds
        )

        self._running = False
        self._thread = None

    def start(self):
        if self._running:
            return

        self._running = True

        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
        )

        self._thread.start()

    def stop(self):
        self._running = False

        if self._thread is not None:
            self._thread.join(
                timeout=2
            )

    def _run(self):

        while self._running:

            self.check_health()

            time.sleep(
                self.check_interval_seconds
            )

    def check_health(self):
        now = time.time()

        robots = (
            self.fleet_state
            .get_all_internal()
        )

        for robot in robots:

            telemetry_age = (
                now
                - robot.last_seen
            )

            if (
                telemetry_age
                > self.timeout_seconds
            ):
                transitioned = (
                    self.fleet_state
                    .mark_unknown(
                        robot.robot_id
                    )
                )

                if transitioned:

                    print(
                        "[HEALTH] "
                        f"{robot.robot_id} "
                        f"ACTIVE -> UNKNOWN "
                        f"(last seen "
                        f"{telemetry_age:.1f}s ago)"
                    )

                    alert = (
                        self.alert_service
                        .create_telemetry_lost_alert(
                            robot_id=robot.robot_id,
                            last_seen_at=robot.last_seen,
                        )
                    )

                    self.event_bus.publish(
                        {
                            "type": "ROBOT_STATUS_CHANGED",
                            "robot_id": robot.robot_id,
                            "status": "UNKNOWN",
                            "last_seen": robot.last_seen,
                        }
                    )

                    self.event_bus.publish(
                        {
                            "type": "ALERT_CREATED",
                            "alert": {
                                "alert_id": alert.alert_id,
                                "robot_id": alert.robot_id,
                                "type": alert.alert_type,
                                "status": alert.status,
                                "started_at": alert.started_at,
                                "last_seen_at": alert.last_seen_at,
                            },
                        }
                    )