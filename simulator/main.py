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


# ======================================================================
# Robot starting configurations
# ======================================================================

def build_robot_configs(
    robot_count: int,
):
    """
    Return deterministic initial robot configurations.

    Each tuple is:

        (
            x,
            y,
            theta,
        )

    Keep configurations deterministic so fleet-size
    experiments remain reproducible.
    """

    configs = {

        # ----------------------------------------------------------
        # 3 robots
        # ----------------------------------------------------------

        3: [
            (
                15,
                10,
                0.0,
            ),

            (
                50,
                65,
                math.pi,
            ),

            (
                85,
                10,
                math.pi,
            ),
        ],

        # ----------------------------------------------------------
        # 7 robots
        # ----------------------------------------------------------

        7: [
            (
                10,
                10,
                0.0,
            ),

            (
                30,
                10,
                0.0,
            ),

            (
                50,
                10,
                0.0,
            ),

            (
                70,
                10,
                0.0,
            ),

            (
                20,
                65,
                0.0,
            ),

            (
                50,
                65,
                math.pi,
            ),

            (
                80,
                65,
                math.pi,
            ),
        ],

        # ----------------------------------------------------------
        # 10 robots
        # ----------------------------------------------------------

        10: [
            (
                10,
                10,
                0.0,
            ),

            (
                30,
                10,
                0.0,
            ),

            (
                50,
                10,
                0.0,
            ),

            (
                70,
                10,
                0.0,
            ),

            (
                90,
                10,
                math.pi,
            ),

            (
                10,
                65,
                0.0,
            ),

            (
                30,
                65,
                0.0,
            ),

            (
                50,
                65,
                math.pi,
            ),

            (
                70,
                65,
                math.pi,
            ),

            (
                90,
                65,
                math.pi,
            ),
        ],
    }

    if robot_count not in configs:
        raise ValueError(
            "Unsupported robot count: "
            f"{robot_count}. "
            "Available configurations: "
            f"{sorted(configs.keys())}"
        )

    return configs[
        robot_count
    ]


# ======================================================================
# CLI
# ======================================================================

def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Run the cookie collection "
            "fleet simulation."
        )
    )

    parser.add_argument(
        "--robot-count",
        type=int,
        default=7,
        choices=[
            3,
            7,
            10,
        ],
        help=(
            "Number of robots in the fleet."
        ),
    )

    parser.add_argument(
        "--duration",
        type=float,
        default=None,
        help=(
            "Simulation duration in seconds. "
            "If omitted, run until the "
            "Pygame window is closed."
        ),
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help=(
            "Run without rendering the "
            "Pygame simulation."
        ),
    )

    return parser.parse_args()


# ======================================================================
# Main
# ======================================================================

def main():
    args = parse_arguments()

    # ------------------------------------------------------------------
    # Mission run identity
    #
    # Microseconds are included because the fleet-size experiment
    # launcher may start several simulations almost simultaneously.
    # ------------------------------------------------------------------

    run_id = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    print()
    print("=" * 70)

    print(
        "[MISSION RUN]"
    )

    print(
        f"  run_id:       {run_id}"
    )

    print(
        f"  robot_count:  {args.robot_count}"
    )

    print(
        f"  duration:     "
        f"{args.duration if args.duration is not None else 'unbounded'}"
    )

    print(
        f"  headless:     {args.headless}"
    )

    print("=" * 70)
    print()

    # ==================================================================
    # 1. Mission environment
    # ==================================================================

    environment = (
        CookieMissionEnvironment(
            width=100,
            height=75,
        )
    )

    # ==================================================================
    # 2. Edge event infrastructure
    #
    # Mission components
    #
    #       ↓
    #
    # EdgeEventBus
    #
    #       ├── ConsoleEventSink
    #       └── BackendEventPublisher
    #
    # Backend persists events by run_id.
    # ==================================================================

    event_bus = EdgeEventBus()

    console_sink = (
        ConsoleEventSink()
    )

    backend_sink = (
        BackendEventPublisher(
            backend_url=(
                "http://localhost:8000"
            ),
            timeout_seconds=1.0,
        )
    )

    event_bus.register_sink(
        console_sink
    )

    event_bus.register_sink(
        backend_sink
    )

    # ==================================================================
    # 3. Robot configuration
    # ==================================================================

    robot_configs = (
        build_robot_configs(
            args.robot_count
        )
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
            robot_id=(
                f"robot_{index}"
            ),

            arena=environment,

            x=x,
            y=y,
            theta=theta,

            linear_step=0.45,

            angular_step=(
                math.radians(
                    8
                )
            ),

            radius=2,
        )

        robots.append(
            robot
        )

    # ==================================================================
    # 4. Edge mission/task controller
    # ==================================================================

    task_controller = (
        TaskController(
            environment=environment,
            event_bus=event_bus,
            run_id=run_id,
        )
    )

    for robot in robots:

        task_controller.register_robot(
            robot
        )

    # ==================================================================
    # 5. Cookie workload
    #
    # Important experiment constants:
    #
    #     spawn interval:      1.5 seconds
    #     theoretical rate:    40 cookies/min
    #     active-cookie cap:   12
    #     workload seed:       42
    #
    # These remain identical between the 3, 7 and 10 robot runs.
    # ==================================================================

    cookie_generator = (
        CookieGenerator(
            environment=environment,
            event_bus=event_bus,
            run_id=run_id,

            spawn_interval_seconds=1.5,

            seed=42,

            cookie_radius=1.0,

            margin=7.0,

            max_active_cookies=12,
        )
    )

    cookie_generator.on_cookie_spawned = (
        task_controller.on_cookie_spawned
    )

    # ==================================================================
    # 6. Robot-side mission controllers
    #
    # Each robot gets its own planner instance.
    #
    # Planner seeds are deterministic:
    #
    #     robot_1 -> 1001
    #     robot_2 -> 1002
    #     ...
    #
    # ==================================================================

    controllers = [
        CookieCollectorController(
            robot=robot,

            task_controller=(
                task_controller
            ),

            environment=(
                environment
            ),

            event_bus=(
                event_bus
            ),

            run_id=(
                run_id
            ),

            planner_seed=(
                1000 + index
            ),
        )

        for index, robot
        in enumerate(
            robots,
            start=1,
        )
    ]

    # ==================================================================
    # 7. Low-latency dashboard state publisher
    #
    # This is different from mission events.
    #
    # Mission events:
    #     persisted and analyzed later.
    #
    # Live state:
    #     ephemeral visualization only.
    #
    # CookieMissionSimulation automatically skips this when headless.
    # ==================================================================

    live_state_publisher = (
        LiveMissionStatePublisher(
            backend_url=(
                "http://localhost:8000"
            ),
            timeout_seconds=0.25,
        )
    )

    # ==================================================================
    # 8. Simulation
    # ==================================================================

    simulation = (
        CookieMissionSimulation(
            arena=environment,

            robots=robots,

            controllers=controllers,

            cookie_generator=(
                cookie_generator
            ),

            task_controller=(
                task_controller
            ),

            live_state_publisher=(
                live_state_publisher
            ),

            live_state_frequency_hz=10.0,

            headless=(
                args.headless
            ),

            duration_seconds=(
                args.duration
            ),
        )
    )

    # ==================================================================
    # 9. Run
    # ==================================================================

    simulation.run()

    print()
    print("=" * 70)

    print(
        "[MISSION FINISHED]"
    )

    print(
        f"  run_id:      {run_id}"
    )

    print(
        f"  robots:      {args.robot_count}"
    )

    print(
        f"  sim_time:    "
        f"{simulation.simulation_elapsed:.1f}s"
    )

    print("=" * 70)
    print()


if __name__ == "__main__":
    main()