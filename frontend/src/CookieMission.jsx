import {
  useEffect,
  useState,
} from "react";

import axios from "axios";


const BACKEND_URL =
  "http://localhost:8000";

const WS_URL =
  "ws://localhost:8000/events";


function MetricCard({
  label,
  value,
  unit = "",
}) {
  return (
    <div className="metric-card">

      <div className="metric-label">
        {label}
      </div>

      <div className="metric-value">
        {value}

        {unit && (
          <span className="metric-unit">
            {unit}
          </span>
        )}
      </div>

    </div>
  );
}


function formatNumber(
  value,
  digits = 1,
) {
  if (
    value === null
    || value === undefined
  ) {
    return "—";
  }

  return Number(
    value
  ).toFixed(
    digits
  );
}


function LiveMissionMap({
  robots,
  cookies,
  arenaWidth = 100,
  arenaHeight = 75,
}) {
  return (
    <div className="cookie-live-map">

      {/* Cookies */}

      {cookies.map(
        (cookie) => {
          const left =
            (
              cookie.x
              / arenaWidth
            ) * 100;

          const bottom =
            (
              cookie.y
              / arenaHeight
            ) * 100;

          return (
            <div
              key={
                cookie.cookie_id
              }
              className={
                cookie.assigned_robot_id
                  ? "live-cookie assigned"
                  : "live-cookie"
              }
              style={{
                left:
                  `${left}%`,

                bottom:
                  `${bottom}%`,
              }}
              title={
                cookie.assigned_robot_id
                  ? `${cookie.cookie_id} → ${cookie.assigned_robot_id}`
                  : cookie.cookie_id
              }
            />
          );
        }
      )}


      {/* Robots */}

      {robots.map(
        (robot) => {
          const left =
            (
              robot.x
              / arenaWidth
            ) * 100;

          const bottom =
            (
              robot.y
              / arenaHeight
            ) * 100;

          return (
            <div
              key={
                robot.robot_id
              }
              className="live-robot"
              style={{
                left:
                  `${left}%`,

                bottom:
                  `${bottom}%`,

                transform:
                  `translate(-50%, 50%) rotate(${
                    -robot.theta
                  }rad)`,
              }}
              title={
                robot.robot_id
              }
            >

              <div className="live-robot-body">

                <div className="live-robot-heading" />

              </div>

              <div className="live-robot-label">
                {
                  robot.robot_id
                }
              </div>

            </div>
          );
        }
      )}

    </div>
  );
}


function CookieMission() {
  const [
    summary,
    setSummary,
  ] = useState(null);

  const [
    liveRobots,
    setLiveRobots,
  ] = useState([]);

  const [
    liveCookies,
    setLiveCookies,
  ] = useState([]);

  const [
    liveConnected,
    setLiveConnected,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState(null);


  // ==============================================================
  // Aggregated metrics
  //
  // Lower-frequency polling.
  // ==============================================================

  useEffect(() => {
    let active = true;

    async function loadSummary() {
      try {
        const response =
          await axios.get(
            `${BACKEND_URL}/mission-summary`
          );

        if (active) {
          setSummary(
            response.data
          );

          setError(null);
        }

      } catch (err) {
        console.error(
          "Failed to load cookie mission summary:",
          err
        );

        if (active) {
          setError(
            "Unable to load mission metrics."
          );
        }
      }
    }

    loadSummary();

    const interval =
      setInterval(
        loadSummary,
        2000,
      );

    return () => {
      active = false;

      clearInterval(
        interval
      );
    };

  }, []);


  // ==============================================================
  // Low-latency mission state
  //
  // High-frequency WebSocket stream.
  // ==============================================================

  useEffect(() => {

    const socket =
      new WebSocket(
        WS_URL
      );

    socket.onopen = () => {
      setLiveConnected(
        true
      );
    };

    socket.onmessage = (
        event
        ) => {
        const message =
            JSON.parse(
            event.data
            );

        if (
            message.type ===
            "MISSION_RESET"
        ) {
            setLiveRobots([]);
            setLiveCookies([]);

            return;
        }

        if (
            message.type !==
            "MISSION_STATE_SNAPSHOT"
        ) {
            return;
        }

        if (
            message.mission_id !==
            "cookie_collection"
        ) {
            return;
        }

        setLiveRobots(
            message.robots ?? []
        );

        setLiveCookies(
            message.cookies ?? []
        );
    };

    socket.onerror = (
      error
    ) => {
      console.error(
        "Cookie mission WebSocket error:",
        error
      );
    };

    socket.onclose = () => {
      setLiveConnected(
        false
      );
    };

    return () => {
      socket.close();
    };

  }, []);


  if (
    error
    && !summary
  ) {
    return (
      <div className="cookie-page">

        <h1>
          Cookie Mission
        </h1>

        <div className="error-message">
          {error}
        </div>

      </div>
    );
  }


  if (!summary) {
    return (
      <div className="cookie-page">

        <h1>
          Cookie Mission
        </h1>

        <div>
          Loading mission metrics...
        </div>

      </div>
    );
  }


  // ==============================================================
  // Timing metrics
  // ==============================================================

  const missionTime =
    summary.mission_time
    || {};

  const totalTime =
    missionTime.total
    || {};

  const queueWait =
    missionTime.queue_wait
    || {};

  const execution =
    missionTime.execution
    || {};


  // ==============================================================
  // Per-robot metrics
  // ==============================================================

  const cookiesCollected =
    summary.cookies_collected
    || {};

  const collectedByRobot =
    cookiesCollected.by_robot
    || {};

  const failures =
    summary.planning_failures
    || {};

  const failureByRobot =
    failures.by_robot
    || {};

  const replans =
    summary.replans
    || {};

  const replanByRobot =
    replans.by_robot
    || {};


  const robotIds =
    Array.from(
      new Set([
        ...liveRobots.map(
          (robot) =>
            robot.robot_id
        ),

        ...Object.keys(
          collectedByRobot
        ),

        ...Object.keys(
          failureByRobot
        ),

        ...Object.keys(
          replanByRobot
        ),
      ])
    ).sort(
      (a, b) => {
        const aNumber =
          Number(
            a.split("_")[1]
          );

        const bNumber =
          Number(
            b.split("_")[1]
          );

        return (
          aNumber
          - bNumber
        );
      }
    );


  return (
    <div className="cookie-page">

      {/* ========================================================
          Header
      ======================================================== */}

      <div className="cookie-header">

        <div>

          <h1>
            Cookie Mission
          </h1>

          <p>
            Live mission performance,
            planner behavior and fleet state.
          </p>

        </div>

        <div className="cookie-header-status">

          <div className="mission-runtime">
            Runtime:{" "}
            {formatNumber(
              summary.duration_seconds,
              0,
            )}
            s
          </div>

          <div
            className={
              liveConnected
                ? "live-status connected"
                : "live-status disconnected"
            }
          >
            <span className="live-dot" />

            {liveConnected
              ? "Live"
              : "Disconnected"}
          </div>

        </div>

      </div>


      {/* ========================================================
          Metrics + live mission
      ======================================================== */}

      <div className="cookie-overview-layout">

        {/* LEFT — aggregated metrics */}

        <section className="cookie-overview-panel">

          <div className="section-header">
            <h2>
              Mission Metrics
            </h2>

            <span>
              Aggregated every 2s
            </span>
          </div>

          <div className="metric-grid">

            <MetricCard
              label="Spawned / min"
              value={
                formatNumber(
                  summary.spawned_per_minute
                )
              }
            />

            <MetricCard
              label="Collected / min"
              value={
                formatNumber(
                  summary.collected_per_minute
                )
              }
            />

            <MetricCard
              label="Avg open cookies"
              value={
                formatNumber(
                  summary.average_open_cookies
                )
              }
            />

            <MetricCard
              label="Avg mission time"
              value={
                formatNumber(
                  totalTime.average_seconds
                )
              }
              unit="s"
            />

            <MetricCard
              label="Avg queue wait"
              value={
                formatNumber(
                  queueWait.average_seconds
                )
              }
              unit="s"
            />

            <MetricCard
              label="Avg execution"
              value={
                formatNumber(
                  execution.average_seconds
                )
              }
              unit="s"
            />

            <MetricCard
              label="Plan failures"
              value={
                failures.total
                ?? 0
              }
            />

            <MetricCard
              label="Replans"
              value={
                replans.total
                ?? 0
              }
            />

          </div>

        </section>


        {/* RIGHT — low-latency simulator state */}

        <section className="cookie-overview-panel">

          <div className="section-header">

            <h2>
              Live Mission State
            </h2>

            <span>
              ~10 Hz edge state
            </span>

          </div>

          <LiveMissionMap
            robots={
              liveRobots
            }
            cookies={
              liveCookies
            }
            arenaWidth={100}
            arenaHeight={75}
          />

          <div className="live-map-legend">

            <span>
              <i className="legend-robot" />
              Robot
            </span>

            <span>
              <i className="legend-cookie" />
              Cookie
            </span>

            <span>
              <i className="legend-cookie assigned" />
              Assigned cookie
            </span>

          </div>

        </section>

      </div>


      {/* ========================================================
          Mission State
      ======================================================== */}

      <div className="mission-section">

        <div className="section-header">
          <h2>
            Mission State
          </h2>
        </div>

        <div className="mission-state-row">

          <div>

            <span>
              Spawned
            </span>

            <strong>
              {
                summary.total_spawned
              }
            </strong>

          </div>


          <div>

            <span>
              Collected
            </span>

            <strong>
              {
                summary.total_collected
              }
            </strong>

          </div>


          <div>

            <span>
              Currently open
            </span>

            <strong>
              {
                summary.currently_open
              }
            </strong>

          </div>

        </div>

      </div>


      {/* ========================================================
          Per Robot
      ======================================================== */}

      <div className="mission-section">

        <div className="section-header">

          <h2>
            Per Robot
          </h2>

        </div>


        <table className="robot-metrics-table">

          <thead>

            <tr>

              <th>
                Robot
              </th>

              <th>
                Cookies collected
              </th>

              <th>
                Plan failures
              </th>

              <th>
                Replans
              </th>

            </tr>

          </thead>


          <tbody>

            {robotIds.length === 0 ? (

              <tr>

                <td
                  colSpan="4"
                  className="empty-cell"
                >
                  No robot mission events yet.
                </td>

              </tr>

            ) : (

              robotIds.map(
                (robotId) => (

                  <tr key={robotId}>

                    <td>
                      {robotId}
                    </td>

                    <td>
                      {
                        collectedByRobot[
                          robotId
                        ] ?? 0
                      }
                    </td>

                    <td>
                      {
                        failureByRobot[
                          robotId
                        ] ?? 0
                      }
                    </td>

                    <td>
                      {
                        replanByRobot[
                          robotId
                        ] ?? 0
                      }
                    </td>

                  </tr>

                )
              )

            )}

          </tbody>

        </table>

      </div>


      {/* ========================================================
          Timing extremes
      ======================================================== */}

      <div className="mission-section">

        <div className="section-header">

          <h2>
            Timing Extremes
          </h2>

        </div>


        <div className="timing-grid">

          <div className="timing-card">

            <span>
              Fastest mission
            </span>

            <strong>
              {
                formatNumber(
                  totalTime.min_seconds
                )
              }
              s
            </strong>

            <small>
              {
                totalTime.fastest
                  ?.cookie_id
                || "—"
              }
            </small>

          </div>


          <div className="timing-card">

            <span>
              Slowest mission
            </span>

            <strong>
              {
                formatNumber(
                  totalTime.max_seconds
                )
              }
              s
            </strong>

            <small>
              {
                totalTime.slowest
                  ?.cookie_id
                || "—"
              }
            </small>

          </div>


          <div className="timing-card">

            <span>
              Longest queue wait
            </span>

            <strong>
              {
                formatNumber(
                  queueWait.max_seconds
                )
              }
              s
            </strong>

            <small>
              {
                queueWait.slowest
                  ?.cookie_id
                || "—"
              }
            </small>

          </div>


          <div className="timing-card">

            <span>
              Longest execution
            </span>

            <strong>
              {
                formatNumber(
                  execution.max_seconds
                )
              }
              s
            </strong>

            <small>
              {
                execution.slowest
                  ?.cookie_id
                || "—"
              }
            </small>

          </div>

        </div>

      </div>

    </div>
  );
}


export default CookieMission;