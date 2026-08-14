from simulator.control.command import (
    ExperimentCommand,
)


class CommandRouter:
    """
    Routes experiment commands to the subsystem
    responsible for handling them.
    """

    def __init__(
        self,
        telemetry_control,
    ):
        self.telemetry_control = (
            telemetry_control
        )

    def handle(
        self,
        command: ExperimentCommand,
    ):
        if command.target == "telemetry":
            return self._handle_telemetry(
                command
            )

        raise ValueError(
            f"Unknown command target: "
            f"{command.target}"
        )

    def _handle_telemetry(
        self,
        command: ExperimentCommand,
    ):
        if command.robot_id is None:
            raise ValueError(
                "robot_id is required "
                "for telemetry commands."
            )

        if command.action == "disconnect":

            if (
                command.duration_seconds
                is None
            ):
                raise ValueError(
                    "duration_seconds is required "
                    "for disconnect."
                )

            self.telemetry_control.disable_for(
                robot_id=command.robot_id,
                duration_seconds=(
                    command.duration_seconds
                ),
            )

            return {
                "status": "accepted",
                "target": "telemetry",
                "action": "disconnect",
                "robot_id": command.robot_id,
                "duration_seconds":
                    command.duration_seconds,
            }

        if command.action == "connect":

            self.telemetry_control.enable(
                command.robot_id
            )

            return {
                "status": "accepted",
                "target": "telemetry",
                "action": "connect",
                "robot_id": command.robot_id,
            }

        raise ValueError(
            f"Unknown telemetry action: "
            f"{command.action}"
        )