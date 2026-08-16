import requests


class BackendEventPublisher:
    """
    Publishes mission events from the edge event bus
    to the backend over HTTP.

    Backend failures are treated as non-fatal for the
    simulator. The robot mission should continue even if
    observability delivery temporarily fails.
    """

    def __init__(
        self,
        backend_url="http://localhost:8000",
        timeout_seconds=1.0,
    ):
        self.backend_url = (
            backend_url.rstrip("/")
        )

        self.timeout_seconds = (
            timeout_seconds
        )

        self.endpoint = (
            f"{self.backend_url}/mission-events"
        )

    def handle(
        self,
        event,
    ):
        try:
            response = requests.post(
                self.endpoint,
                json=event.to_dict(),
                timeout=self.timeout_seconds,
            )

            response.raise_for_status()

        except requests.RequestException as exc:
            print(
                "[EVENT DELIVERY FAILED] "
                f"{event.event_type} "
                f"event_id={event.event_id} "
                f"error={exc}"
            )