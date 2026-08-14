import argparse
import sys

import requests


CONTROL_URL = (
    "http://localhost:9000/commands"
)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Simulate telemetry/network loss "
            "for a robot."
        )
    )

    parser.add_argument(
        "--robot",
        required=True,
        help=(
            "Robot ID or robot number "
            "(example: robot_4 or 4)"
        ),
    )

    parser.add_argument(
        "--duration",
        type=float,
        default=20.0,
        help=(
            "Failure duration in seconds "
            "(default: 20)"
        ),
    )

    args = parser.parse_args()

    robot_id = args.robot

    # Convenience:
    #
    # --robot 4
    #
    # becomes:
    #
    # robot_4
    #
    if robot_id.isdigit():
        robot_id = (
            f"robot_{robot_id}"
        )

    command = {
        "target": "telemetry",
        "action": "disconnect",
        "robot_id": robot_id,
        "duration_seconds":
            args.duration,
    }

    print()
    print(
        "Network Failure Experiment"
    )
    print(
        "--------------------------"
    )
    print(
        f"Robot:    {robot_id}"
    )
    print(
        f"Duration: {args.duration:.1f}s"
    )
    print()

    try:
        response = requests.post(
            CONTROL_URL,
            json=command,
            timeout=2,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        print(
            "Experiment command failed:"
        )
        print(exc)

        sys.exit(1)

    print(
        "Command accepted."
    )


if __name__ == "__main__":
    main()