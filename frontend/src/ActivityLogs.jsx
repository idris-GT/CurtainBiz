import { useEffect, useMemo, useState } from "react";
import "./ActivityLogs.css";
import api from "./api/client";

function getArray(response) {
  if (Array.isArray(response.data)) return response.data;
  if (Array.isArray(response.data?.data)) return response.data.data;
  if (Array.isArray(response.data?.items)) return response.data.items;
  return [];
}

function formatAction(action) {
  return String(action || "—")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function ActivityLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [selectedLog, setSelectedLog] = useState(null);

  const loadLogs = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get("/activity-logs/");
      const data = getArray(response);

      setLogs(data);
    } catch (err) {
      console.error("Activity Logs API error:", err);

      setError(
        "Unable to load activity logs. Please check that the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, []);

  const filteredLogs = useMemo(() => {
    const term = search.trim().toLowerCase();

    if (!term) return logs;

    return logs.filter((log) => {
      return (
        String(log.id || "")
          .toLowerCase()
          .includes(term) ||
        String(log.user_id || "")
          .toLowerCase()
          .includes(term) ||
        String(log.action || "")
          .toLowerCase()
          .includes(term) ||
        String(log.entity_type || "")
          .toLowerCase()
          .includes(term) ||
        String(log.entity_id || "")
          .toLowerCase()
          .includes(term) ||
        String(log.description || "")
          .toLowerCase()
          .includes(term)
      );
    });
  }, [logs, search]);

  const stats = useMemo(() => {
    const creates = logs.filter(
      (log) =>
        String(log.action || "").toUpperCase() === "CREATE"
    ).length;

    const updates = logs.filter((log) =>
      String(log.action || "")
        .toUpperCase()
        .includes("UPDATE")
    ).length;

    const productionActions = logs.filter(
      (log) =>
        String(log.entity_type || "").toUpperCase() ===
        "PRODUCTION"
    ).length;

    return {
      total: logs.length,
      creates,
      updates,
      productionActions,
    };
  }, [logs]);

  return (
    <section className="activity-page">
      {/* HEADER */}
      <div className="page-heading">
        <div>
          <p className="eyebrow">SYSTEM AUDIT</p>

          <h3>Activity Logs</h3>

          <p>
            Track important actions performed across the
            business platform.
          </p>
        </div>

        <button
          className="primary-button"
          onClick={loadLogs}
          disabled={loading}
        >
          {loading ? "Refreshing..." : "↻ Refresh"}
        </button>
      </div>

      {/* ERROR */}
      {error && (
        <div className="activity-error">
          <div>
            <strong>Connection problem</strong>
            <span>{error}</span>
          </div>

          <button onClick={loadLogs}>Retry</button>
        </div>
      )}

      {/* STATS */}
      <div className="stats-grid activity-stats">
        <div className="stat-card">
          <div className="stat-top">
            <div className="stat-icon">▤</div>
            <span className="live-badge">Live</span>
          </div>

          <p>Total Activities</p>
          <h4>{loading ? "..." : stats.total}</h4>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <div className="stat-icon">＋</div>
            <span className="live-badge">Live</span>
          </div>

          <p>Creates</p>
          <h4>{loading ? "..." : stats.creates}</h4>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <div className="stat-icon">↻</div>
            <span className="live-badge">Live</span>
          </div>

          <p>Updates</p>
          <h4>{loading ? "..." : stats.updates}</h4>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <div className="stat-icon">⚙</div>
            <span className="live-badge">Live</span>
          </div>

          <p>Production Activity</p>
          <h4>
            {loading ? "..." : stats.productionActions}
          </h4>
        </div>
      </div>

      {/* MAIN PANEL */}
      <div className="panel activity-panel">
        <div className="panel-header">
          <div>
            <h3>System Activity</h3>

            <p>
              Real activity records from the database
            </p>
          </div>

          <div className="activity-count">
            {filteredLogs.length} record
            {filteredLogs.length !== 1 ? "s" : ""}
          </div>
        </div>

        {/* SEARCH */}
        <div className="activity-toolbar">
          <div className="activity-search">
            <span>⌕</span>

            <input
              type="text"
              placeholder="Search actions, users, entities, descriptions..."
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
            />
          </div>

          {search && (
            <button
              className="clear-search"
              onClick={() => setSearch("")}
            >
              Clear
            </button>
          )}
        </div>

        {/* TABLE */}
        <div className="table-wrapper">
          <table className="activity-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>ACTION</th>
                <th>ENTITY</th>
                <th>ENTITY ID</th>
                <th>USER ID</th>
                <th>DESCRIPTION</th>
                <th>CREATED AT</th>
                <th>ACTION</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td
                    colSpan="8"
                    className="table-message"
                  >
                    Loading activity logs...
                  </td>
                </tr>
              ) : filteredLogs.length === 0 ? (
                <tr>
                  <td
                    colSpan="8"
                    className="table-message"
                  >
                    {search
                      ? "No activity logs match your search."
                      : "No activity logs found."}
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log) => (
                  <tr key={log.id}>
                    <td>
                      <strong>#{log.id}</strong>
                    </td>

                    <td>
                      <span
                        className={`activity-action ${String(
                          log.action || ""
                        )
                          .toLowerCase()
                          .replaceAll("_", "-")}`}
                      >
                        {formatAction(log.action)}
                      </span>
                    </td>

                    <td>
                      <span className="entity-badge">
                        {log.entity_type || "—"}
                      </span>
                    </td>

                    <td>
                      {log.entity_id ?? "—"}
                    </td>

                    <td>
                      <span className="user-id">
                        {log.user_id || "—"}
                      </span>
                    </td>

                    <td className="description-cell">
                      {log.description || "—"}
                    </td>

                    <td>
                      {formatDate(log.created_at)}
                    </td>

                    <td>
                      <button
                        className="view-button"
                        onClick={() =>
                          setSelectedLog(log)
                        }
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* DETAILS MODAL */}
      {selectedLog && (
        <div
          className="modal-overlay"
          onClick={() => setSelectedLog(null)}
        >
          <div
            className="modal activity-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >
            <div className="modal-header">
              <div>
                <p className="eyebrow">
                  ACTIVITY DETAILS
                </p>

                <h3>
                  Activity #{selectedLog.id}
                </h3>
              </div>

              <button
                className="modal-close"
                onClick={() =>
                  setSelectedLog(null)
                }
              >
                ×
              </button>
            </div>

            <div className="activity-details">
              <div className="detail-item">
                <span>ID</span>
                <strong>
                  #{selectedLog.id}
                </strong>
              </div>

              <div className="detail-item">
                <span>Action</span>
                <strong>
                  {formatAction(
                    selectedLog.action
                  )}
                </strong>
              </div>

              <div className="detail-item">
                <span>Entity Type</span>
                <strong>
                  {selectedLog.entity_type ||
                    "—"}
                </strong>
              </div>

              <div className="detail-item">
                <span>Entity ID</span>
                <strong>
                  {selectedLog.entity_id ??
                    "—"}
                </strong>
              </div>

              <div className="detail-item full">
                <span>User ID</span>
                <strong className="break-value">
                  {selectedLog.user_id || "—"}
                </strong>
              </div>

              <div className="detail-item full">
                <span>Description</span>
                <strong>
                  {selectedLog.description ||
                    "—"}
                </strong>
              </div>

              <div className="detail-item full">
                <span>Created At</span>
                <strong>
                  {formatDate(
                    selectedLog.created_at
                  )}
                </strong>
              </div>
            </div>

            <div className="modal-footer">
              <button
                className="secondary-button"
                onClick={() =>
                  setSelectedLog(null)
                }
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

export default ActivityLogs;