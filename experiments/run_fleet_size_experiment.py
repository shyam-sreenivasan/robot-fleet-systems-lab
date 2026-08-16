import argparse
import os
import subprocess
import sys
import time


ROBOT_COUNTS = [
    3,
    7,
    10,
]


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run cookie mission fleet-size "
            "experiments in parallel."
        )
    )

    parser.add_argument(
        "--duration",
        type=float,
        default=120.0,
        help=(
            "Simulation duration in seconds "
            "for each fleet size."
        ),
    )

    parser.add_argument(
        "--with-ui",
        action="store_true",
        help=(
            "Run simulations with Pygame UI. "
            "Default is headless."
        ),
    )

    args = parser.parse_args()

    processes = []

    print()
    print("=" * 60)
    print("FLEET SIZE EXPERIMENT")
    print("=" * 60)

    print(
        f"Robot counts: {ROBOT_COUNTS}"
    )

    print(
        f"Duration:     {args.duration}s"
    )

    print(
        f"Headless:     {not args.with_ui}"
    )

    print("=" * 60)
    print()

    for robot_count in ROBOT_COUNTS:

        command = [
            sys.executable,
            "-m",
            (
                "simulator.missions."
                "cookie_collection.main"
            ),
            "--robot-count",
            str(robot_count),
            "--duration",
            str(args.duration),
        ]

        environment = (
            os.environ.copy()
        )

        if not args.with_ui:

            command.append(
                "--headless"
            )

            # Allows Pygame initialization without
            # a physical display.
            environment[
                "SDL_VIDEODRIVER"
            ] = "dummy"

        print(
            "[LAUNCH] "
            f"{robot_count} robots"
        )

        process = subprocess.Popen(
            command,
            env=environment,
        )

        processes.append(
            (
                robot_count,
                process,
            )
        )

        # Small stagger purely to make console output
        # and generated run IDs easier to distinguish.
        time.sleep(
            0.1
        )

    print()
    print(
        "[EXPERIMENT] "
        "All simulations launched."
    )
    print()

    failures = []

    for (
        robot_count,
        process,
    ) in processes:

        return_code = (
            process.wait()
        )

        if return_code == 0:

            print(
                "[COMPLETE] "
                f"{robot_count} robots"
            )

        else:

            print(
                "[FAILED] "
                f"{robot_count} robots "
                f"exit_code={return_code}"
            )

            failures.append(
                robot_count
            )

    print()
    print("=" * 60)

    if failures:

        print(
            "EXPERIMENT COMPLETED "
            "WITH FAILURES"
        )

        print(
            f"Failed fleet sizes: "
            f"{failures}"
        )

    else:

        print(
            "EXPERIMENT COMPLETE"
        )

        print(
            "All fleet sizes finished."
        )

    print("=" * 60)


if __name__ == "__main__":
    main()