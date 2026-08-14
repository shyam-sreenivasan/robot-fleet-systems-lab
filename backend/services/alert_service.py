import time
import uuid
from threading import Lock

from backend.models.alert import Alert


TELEMETRY_LOST = "TELEMETRY_LOST"

ACTIVE = "ACTIVE"
RESOLVED = "RESOLVED"


class AlertService:

    def __init__(self):
        self._alerts = []
        self._lock = Lock()

    def create_telemetry_lost_alert(
        self,
        robot_id: str,
        last_seen_at: float,
    ):
        """
        Create one active TELEMETRY_LOST alert for a robot.

        Duplicate active alerts are not created.
        """

        with self._lock:

            existing = self._find_active_alert(
                robot_id=robot_id,
                alert_type=TELEMETRY_LOST,
            )

            if existing is not None:
                return existing

            alert = Alert(
                alert_id=str(
                    uuid.uuid4()
                ),

                robot_id=robot_id,
                alert_type=TELEMETRY_LOST,

                status=ACTIVE,

                started_at=time.time(),
                last_seen_at=last_seen_at,

                resolved_at=None,
            )

            self._alerts.append(
                alert
            )

            return alert

    def resolve_telemetry_lost_alert(
        self,
        robot_id: str,
    ) -> bool:
        """
        Resolve the active telemetry-lost alert for a robot.

        Returns True if an alert was actually resolved.
        """

        with self._lock:

            alert = self._find_active_alert(
                robot_id=robot_id,
                alert_type=TELEMETRY_LOST,
            )

            if alert is None:
                return False

            alert.status = RESOLVED
            alert.resolved_at = time.time()

            return True

    def get_all(
        self,
        active_only: bool = False,
    ):
        with self._lock:

            alerts = self._alerts

            if active_only:
                alerts = [
                    alert
                    for alert in alerts
                    if alert.status == ACTIVE
                ]

            return [
                self._to_dict(alert)
                for alert in alerts
            ]

    def active_count(self):
        with self._lock:

            return sum(
                1
                for alert in self._alerts
                if alert.status == ACTIVE
            )

    def _find_active_alert(
        self,
        robot_id: str,
        alert_type: str,
    ):
        for alert in self._alerts:

            if (
                alert.robot_id == robot_id
                and alert.alert_type == alert_type
                and alert.status == ACTIVE
            ):
                return alert

        return None

    @staticmethod
    def _to_dict(alert):
        return {
            "alert_id": alert.alert_id,
            "robot_id": alert.robot_id,
            "type": alert.alert_type,

            "status": alert.status,

            "started_at": alert.started_at,
            "last_seen_at": alert.last_seen_at,
            "resolved_at": alert.resolved_at,
        }