import requests


class LiveMissionStatePublisher:
    """
    Publishes ephemeral, high-frequency mission state.

    This is intentionally separate from MissionEvent.

    MissionEvent:
        durable-ish atomic events used for analytics

    LiveMissionStatePublisher:
        transient operational state used for visualization
    """

    def __init__(
        self,
        backend_url="http://localhost:8000",
        timeout_seconds=0.25,
    ):
        self.backend_url = backend_url.rstrip("/")

        self.endpoint = (
            f"{self.backend_url}/live-mission-state"
        )

        self.timeout_seconds = timeout_seconds

    def publish(
        self,
        robots,
        environment,
    ):
        payload = {
            "mission_id": "cookie_collection",

            "robots": [
                {
                    "robot_id": robot.robot_id,
                    "x": robot.state.x,
                    "y": robot.state.y,
                    "theta": robot.state.theta,
                }
                for robot in robots
            ],

            "cookies": [
                {
                    "cookie_id": cookie.cookie_id,
                    "x": cookie.x,
                    "y": cookie.y,
                    "radius": cookie.radius,
                    "assigned_robot_id":
                        cookie.assigned_robot_id,
                }
                for cookie
                in environment.get_cookies()
            ],
        }

        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                timeout=self.timeout_seconds,
            )

            response.raise_for_status()

        except requests.RequestException:
            # Live visualization must never interfere
            # with the physical mission loop.
            pass