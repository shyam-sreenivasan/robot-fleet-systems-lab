import math

from simulator.arena import Arena
from simulator.robot import Robot
from simulator.simulation import Simulation

from simulator.sensors.lidar import Lidar
import threading

from simulator.controllers.autonomous_controller import (
    AutonomousController,
)

from simulator.telemetry.direct_publisher import (
    DirectPublisher,
)

from simulator.telemetry.control import (
    TelemetryControl,
)

from simulator.control.router import (
    CommandRouter,
)

from simulator.control.server import (
    ControlServer,
)



def main():
    arena = Arena(
        width=100,
        height=75,
    )

    robot_configs = [
        (
            15,
            15,
            0,
        ),
        (
            35,
            15,
            math.radians(45),
        ),
        (
            55,
            15,
            math.radians(90),
        ),
        (
            80,
            15,
            math.radians(135),
        ),
        (
            15,
            55,
            math.radians(180),
        ),
        (
            35,
            55,
            math.radians(225),
        ),
        (
            55,
            55,
            math.radians(270),
        ),
        (
            80,
            55,
            math.radians(315),
        ),
    ]

    robots = []
    controllers = []

    for index, (
        x,
        y,
        theta,
    ) in enumerate(
        robot_configs,
        start=1,
    ):
        lidar = Lidar(
            field_of_view_degrees=150,
            num_rays=31,
            max_range=5,
        )

        robot = Robot(
            robot_id=f"robot_{index}",
            arena=arena,
            x=x,
            y=y,
            theta=theta,
            linear_step=0.25,
            angular_step=math.radians(5),
            radius=2.0,
            lidar=lidar,
        )

        controller = AutonomousController(
            robot=robot,
            obstacle_threshold=4.0,
        )

        robots.append(
            robot
        )

        controllers.append(
            controller
        )

    telemetry_control = (
        TelemetryControl()
    )

    telemetry_publisher = (
        DirectPublisher(
            endpoint=(
                "http://localhost:8000/telemetry"
            ),
            telemetry_control=(
                telemetry_control
            ),
        )
    )

    command_router = CommandRouter(
        telemetry_control=(
            telemetry_control
        )
    )

    control_server = ControlServer(
        command_router=command_router,
        port=9000,
    )

    control_server.start()

    simulation = Simulation(
        arena=arena,
        robots=robots,
        controllers=controllers,
        telemetry_publisher=(
            telemetry_publisher
        ),
        telemetry_frequency_hz=2.0,
    )

    try:
        simulation.run()

    finally:
        control_server.stop()


if __name__ == "__main__":
    main()