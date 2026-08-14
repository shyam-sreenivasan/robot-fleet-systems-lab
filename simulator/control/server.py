import threading

import uvicorn

from fastapi import FastAPI
from fastapi import HTTPException

from simulator.control.command import (
    ExperimentCommand,
)


def create_control_app(
    command_router,
):
    app = FastAPI(
        title="Robot Fleet Simulator Control Plane"
    )

    @app.get("/health")
    def health():
        return {
            "status": "ok"
        }

    @app.post("/commands")
    def command(
        command: ExperimentCommand,
    ):
        try:
            return command_router.handle(
                command
            )

        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=str(exc),
            )

    return app


class ControlServer:
    """
    Runs the simulator experiment/control API
    in a background thread.
    """

    def __init__(
        self,
        command_router,
        host="127.0.0.1",
        port=9000,
    ):
        self.host = host
        self.port = port

        self.app = create_control_app(
            command_router
        )

        self._thread = None
        self._server = None

    def start(self):
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="warning",
        )

        self._server = (
            uvicorn.Server(
                config
            )
        )

        self._thread = threading.Thread(
            target=self._server.run,
            daemon=True,
        )

        self._thread.start()

        print(
            "[CONTROL] "
            f"Simulator control plane running at "
            f"http://{self.host}:{self.port}"
        )

    def stop(self):
        if self._server is not None:
            self._server.should_exit = True

        if self._thread is not None:
            self._thread.join(
                timeout=2
            )