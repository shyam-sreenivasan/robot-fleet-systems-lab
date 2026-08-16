import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, median


def load_events(path: Path):
    events = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            events.append(
                json.loads(line)
            )

    return sorted(
        events,
        key=lambda event: event["timestamp"],
    )


def percentile(
    values,
    percentile_value,
):
    if not values:
        return 0.0

    ordered = sorted(values)

    index = (
        len(ordered) - 1
    ) * percentile_value

    lower = int(index)
    upper = min(
        lower + 1,
        len(ordered) - 1,
    )

    weight = index - lower

    return (
        ordered[lower]
        * (1 - weight)
        + ordered[upper]
        * weight
    )


def analyze(events):
    if not events:
        return None

    first_timestamp = events[0]["timestamp"]
    last_timestamp = events[-1]["timestamp"]

    duration_seconds = (
        last_timestamp
        - first_timestamp
    )

    duration_minutes = (
        duration_seconds / 60.0
    )

    spawned = []
    assigned = []
    collected = []
    plan_started = []
    plan_succeeded = []
    plan_failed = []
    replans = []

    robots_seen = set()

    for event in events:
        event_type = event["event_type"]

        robot_id = event.get(
            "robot_id"
        )

        if robot_id:
            robots_seen.add(
                robot_id
            )

        if event_type == "COOKIE_SPAWNED":
            spawned.append(event)

        elif event_type == "COOKIE_ASSIGNED":
            assigned.append(event)

        elif event_type == "COOKIE_COLLECTED":
            collected.append(event)

        elif event_type == "PLAN_STARTED":
            plan_started.append(event)

        elif event_type == "PLAN_SUCCEEDED":
            plan_succeeded.append(event)

        elif event_type == "PLAN_FAILED":
            plan_failed.append(event)

        elif event_type == "REPLAN_TRIGGERED":
            replans.append(event)

    spawned_at = {}
    assigned_at = {}

    for event in spawned:
        cookie_id = event[
            "metadata"
        ].get(
            "cookie_id"
        )

        if cookie_id:
            spawned_at[cookie_id] = (
                event["timestamp"]
            )

    for event in assigned:
        cookie_id = event[
            "metadata"
        ].get(
            "cookie_id"
        )

        if cookie_id:
            assigned_at[cookie_id] = (
                event["timestamp"]
            )

    mission_times = []
    queue_wait_times = []
    execution_times = []

    collected_by_robot = (
        defaultdict(int)
    )

    for event in collected:
        robot_id = event.get(
            "robot_id"
        )

        if robot_id:
            collected_by_robot[
                robot_id
            ] += 1

        cookie_id = event[
            "metadata"
        ].get(
            "cookie_id"
        )

        if (
            cookie_id
            not in spawned_at
        ):
            continue

        collected_at = (
            event["timestamp"]
        )

        total_time = (
            collected_at
            - spawned_at[cookie_id]
        )

        mission_times.append(
            total_time
        )

        if (
            cookie_id
            in assigned_at
        ):
            queue_wait = (
                assigned_at[cookie_id]
                - spawned_at[cookie_id]
            )

            execution_time = (
                collected_at
                - assigned_at[cookie_id]
            )

            queue_wait_times.append(
                queue_wait
            )

            execution_times.append(
                execution_time
            )

    failures_by_robot = (
        defaultdict(int)
    )

    for event in plan_failed:
        robot_id = event.get(
            "robot_id"
        )

        if robot_id:
            failures_by_robot[
                robot_id
            ] += 1

    replans_by_robot = (
        defaultdict(int)
    )

    for event in replans:
        robot_id = event.get(
            "robot_id"
        )

        if robot_id:
            replans_by_robot[
                robot_id
            ] += 1

    planning_time_by_robot = (
        defaultdict(float)
    )

    for event in (
        plan_succeeded
        + plan_failed
    ):
        robot_id = event.get(
            "robot_id"
        )

        latency_ms = (
            event.get(
                "metadata",
                {}
            ).get(
                "planning_latency_ms",
                0.0,
            )
        )

        if robot_id:
            planning_time_by_robot[
                robot_id
            ] += (
                latency_ms / 1000.0
            )

    idle_time_by_robot = (
        calculate_idle_time(
            assigned_events=assigned,
            collected_events=collected,
            robots=robots_seen,
            run_start=first_timestamp,
            run_end=last_timestamp,
        )
    )

    average_open_cookies = (
        calculate_average_open_cookies(
            events
        )
    )

    robot_count = len(
        robots_seen
    )

    total_collected = len(
        collected
    )

    spawned_per_minute = (
        len(spawned)
        / duration_minutes
        if duration_minutes > 0
        else 0.0
    )

    collected_per_minute = (
        total_collected
        / duration_minutes
        if duration_minutes > 0
        else 0.0
    )

    collected_per_robot_per_minute = (
        collected_per_minute
        / robot_count
        if robot_count > 0
        else 0.0
    )

    replans_per_cookie = (
        len(replans)
        / total_collected
        if total_collected > 0
        else 0.0
    )

    failures_per_cookie = (
        len(plan_failed)
        / total_collected
        if total_collected > 0
        else 0.0
    )

    return {
        "run_id":
            events[0].get(
                "run_id"
            ),

        "duration_seconds":
            duration_seconds,

        "robot_count":
            robot_count,

        "total_spawned":
            len(spawned),

        "total_collected":
            total_collected,

        "spawned_per_minute":
            spawned_per_minute,

        "collected_per_minute":
            collected_per_minute,

        "collected_per_robot_per_minute":
            collected_per_robot_per_minute,

        "average_open_cookies":
            average_open_cookies,

        "mission_time":
            stats(
                mission_times
            ),

        "queue_wait":
            stats(
                queue_wait_times
            ),

        "execution_time":
            stats(
                execution_times
            ),

        "plan_failures":
            len(plan_failed),

        "replans":
            len(replans),

        "failures_per_cookie":
            failures_per_cookie,

        "replans_per_cookie":
            replans_per_cookie,

        "collected_by_robot":
            dict(
                sorted(
                    collected_by_robot.items()
                )
            ),

        "failures_by_robot":
            dict(
                sorted(
                    failures_by_robot.items()
                )
            ),

        "replans_by_robot":
            dict(
                sorted(
                    replans_by_robot.items()
                )
            ),

        "planning_time_by_robot":
            dict(
                sorted(
                    planning_time_by_robot.items()
                )
            ),

        "idle_time_by_robot":
            dict(
                sorted(
                    idle_time_by_robot.items()
                )
            ),
    }


def calculate_idle_time(
    assigned_events,
    collected_events,
    robots,
    run_start,
    run_end,
):
    assignments_by_robot = (
        defaultdict(list)
    )

    collections_by_robot = (
        defaultdict(list)
    )

    for event in assigned_events:
        robot_id = event.get(
            "robot_id"
        )

        if robot_id:
            assignments_by_robot[
                robot_id
            ].append(
                event["timestamp"]
            )

    for event in collected_events:
        robot_id = event.get(
            "robot_id"
        )

        if robot_id:
            collections_by_robot[
                robot_id
            ].append(
                event["timestamp"]
            )

    idle_time_by_robot = {}

    for robot_id in robots:
        assignments = sorted(
            assignments_by_robot[
                robot_id
            ]
        )

        collections = sorted(
            collections_by_robot[
                robot_id
            ]
        )

        idle_seconds = 0.0

        if assignments:
            idle_seconds += max(
                0.0,
                assignments[0]
                - run_start,
            )
        else:
            idle_seconds = (
                run_end
                - run_start
            )

            idle_time_by_robot[
                robot_id
            ] = idle_seconds

            continue

        for collected_at in collections:
            next_assignment = next(
                (
                    timestamp
                    for timestamp
                    in assignments
                    if timestamp
                    > collected_at
                ),
                None,
            )

            if next_assignment is not None:
                idle_seconds += max(
                    0.0,
                    next_assignment
                    - collected_at,
                )

            elif (
                collected_at
                < run_end
            ):
                idle_seconds += (
                    run_end
                    - collected_at
                )

        idle_time_by_robot[
            robot_id
        ] = idle_seconds

    return idle_time_by_robot


def calculate_average_open_cookies(
    events,
):
    lifecycle_events = [
        event
        for event in events
        if event["event_type"]
        in {
            "COOKIE_SPAWNED",
            "COOKIE_COLLECTED",
        }
    ]

    if len(lifecycle_events) < 2:
        return 0.0

    open_count = 0
    weighted_sum = 0.0

    previous_timestamp = (
        lifecycle_events[0][
            "timestamp"
        ]
    )

    for event in lifecycle_events:
        timestamp = event[
            "timestamp"
        ]

        elapsed = (
            timestamp
            - previous_timestamp
        )

        weighted_sum += (
            open_count
            * elapsed
        )

        if (
            event["event_type"]
            == "COOKIE_SPAWNED"
        ):
            open_count += 1

        elif (
            event["event_type"]
            == "COOKIE_COLLECTED"
        ):
            open_count = max(
                0,
                open_count - 1,
            )

        previous_timestamp = (
            timestamp
        )

    total_duration = (
        lifecycle_events[-1][
            "timestamp"
        ]
        - lifecycle_events[0][
            "timestamp"
        ]
    )

    if total_duration <= 0:
        return 0.0

    return (
        weighted_sum
        / total_duration
    )


def stats(values):
    if not values:
        return {
            "average": 0.0,
            "median": 0.0,
            "p95": 0.0,
            "min": 0.0,
            "max": 0.0,
        }

    return {
        "average":
            mean(values),

        "median":
            median(values),

        "p95":
            percentile(
                values,
                0.95,
            ),

        "min":
            min(values),

        "max":
            max(values),
    }


def print_summary(summary):
    print()
    print("=" * 64)
    print("COOKIE MISSION RUN ANALYSIS")
    print("=" * 64)

    print(
        f"Run ID:          "
        f"{summary['run_id']}"
    )

    print(
        f"Duration:        "
        f"{summary['duration_seconds']:.1f}s"
    )

    print(
        f"Robots:          "
        f"{summary['robot_count']}"
    )

    print()

    print("THROUGHPUT")
    print("-" * 64)

    print(
        f"Spawned/min:     "
        f"{summary['spawned_per_minute']:.2f}"
    )

    print(
        f"Collected/min:   "
        f"{summary['collected_per_minute']:.2f}"
    )

    print(
        f"Per robot/min:   "
        f"{summary['collected_per_robot_per_minute']:.2f}"
    )

    print(
        f"Avg open:        "
        f"{summary['average_open_cookies']:.2f}"
    )

    print()

    print("TASK LATENCY")
    print("-" * 64)

    print_stats(
        "Mission",
        summary["mission_time"],
    )

    print_stats(
        "Queue",
        summary["queue_wait"],
    )

    print_stats(
        "Execution",
        summary["execution_time"],
    )

    print()

    print("PLANNER")
    print("-" * 64)

    print(
        f"Plan failures:   "
        f"{summary['plan_failures']}"
    )

    print(
        f"Replans:         "
        f"{summary['replans']}"
    )

    print(
        f"Failures/cookie: "
        f"{summary['failures_per_cookie']:.3f}"
    )

    print(
        f"Replans/cookie:  "
        f"{summary['replans_per_cookie']:.3f}"
    )

    print()

    print("PER ROBOT")
    print("-" * 64)

    robot_ids = sorted(
        set(
            summary[
                "collected_by_robot"
            ]
        )
        | set(
            summary[
                "failures_by_robot"
            ]
        )
        | set(
            summary[
                "replans_by_robot"
            ]
        )
        | set(
            summary[
                "idle_time_by_robot"
            ]
        )
    )

    print(
        f"{'Robot':<12}"
        f"{'Collected':>12}"
        f"{'Failures':>12}"
        f"{'Replans':>12}"
        f"{'Idle %':>10}"
        f"{'Planning %':>12}"
    )

    for robot_id in robot_ids:
        idle_seconds = (
            summary[
                "idle_time_by_robot"
            ].get(
                robot_id,
                0.0,
            )
        )

        planning_seconds = (
            summary[
                "planning_time_by_robot"
            ].get(
                robot_id,
                0.0,
            )
        )

        duration = summary[
            "duration_seconds"
        ]

        idle_percent = (
            idle_seconds
            / duration
            * 100
            if duration > 0
            else 0.0
        )

        planning_percent = (
            planning_seconds
            / duration
            * 100
            if duration > 0
            else 0.0
        )

        print(
            f"{robot_id:<12}"
            f"{summary['collected_by_robot'].get(robot_id, 0):>12}"
            f"{summary['failures_by_robot'].get(robot_id, 0):>12}"
            f"{summary['replans_by_robot'].get(robot_id, 0):>12}"
            f"{idle_percent:>9.1f}%"
            f"{planning_percent:>11.1f}%"
        )

    print("=" * 64)


def print_stats(
    name,
    values,
):
    print(
        f"{name:<12}"
        f"avg={values['average']:.2f}s  "
        f"p50={values['median']:.2f}s  "
        f"p95={values['p95']:.2f}s  "
        f"max={values['max']:.2f}s"
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Analyze one cookie mission "
            "events.jsonl run."
        )
    )

    parser.add_argument(
        "events_file",
        type=Path,
        help="Path to events.jsonl",
    )

    args = parser.parse_args()

    events = load_events(
        args.events_file
    )

    summary = analyze(
        events
    )

    if summary is None:
        print(
            "No events found."
        )

        return

    print_summary(
        summary
    )


if __name__ == "__main__":
    main()