import React, { useEffect, useMemo, useState } from "react";
import api from "./api/client";
import "./ProductionTasks.css";

const formatDateTime = (value) => {
  if (!value) return "-";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const getStatusClass = (status) => {
  switch (status) {
    case "COMPLETED":
      return "task-status completed";

    case "IN_PROGRESS":
      return "task-status progress";

    case "QUALITY_CHECK":
      return "task-status quality";

    case "CANCELLED":
      return "task-status cancelled";

    default:
      return "task-status pending";
  }
};

const getPriorityClass = (priority) => {
  switch (priority) {
    case "HIGH":
      return "task-priority high";

    case "LOW":
      return "task-priority low";

    default:
      return "task-priority medium";
  }
};

export default function ProductionTasks() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedTask, setSelectedTask] = useState(null);
  const [error, setError] = useState("");

  const loadTasks = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get("/production-tasks/");

      setTasks(
        Array.isArray(response.data)
          ? response.data
          : []
      );
    } catch (err) {
      console.error(err);

      setError(
        err.response?.data?.detail ||
          "Unable to load production tasks."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, []);

  const filteredTasks = useMemo(() => {
    const value = search.trim().toLowerCase();

    if (!value) return tasks;

    return tasks.filter((task) => {
      return [
        task.id,
        task.production_id,
        task.order_number,
        task.task_name,
        task.assigned_employee,
        task.status,
        task.priority,
        task.notes,
      ]
        .filter(Boolean)
        .some((field) =>
          String(field).toLowerCase().includes(value)
        );
    });
  }, [tasks, search]);

  const totalTasks = tasks.length;

  const pendingTasks = tasks.filter(
    (task) => task.status === "PENDING"
  ).length;

  const activeTasks = tasks.filter(
    (task) => task.status === "IN_PROGRESS"
  ).length;

  const completedTasks = tasks.filter(
    (task) => task.status === "COMPLETED"
  ).length;

  const viewTask = async (task) => {
    try {
      const response = await api.get(
        `/production-tasks/${task.id}`
      );

      setSelectedTask(response.data);
    } catch (err) {
      console.error(err);
      setSelectedTask(task);
    }
  };

  return (
    <div className="production-tasks-page">
      <div className="production-tasks-header">
        <div>
          <h1>Production Tasks</h1>
          <p>
            Monitor individual tasks assigned to production
            employees.
          </p>
        </div>

        <button
          className="production-tasks-refresh"
          onClick={loadTasks}
          disabled={loading}
        >
          ↻ Refresh
        </button>
      </div>

      {error && (
        <div className="production-tasks-error">
          {error}
        </div>
      )}

      <div className="production-tasks-stats">
        <div className="production-tasks-stat">
          <span>Total Tasks</span>
          <strong>{totalTasks}</strong>
        </div>

        <div className="production-tasks-stat">
          <span>Pending</span>
          <strong>{pendingTasks}</strong>
        </div>

        <div className="production-tasks-stat">
          <span>In Progress</span>
          <strong>{activeTasks}</strong>
        </div>

        <div className="production-tasks-stat">
          <span>Completed</span>
          <strong>{completedTasks}</strong>
        </div>
      </div>

      <div className="production-tasks-toolbar">
        <div className="production-tasks-search">
          <span>⌕</span>

          <input
            type="text"
            placeholder="Search production tasks..."
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
          />
        </div>
      </div>

      <div className="production-tasks-table-card">
        <div className="production-tasks-table-wrapper">
          <table className="production-tasks-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Production</th>
                <th>Order</th>
                <th>Task</th>
                <th>Employee</th>
                <th>Status</th>
                <th>Priority</th>
                <th>Started</th>
                <th>Completed</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td
                    colSpan="10"
                    className="production-tasks-empty"
                  >
                    Loading production tasks...
                  </td>
                </tr>
              ) : filteredTasks.length === 0 ? (
                <tr>
                  <td
                    colSpan="10"
                    className="production-tasks-empty"
                  >
                    No production tasks found.
                  </td>
                </tr>
              ) : (
                filteredTasks.map((task) => (
                  <tr key={task.id}>
                    <td>#{task.id}</td>

                    <td>
                      #{task.production_id}
                    </td>

                    <td>
                      <strong>
                        {task.order_number || "-"}
                      </strong>
                    </td>

                    <td>{task.task_name || "-"}</td>

                    <td>
                      {task.assigned_employee ||
                        task.assigned_employee_id ||
                        "-"}
                    </td>

                    <td>
                      <span
                        className={getStatusClass(
                          task.status
                        )}
                      >
                        {task.status || "PENDING"}
                      </span>
                    </td>

                    <td>
                      <span
                        className={getPriorityClass(
                          task.priority
                        )}
                      >
                        {task.priority || "MEDIUM"}
                      </span>
                    </td>

                    <td>
                      {formatDateTime(task.started_at)}
                    </td>

                    <td>
                      {formatDateTime(task.completed_at)}
                    </td>

                    <td>
                      <button
                        className="production-task-view"
                        onClick={() =>
                          viewTask(task)
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

      {selectedTask && (
        <div
          className="production-task-modal-overlay"
          onMouseDown={() =>
            setSelectedTask(null)
          }
        >
          <div
            className="production-task-modal"
            onMouseDown={(event) =>
              event.stopPropagation()
            }
          >
            <div className="production-task-modal-header">
              <div>
                <h2>Task Details</h2>
                <p>
                  Production Task #{selectedTask.id}
                </p>
              </div>

              <button
                className="production-task-close"
                onClick={() =>
                  setSelectedTask(null)
                }
              >
                ×
              </button>
            </div>

            <div className="production-task-details">
              <div>
                <span>Task ID</span>
                <strong>
                  #{selectedTask.id}
                </strong>
              </div>

              <div>
                <span>Production ID</span>
                <strong>
                  #{selectedTask.production_id}
                </strong>
              </div>

              <div>
                <span>Order</span>
                <strong>
                  {selectedTask.order_number || "-"}
                </strong>
              </div>

              <div>
                <span>Task Name</span>
                <strong>
                  {selectedTask.task_name || "-"}
                </strong>
              </div>

              <div>
                <span>Assigned Employee</span>
                <strong>
                  {selectedTask.assigned_employee ||
                    selectedTask.assigned_employee_id ||
                    "-"}
                </strong>
              </div>

              <div>
                <span>Status</span>
                <strong>
                  <span
                    className={getStatusClass(
                      selectedTask.status
                    )}
                  >
                    {selectedTask.status || "PENDING"}
                  </span>
                </strong>
              </div>

              <div>
                <span>Priority</span>
                <strong>
                  <span
                    className={getPriorityClass(
                      selectedTask.priority
                    )}
                  >
                    {selectedTask.priority || "MEDIUM"}
                  </span>
                </strong>
              </div>

              <div>
                <span>Started At</span>
                <strong>
                  {formatDateTime(
                    selectedTask.started_at
                  )}
                </strong>
              </div>

              <div>
                <span>Completed At</span>
                <strong>
                  {formatDateTime(
                    selectedTask.completed_at
                  )}
                </strong>
              </div>

              <div className="production-task-details-full">
                <span>Notes</span>
                <strong>
                  {selectedTask.notes || "-"}
                </strong>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}