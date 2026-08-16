import argparse
import math
from datetime import datetime

from simulator.robot import Robot

from simulator.missions.cookie_collection.environment import (
    CookieMissionEnvironment,
)

from simulator.missions.cookie_collection.generator import (
    CookieGenerator,
)

from simulator.missions.cookie_collection.task_controller import (
    TaskController,
)

from simulator.missions.cookie_collection.collector_controller import (
    CookieCollectorController,
)

from simulator.missions.cookie_collection.simulation import (
    CookieMissionSimulation,
)

from simulator.missions.cookie_collection.edge.event_bus import (
    EdgeEventBus,
)

from simulator.missions.cookie_collection.edge.console_sink import (
    ConsoleEventSink,
)

from simulator.missions.cookie_collection.edge.backend_sink import (
    BackendEventPublisher,
)

from simulator.missions.cookie_collection.edge.live_state_publisher import (
    LiveMissionStatePublisher,
)


def build_robot_configs(
    robot_count,
):
    configs = {
        3: [
            (15, 10, 0.0),
            (50, 65, math.pi),
            (85, 10, math.pi),
        ],
        4: [
            (10, 10, 0.0),
            (30, 10, 0.0),
            (50, 65, math.pi),
            (80, 65, math.pi),
        ],

        7: [
            (10, 10, 0.0),
            (30, 10, 0.0),
            (50, 10, 0.0),
            (70, 10, 0.0),

            (20, 65, 0.0),
            (50, 65, math.pi),
            (80, 65, math.pi),
        ],

        10: [
            (10, 10, 0.0),
            (30, 10, 0.0),
            (50, 10, 0.0),
            (70, 10, 0.0),
            (90, 10, math.pi),

            (10, 65, 0.0),
            (30, 65, 0.0),
            (50, 65, math.pi),
            (70, 65, math.pi),
            (90, 65, math.pi),
        ],
    }

    if robot_count not in configs:
        raise ValueError(
            f"No robot configuration "
            f"defined for {robot_count} robots."
        )

    return configs[
        robot_count
    ]


def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--robot-count",
        type=int,
        default=7,
        choices=[
            3,
            4,
            7,
            10,
        ],
    )

    parser.add_argument(
        "--duration",
        type=float,
        default=None,
        help=(
            "Duration in seconds. "
            "Without this option, the simulation "
            "runs until manually closed."
        ),
    )

    parser.add_argument(
        "--headless",
        action="store_true",
    )

    return parser.parse_args()


def main():
    args = parse_arguments()

    # ==============================================================
    # Run identity
    # ==============================================================

    run_id = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    print()
    print(
        f"[MISSION RUN] "
        f"run_id={run_id} "
        f"robots={args.robot_count} "
        f"duration={args.duration} "
        f"headless={args.headless}"
    )

    # ==============================================================
    # 1. Mission environment
    # ==============================================================

    environment = CookieMissionEnvironment(
        width=100,
        height=75,
    )

    # ==============================================================
    # 2. Edge event infrastructure
    # ==============================================================

    event_bus = EdgeEventBus()

    console_sink = ConsoleEventSink()

    backend_sink = BackendEventPublisher(
        backend_url="http://localhost:8000",
        timeout_seconds=1.0,
    )

    # Keep console output for visual/manual runs.
    if not args.headless:
        event_bus.register_sink(
            console_sink
        )

    event_bus.register_sink(
        backend_sink
    )

    # ==============================================================
    # 3. Robots
    # ==============================================================

    robot_configs = build_robot_configs(
        args.robot_count
    )

    robots = []

    for index, (
        x,
        y,
        theta,
    ) in enumerate(
        robot_configs,
        start=1,
    ):
        robot = Robot(
            robot_id=f"robot_{index}",
            arena=environment,
            x=x,
            y=y,
            theta=theta,
            linear_step=0.45,
            angular_step=math.radians(
                8
            ),
            radius=2,
        )

        robots.append(
            robot
        )

    # ==============================================================
    # 4. Task controller
    # ==============================================================

    task_controller = TaskController(
        environment=environment,
        event_bus=event_bus,
        run_id=run_id,
    )

    for robot in robots:
        task_controller.register_robot(
            robot
        )

    # ==============================================================
    # 5. Cookie generator
    # ==============================================================

    cookie_generator = CookieGenerator(
        environment=environment,
        event_bus=event_bus,
        run_id=run_id,
        spawn_interval_seconds=1.5,
        seed=42,
        cookie_radius=1.0,
        margin=7.0,
        max_active_cookies=12,
    )

    cookie_generator.on_cookie_spawned = (
        task_controller.on_cookie_spawned
    )

    # ==============================================================
    # 6. Robot controllers
    # ==============================================================

    controllers = [
        CookieCollectorController(
            robot=robot,
            task_controller=task_controller,
            run_id=run_id,
            environment=environment,
            event_bus=event_bus,
            planner_seed=1000 + index,
        )
        for index, robot in enumerate(
            robots,
            start=1,
        )
    ]

    # ==============================================================
    # 7. Live dashboard state
    # ==============================================================

    live_state_publisher = (
        LiveMissionStatePublisher(
            backend_url="http://localhost:8000",
            timeout_seconds=0.25,
        )
    )

    # ==============================================================
    # 8. Simulation
    # ==============================================================

    simulation = CookieMissionSimulation(
        arena=environment,
        robots=robots,
        controllers=controllers,
        cookie_generator=cookie_generator,
        task_controller=task_controller,
        live_state_publisher=live_state_publisher,
        live_state_frequency_hz=10.0,

        # THESE WERE MISSING
        duration_seconds=args.duration,
        headless=args.headless,
    )

    # ==============================================================
    # 9. Run
    # ==============================================================

    simulation.run()


if __name__ == "__main__":
    main()