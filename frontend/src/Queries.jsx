import React, { useEffect, useMemo, useState } from "react";
import api from "./api/client";
import "./Queries.css";

function Queries() {
  const [queries, setQueries] = useState([]);
  const [search, setSearch] = useState("");
  const [selectedQuery, setSelectedQuery] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchQueries = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get("/queries/");
      setQueries(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      console.error("Failed to load queries:", err);
      setError(
        err.response?.data?.detail ||
          "Failed to load queries. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueries();
  }, []);

  const filteredQueries = useMemo(() => {
    const term = search.trim().toLowerCase();

    if (!term) return queries;

    return queries.filter((query) =>
      [
        query.id,
        query.order_number,
        query.department,
        query.subject,
        query.description,
        query.priority,
        query.status,
      ]
        .filter((value) => value !== null && value !== undefined)
        .some((value) => String(value).toLowerCase().includes(term))
    );
  }, [queries, search]);

  const openQuery = async (query) => {
    try {
      const response = await api.get(`/queries/${query.id}`);
      setSelectedQuery(response.data);
    } catch (err) {
      console.error("Failed to load query details:", err);

      // If detail endpoint fails, still show the row data.
      setSelectedQuery(query);
    }
  };

  const closeModal = () => {
    setSelectedQuery(null);
  };

  const formatDate = (date) => {
    if (!date) return "-";

    const parsed = new Date(date);

    if (Number.isNaN(parsed.getTime())) return date;

    return parsed.toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  };

  const getPriorityClass = (priority) => {
    if (!priority) return "query-priority";

    return `query-priority ${String(priority).toLowerCase()}`;
  };

  const getStatusClass = (status) => {
    if (!status) return "query-status";

    return `query-status ${String(status).toLowerCase()}`;
  };

  const openCount = queries.filter(
    (query) => String(query.status).toUpperCase() === "OPEN"
  ).length;

  const highPriorityCount = queries.filter(
    (query) => String(query.priority).toUpperCase() === "HIGH"
  ).length;

  const resolvedCount = queries.filter((query) =>
    ["RESOLVED", "CLOSED", "COMPLETED"].includes(
      String(query.status).toUpperCase()
    )
  ).length;

  return (
    <div className="queries-page">
      <div className="queries-header">
        <div>
          <h1>Queries</h1>
          <p>Monitor customer and internal queries.</p>
        </div>
      </div>

      <div className="queries-summary">
        <div className="query-summary-card">
          <span>Total Queries</span>
          <strong>{queries.length}</strong>
        </div>

        <div className="query-summary-card">
          <span>Open</span>
          <strong>{openCount}</strong>
        </div>

        <div className="query-summary-card">
          <span>High Priority</span>
          <strong>{highPriorityCount}</strong>
        </div>

        <div className="query-summary-card">
          <span>Resolved</span>
          <strong>{resolvedCount}</strong>
        </div>
      </div>

      <div className="queries-toolbar">
        <div className="queries-search">
          <span>⌕</span>

          <input
            type="text"
            placeholder="Search queries..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>

        <button
          className="queries-refresh-button"
          onClick={fetchQueries}
          disabled={loading}
        >
          ↻ Refresh
        </button>
      </div>

      {error && <div className="queries-error">{error}</div>}

      <div className="queries-table-card">
        <table className="queries-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Order</th>
              <th>Department</th>
              <th>Subject</th>
              <th>Priority</th>
              <th>Status</th>
              <th>Created Date</th>
              <th>Action</th>
            </tr>
          </thead>

          <tbody>
            {loading ? (
              <tr>
                <td colSpan="8" className="queries-empty">
                  Loading queries...
                </td>
              </tr>
            ) : filteredQueries.length === 0 ? (
              <tr>
                <td colSpan="8" className="queries-empty">
                  {search ? "No matching queries found." : "No queries found."}
                </td>
              </tr>
            ) : (
              filteredQueries.map((query) => (
                <tr key={query.id}>
                  <td>#{query.id}</td>

                  <td>
                    <strong>{query.order_number || "-"}</strong>
                  </td>

                  <td>{query.department || "-"}</td>

                  <td className="query-subject">
                    {query.subject || "-"}
                  </td>

                  <td>
                    <span className={getPriorityClass(query.priority)}>
                      {query.priority || "-"}
                    </span>
                  </td>

                  <td>
                    <span className={getStatusClass(query.status)}>
                      {query.status || "-"}
                    </span>
                  </td>

                  <td>{formatDate(query.created_at)}</td>

                  <td>
                    <button
                      className="query-view-button"
                      onClick={() => openQuery(query)}
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

      {selectedQuery && (
        <div className="query-modal-overlay" onClick={closeModal}>
          <div
            className="query-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="query-modal-header">
              <div>
                <h2>Query Details</h2>
                <p>Query #{selectedQuery.id}</p>
              </div>

              <button
                className="query-close-button"
                onClick={closeModal}
              >
                ×
              </button>
            </div>

            <div className="query-details-grid">
              <div className="query-detail-card">
                <span>Query ID</span>
                <strong>#{selectedQuery.id}</strong>
              </div>

              <div className="query-detail-card">
                <span>Order</span>
                <strong>{selectedQuery.order_number || "-"}</strong>
              </div>

              <div className="query-detail-card">
                <span>Department</span>
                <strong>{selectedQuery.department || "-"}</strong>
              </div>

              <div className="query-detail-card">
                <span>Priority</span>
                <span className={getPriorityClass(selectedQuery.priority)}>
                  {selectedQuery.priority || "-"}
                </span>
              </div>

              <div className="query-detail-card">
                <span>Status</span>
                <span className={getStatusClass(selectedQuery.status)}>
                  {selectedQuery.status || "-"}
                </span>
              </div>

              <div className="query-detail-card">
                <span>Created Date</span>
                <strong>
                  {formatDate(selectedQuery.created_at)}
                </strong>
              </div>
            </div>

            <div className="query-content-card">
              <span>Subject</span>
              <strong>{selectedQuery.subject || "-"}</strong>
            </div>

            <div className="query-content-card">
              <span>Description</span>
              <p>{selectedQuery.description || "-"}</p>
            </div>

            <div className="query-modal-footer">
              <button onClick={closeModal}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Queries;