from collections import defaultdict


class CookieMissionMetricsService:
    """
    Derives cookie mission metrics from atomic mission events.

    Raw events remain the source of truth.
    """

    def __init__(
        self,
        event_repository,
    ):
        self.event_repository = (
            event_repository
        )

    def summary(self):
        events = (
            self.event_repository.get_all(
                mission_id="cookie_collection"
            )
        )

        if not events:
            return self._empty_summary()

        events = sorted(
            events,
            key=lambda event: event.timestamp,
        )

        first_timestamp = (
            events[0].timestamp
        )

        last_timestamp = (
            events[-1].timestamp
        )

        duration_seconds = max(
            last_timestamp - first_timestamp,
            0.0,
        )

        spawned_events = [
            event
            for event in events
            if event.event_type
            == "COOKIE_SPAWNED"
        ]

        collected_events = [
            event
            for event in events
            if event.event_type
            == "COOKIE_COLLECTED"
        ]

        failed_plan_events = [
            event
            for event in events
            if event.event_type
            == "PLAN_FAILED"
        ]

        replan_events = [
            event
            for event in events
            if event.event_type
            == "REPLAN_TRIGGERED"
        ]

        assigned_events = [
            event
            for event in events
            if event.event_type
            == "COOKIE_ASSIGNED"
        ]


        mission_times = (
            self._calculate_mission_times(
                spawned_events,
                assigned_events,
                collected_events,
            )
        )

        planning_failures_by_robot = (
            self._count_by_robot(
                failed_plan_events
            )
        )

        replans_by_robot = (
            self._count_by_robot(
                replan_events
            )
        )

        avg_open_cookies = (
            self._calculate_average_open_cookies(
                events
            )
        )

        cookies_collected_by_robot = (
            self._count_by_robot(
                collected_events
            )
        )

        duration_minutes = (
            duration_seconds / 60.0
        )

        if duration_minutes > 0:
            spawned_per_minute = (
                len(spawned_events)
                / duration_minutes
            )

            collected_per_minute = (
                len(collected_events)
                / duration_minutes
            )

        else:
            spawned_per_minute = 0.0
            collected_per_minute = 0.0

        return {
            "mission_id":
                "cookie_collection",

            "duration_seconds":
                duration_seconds,

            "total_spawned":
                len(spawned_events),

            "total_collected":
                len(collected_events),

            "currently_open":
                len(spawned_events)
                - len(collected_events),

            "spawned_per_minute":
                spawned_per_minute,

            "collected_per_minute":
                collected_per_minute,

            "average_open_cookies":
                avg_open_cookies,

            "mission_time": (
                self._mission_time_summary(
                    mission_times
                )
            ),

            "planning_failures": {
                "total":
                    len(
                        failed_plan_events
                    ),

                "by_robot":
                    planning_failures_by_robot,
            },

            "replans": {
                "total":
                    len(
                        replan_events
                    ),

                "by_robot":
                    replans_by_robot,
            },

            "cookies_collected": {
                "total":
                    len(collected_events),

                "by_robot":
                    cookies_collected_by_robot,
            },
        }

    def _calculate_mission_times(
        self,
        spawned_events,
        collected_events,
    ):
        """
        Cookie mission time:

            collected_at - spawned_at

        This includes both:
        - time waiting for assignment
        - robot execution/navigation time
        """

        spawned_at = {}

        for event in spawned_events:
            cookie_id = (
                event.metadata.get(
                    "cookie_id"
                )
            )

            if cookie_id is not None:
                spawned_at[
                    cookie_id
                ] = event.timestamp

        mission_times = []

        for event in collected_events:
            cookie_id = (
                event.metadata.get(
                    "cookie_id"
                )
            )

            if (
                cookie_id
                not in spawned_at
            ):
                continue

            mission_time = (
                event.timestamp
                - spawned_at[cookie_id]
            )

            mission_times.append(
                {
                    "cookie_id":
                        cookie_id,

                    "robot_id":
                        event.robot_id,

                    "seconds":
                        mission_time,
                }
            )

        return mission_times

    def _mission_time_summary(
        self,
        mission_times,
    ):
        if not mission_times:
            return {
                "total": self._empty_time_stats(),
                "queue_wait": self._empty_time_stats(),
                "execution": self._empty_time_stats(),
            }

        total_values = [
            {
                "cookie_id":
                    item["cookie_id"],
                "robot_id":
                    item["robot_id"],
                "seconds":
                    item["total_seconds"],
            }
            for item in mission_times
        ]

        queue_wait_values = [
            {
                "cookie_id":
                    item["cookie_id"],
                "robot_id":
                    item["robot_id"],
                "seconds":
                    item["queue_wait_seconds"],
            }
            for item in mission_times
            if item["queue_wait_seconds"]
            is not None
        ]

        execution_values = [
            {
                "cookie_id":
                    item["cookie_id"],
                "robot_id":
                    item["robot_id"],
                "seconds":
                    item["execution_seconds"],
            }
            for item in mission_times
            if item["execution_seconds"]
            is not None
        ]

        return {
            "total":
                self._time_stats(
                    total_values
                ),

            "queue_wait":
                self._time_stats(
                    queue_wait_values
                ),

            "execution":
                self._time_stats(
                    execution_values
                ),
        }

    def _count_by_robot(
        self,
        events,
    ):
        counts = defaultdict(int)

        for event in events:
            if event.robot_id is None:
                continue

            counts[
                event.robot_id
            ] += 1

        return dict(
            sorted(
                counts.items()
            )
        )

    def _calculate_mission_times(
        self,
        spawned_events,
        assigned_events,
        collected_events,
    ):
        spawned_at = {}
        assigned_at = {}

        for event in spawned_events:
            cookie_id = event.metadata.get(
                "cookie_id"
            )

            if cookie_id is not None:
                spawned_at[cookie_id] = (
                    event.timestamp
                )

        for event in assigned_events:
            cookie_id = event.metadata.get(
                "cookie_id"
            )

            if cookie_id is not None:
                assigned_at[cookie_id] = (
                    event.timestamp
                )

        mission_times = []

        for event in collected_events:
            cookie_id = event.metadata.get(
                "cookie_id"
            )

            if cookie_id not in spawned_at:
                continue

            spawned_timestamp = (
                spawned_at[cookie_id]
            )

            collected_timestamp = (
                event.timestamp
            )

            assigned_timestamp = (
                assigned_at.get(cookie_id)
            )

            total_seconds = (
                collected_timestamp
                - spawned_timestamp
            )

            queue_wait_seconds = None
            execution_seconds = None

            if assigned_timestamp is not None:
                queue_wait_seconds = (
                    assigned_timestamp
                    - spawned_timestamp
                )

                execution_seconds = (
                    collected_timestamp
                    - assigned_timestamp
                )

            mission_times.append(
                {
                    "cookie_id":
                        cookie_id,

                    "robot_id":
                        event.robot_id,

                    "total_seconds":
                        total_seconds,

                    "queue_wait_seconds":
                        queue_wait_seconds,

                    "execution_seconds":
                        execution_seconds,
                }
            )

        return mission_times

    def _empty_summary(self):
        return {
            "mission_id":
                "cookie_collection",

            "duration_seconds":
                0.0,

            "total_spawned":
                0,

            "total_collected":
                0,

            "currently_open":
                0,

            "spawned_per_minute":
                0.0,

            "collected_per_minute":
                0.0,

            "average_open_cookies":
                0.0,

            "mission_time": {
                "total":
                    self._empty_time_stats(),

                "queue_wait":
                    self._empty_time_stats(),

                "execution":
                    self._empty_time_stats(),
            },

            "planning_failures": {
                "total": 0,
                "by_robot": {},
            },

            "replans": {
                "total": 0,
                "by_robot": {},
            },
            "cookies_collected": {
                "total": 0,
                "by_robot": {},
            },
        }

    def _time_stats(
        self,
        values,
    ):
        if not values:
            return self._empty_time_stats()

        ordered = sorted(
            values,
            key=lambda item: item["seconds"],
        )

        total_seconds = sum(
            item["seconds"]
            for item in values
        )

        return {
            "average_seconds":
                total_seconds
                / len(values),

            "min_seconds":
                ordered[0]["seconds"],

            "max_seconds":
                ordered[-1]["seconds"],

            "fastest":
                ordered[0],

            "slowest":
                ordered[-1],
        }


    def _empty_time_stats(
        self,
    ):
        return {
            "average_seconds": 0.0,
            "min_seconds": 0.0,
            "max_seconds": 0.0,
            "fastest": None,
            "slowest": None,
        }

    def _calculate_average_open_cookies(
        self,
        events,
    ):
        """
        Time-weighted average number of cookies
        that have spawned but not yet been collected.
        """

        lifecycle_events = [
            event
            for event in events
            if event.event_type
            in {
                "COOKIE_SPAWNED",
                "COOKIE_COLLECTED",
            }
        ]

        if len(lifecycle_events) < 2:
            return 0.0

        lifecycle_events = sorted(
            lifecycle_events,
            key=lambda event: event.timestamp,
        )

        open_count = 0
        weighted_sum = 0.0

        previous_timestamp = (
            lifecycle_events[0].timestamp
        )

        for event in lifecycle_events:
            elapsed = (
                event.timestamp
                - previous_timestamp
            )

            weighted_sum += (
                open_count
                * elapsed
            )

            if (
                event.event_type
                == "COOKIE_SPAWNED"
            ):
                open_count += 1

            elif (
                event.event_type
                == "COOKIE_COLLECTED"
            ):
                open_count = max(
                    0,
                    open_count - 1,
                )

            previous_timestamp = (
                event.timestamp
            )

        total_duration = (
            lifecycle_events[-1].timestamp
            - lifecycle_events[0].timestamp
        )

        if total_duration <= 0:
            return 0.0

        return (
            weighted_sum
            / total_duration
        )