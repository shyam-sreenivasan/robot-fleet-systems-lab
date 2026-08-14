import time

import requests

from simulator.telemetry.interface import (
    TelemetryPublisher,
)

from simulator.telemetry.message import (
    TelemetryMessage,
)


class DirectPublisher(TelemetryPublisher):
    """
    Publishes robot telemetry directly to the cloud/backend
    using HTTP.

    Connectivity decisions are delegated to TelemetryControl.
    """

    def __init__(
        self,
        endpoint: str,
        telemetry_control=None,
        timeout_seconds: float = 1.0,
    ):
        self.endpoint = endpoint
        self.telemetry_control = (
            telemetry_control
        )

        self.timeout_seconds = (
            timeout_seconds
        )

    def publish(
        self,
        robot,
    ):
        if (
            self.telemetry_control
            is not None
            and not self.telemetry_control.can_publish(
                robot.robot_id
            )
        ):
            return

        message = TelemetryMessage(
            robot_id=robot.robot_id,
            timestamp=time.time(),

            x=robot.state.x,
            y=robot.state.y,
            theta=robot.state.theta,
        )

        try:
            response = requests.post(
                self.endpoint,
                json=message.to_dict(),
                timeout=self.timeout_seconds,
            )

            response.raise_for_status()

        except requests.RequestException as exc:
            print(
                f"[TELEMETRY] "
                f"Failed to publish "
                f"{robot.robot_id}: {exc}"
            )