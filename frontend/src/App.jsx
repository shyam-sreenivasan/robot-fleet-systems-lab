import { useEffect, useMemo, useState } from "react";
import axios from "axios";

const API_BASE = "http://localhost:8000";
const WS_URL = "ws://localhost:8000/events";

function App() {
  const [summary, setSummary] = useState({
    robot_count: 0,
    active_count: 0,
    unknown_count: 0,
    active_alert_count: 0,
  });

  const [robots, setRobots] = useState([]);
  const [alerts, setAlerts] = useState([]);

  const [unreadAlerts, setUnreadAlerts] = useState([]);
  const [showAlertModal, setShowAlertModal] = useState(false);

  const refreshDashboard = async () => {
    try {
      const [
        summaryResponse,
        fleetResponse,
        alertsResponse,
      ] = await Promise.all([
        axios.get(`${API_BASE}/summary`),
        axios.get(`${API_BASE}/fleet`),
        axios.get(`${API_BASE}/alerts?active_only=true`),
      ]);

      setSummary(summaryResponse.data);

      setRobots(
        fleetResponse.data.robots ?? []
      );

      setAlerts(
        alertsResponse.data.alerts ?? []
      );
    } catch (error) {
      console.error(
        "Failed to refresh dashboard:",
        error
      );
    }
  };


  useEffect(() => {
    refreshDashboard();

    const refreshInterval = setInterval(
      refreshDashboard,
      2000
    );

    const socket = new WebSocket(
      WS_URL
    );

    socket.onopen = () => {
      console.log(
        "Dashboard WebSocket connected"
      );
    };

    socket.onmessage = (event) => {
      const message = JSON.parse(
        event.data
      );

      console.log(
        "Backend event:",
        message
      );

      if (
        message.type === "ALERT_CREATED"
      ) {
        setUnreadAlerts(
          (current) => [
            ...current,
            message.alert,
          ]
        );

        setShowAlertModal(true);
      }

      refreshDashboard();
    };

    socket.onerror = (error) => {
      console.error(
        "WebSocket error:",
        error
      );
    };

    socket.onclose = () => {
      console.log(
        "Dashboard WebSocket disconnected"
      );
    };

    return () => {
      socket.close();
    };
  }, []);

  const latestUnreadAlert =
    useMemo(() => {
      if (unreadAlerts.length === 0) {
        return null;
      }

      return unreadAlerts[
        unreadAlerts.length - 1
      ];
    }, [unreadAlerts]);

  const formatLastSeen = (
    timestamp
  ) => {
    if (!timestamp) {
      return "-";
    }

    const ageSeconds =
      Date.now() / 1000
      - timestamp;

    if (ageSeconds < 1) {
      return "just now";
    }

    return `${ageSeconds.toFixed(
      1
    )}s ago`;
  };
function FleetMap({ robots, arenaWidth = 100, arenaHeight = 75 }) {
  return (
    <div className="fleet-map">
      {robots.map((robot) => {
        const leftPercent =
          (robot.x / arenaWidth) * 100;

        const bottomPercent =
          (robot.y / arenaHeight) * 100;

        return (
          <div
            key={robot.robot_id}
            className={`map-robot ${
              robot.status === "UNKNOWN"
                ? "map-robot-unknown"
                : ""
            }`}
            style={{
              left: `${leftPercent}%`,
              bottom: `${bottomPercent}%`,
              transform: `translate(-50%, 50%) rotate(${
                -robot.theta
              }rad)`,
            }}
            title={`${robot.robot_id} - ${robot.status}`}
          >
            <div className="robot-body">
              <div className="robot-heading" />
            </div>

            <div className="robot-label">
              {robot.robot_id}
            </div>
          </div>
        );
      })}
    </div>
  );
}
  const closeAlertModal = () => {
    setShowAlertModal(false);
    setUnreadAlerts([]);
  };

  return (
    <div className="dashboard">

      <header className="top-bar">

        <div>
          <h1>
            Robot Fleet Operations
          </h1>

          <p>
            Live fleet telemetry and health monitoring
          </p>
        </div>

        <button
          className="notification-button"
          onClick={() => {
            if (
              unreadAlerts.length > 0
            ) {
              setShowAlertModal(true);
            }
          }}
        >
          🔔

          {unreadAlerts.length > 0 && (
            <span className="notification-badge">
              {unreadAlerts.length}
            </span>
          )}
        </button>

      </header>


      <section className="counter-grid">

        <CounterCard
          label="Total Robots"
          value={summary.robot_count}
        />

        <CounterCard
          label="Active"
          value={summary.active_count}
        />

        <CounterCard
          label="Unknown"
          value={summary.unknown_count}
        />

        <CounterCard
          label="Active Alerts"
          value={summary.active_alert_count}
        />

      </section>
      <div className="fleet-layout">

  <section className="panel map-panel">
    <div className="panel-header">
      <h2>Fleet Map</h2>

      <span>
        Backend-known position
      </span>
    </div>

    <FleetMap
      robots={robots}
      arenaWidth={100}
      arenaHeight={75}
    />
  </section>


  <section className="panel">

    <div className="panel-header">

      <h2>
        Fleet
      </h2>

      <span>
        {robots.length} robots
      </span>

    </div>


    <div className="table-wrapper">

      <table>

        <thead>
          <tr>
            <th>Robot</th>
            <th>Status</th>
            <th>X</th>
            <th>Y</th>
            <th>Heading</th>
            <th>Last Active</th>
          </tr>
        </thead>

        <tbody>

          {robots.map(
            (robot) => (
              <tr key={robot.robot_id}>

                <td>
                  {robot.robot_id}
                </td>

                <td>
                  <StatusBadge
                    status={robot.status}
                  />
                </td>

                <td>
                  {robot.x.toFixed(2)}
                </td>

                <td>
                  {robot.y.toFixed(2)}
                </td>

                <td>
                  {(
                    robot.theta
                    * 180
                    / Math.PI
                  ).toFixed(0)}
                  °
                </td>

                <td>
                  {formatLastSeen(
                    robot.last_seen
                  )}
                </td>

              </tr>
            )
          )}

        </tbody>

      </table>

    </div>

  </section>

</div>


      {showAlertModal &&
        latestUnreadAlert && (

          <div className="modal-backdrop">

            <div className="modal">

              <div className="modal-header">

                <h2>
                  Fleet Alert
                </h2>

                <button
                  onClick={
                    closeAlertModal
                  }
                >
                  ✕
                </button>

              </div>


              <div className="alert-title">
                Telemetry Lost
              </div>


              <div className="alert-detail">

                <strong>
                  Robot
                </strong>

                <span>
                  {
                    latestUnreadAlert.robot_id
                  }
                </span>

              </div>


              <div className="alert-detail">

                <strong>
                  Status
                </strong>

                <span>
                  UNKNOWN
                </span>

              </div>


              <div className="alert-detail">

                <strong>
                  Last active
                </strong>

                <span>
                  {formatLastSeen(
                    latestUnreadAlert.last_seen_at
                  )}
                </span>

              </div>


              <p className="alert-message">
                No telemetry has been received
                from this robot within the
                configured health timeout.
              </p>


              <button
                className="acknowledge-button"
                onClick={
                  closeAlertModal
                }
              >
                Mark as read
              </button>

            </div>

          </div>

        )}

    </div>
  );
}


function CounterCard({
  label,
  value,
}) {
  return (
    <div className="counter-card">

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

    </div>
  );
}


function StatusBadge({
  status,
}) {
  return (
    <span
      className={
        status === "ACTIVE"
          ? "status active"
          : "status unknown"
      }
    >
      {status}
    </span>
  );
}


export default App;