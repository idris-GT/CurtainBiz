import React, { useEffect, useMemo, useState } from "react";
import api from "./api/client";
import "./Production.css";

const STATUS_OPTIONS = [
  "PENDING",
  "IN_PROGRESS",
  "PAUSED",
  "QUALITY_CHECK",
  "COMPLETED",
  "CANCELLED",
];

const formatDate = (value) => {
  if (!value) return "-";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
};

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
      return "production-status completed";

    case "IN_PROGRESS":
      return "production-status progress";

    case "QUALITY_CHECK":
      return "production-status quality";

    case "PAUSED":
      return "production-status paused";

    case "CANCELLED":
      return "production-status cancelled";

    default:
      return "production-status pending";
  }
};

const emptyForm = {
  order_id: "",
  assigned_department_id: "",
  assigned_employee_id: "",
  status: "PENDING",
  start_date: "",
  completion_date: "",
  notes: "",
};

export default function Production() {
  const [productions, setProductions] = useState([]);
  const [orders, setOrders] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [employees, setEmployees] = useState([]);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [search, setSearch] = useState("");

  const [showCreate, setShowCreate] = useState(false);
  const [selectedProduction, setSelectedProduction] = useState(null);

  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState("");

  const loadProduction = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get("/production/");
      setProductions(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.detail ||
          "Unable to load production records."
      );
    } finally {
      setLoading(false);
    }
  };

  const loadFormData = async () => {
    try {
      const requests = [
        api.get("/orders/"),
        api.get("/departments/"),
        api.get("/employees/"),
      ];

      const [ordersResponse, departmentsResponse, employeesResponse] =
        await Promise.all(requests);

      setOrders(
        Array.isArray(ordersResponse.data)
          ? ordersResponse.data
          : []
      );

      setDepartments(
        Array.isArray(departmentsResponse.data)
          ? departmentsResponse.data
          : []
      );

      setEmployees(
        Array.isArray(employeesResponse.data)
          ? employeesResponse.data
          : []
      );
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.detail ||
          "Unable to load orders, departments or employees."
      );
    }
  };

  useEffect(() => {
    loadProduction();
    loadFormData();
  }, []);

  const filteredProductions = useMemo(() => {
    const value = search.trim().toLowerCase();

    if (!value) return productions;

    return productions.filter((item) => {
      return [
        item.id,
        item.order_id,
        item.order_number,
        item.department,
        item.assigned_employee,
        item.status,
        item.notes,
      ]
        .filter(Boolean)
        .some((field) =>
          String(field).toLowerCase().includes(value)
        );
    });
  }, [productions, search]);

  const totalProduction = productions.length;

  const inProgress = productions.filter(
    (item) => item.status === "IN_PROGRESS"
  ).length;

  const completed = productions.filter(
    (item) => item.status === "COMPLETED"
  ).length;

  const qualityCheck = productions.filter(
    (item) => item.status === "QUALITY_CHECK"
  ).length;

  const handleInputChange = (event) => {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const handleCreateProduction = async (event) => {
    event.preventDefault();

    if (!form.order_id) {
      setError("Please select an order.");
      return;
    }

    if (!form.assigned_department_id) {
      setError("Please select a department.");
      return;
    }

    if (!form.assigned_employee_id) {
      setError("Please select an employee.");
      return;
    }

    try {
      setSaving(true);
      setError("");

      const payload = {
        order_id: Number(form.order_id),
        assigned_department_id: Number(
          form.assigned_department_id
        ),
        assigned_employee_id: Number(
          form.assigned_employee_id
        ),
        status: form.status,
        start_date: form.start_date
          ? new Date(form.start_date).toISOString()
          : null,
        completion_date: form.completion_date
          ? new Date(form.completion_date).toISOString()
          : null,
        notes: form.notes.trim() || null,
      };

      await api.post("/production/", payload);

      setShowCreate(false);
      setForm(emptyForm);

      await loadProduction();
    } catch (err) {
      console.error(err);

      setError(
        err.response?.data?.detail ||
          "Unable to create production record."
      );
    } finally {
      setSaving(false);
    }
  };

  const openCreateModal = () => {
    setError("");
    setForm(emptyForm);
    setShowCreate(true);
  };

  const closeCreateModal = () => {
    if (saving) return;

    setShowCreate(false);
    setForm(emptyForm);
    setError("");
  };

  const viewProduction = async (production) => {
    try {
      setError("");

      const response = await api.get(
        `/production/${production.id}`
      );

      setSelectedProduction(response.data);
    } catch (err) {
      console.error(err);

      setSelectedProduction(production);
    }
  };

  return (
    <div className="production-page">
      <div className="production-header">
        <div>
          <h1>Production</h1>
          <p>
            Manage production records and monitor manufacturing
            progress.
          </p>
        </div>

        <button
          className="production-primary-btn"
          onClick={openCreateModal}
        >
          + New Production
        </button>
      </div>

      {error && (
        <div className="production-error">
          {error}
        </div>
      )}

      <div className="production-stats">
        <div className="production-stat-card">
          <div className="production-stat-label">
            Total Production
          </div>

          <div className="production-stat-value">
            {totalProduction}
          </div>
        </div>

        <div className="production-stat-card">
          <div className="production-stat-label">
            In Progress
          </div>

          <div className="production-stat-value">
            {inProgress}
          </div>
        </div>

        <div className="production-stat-card">
          <div className="production-stat-label">
            Quality Check
          </div>

          <div className="production-stat-value">
            {qualityCheck}
          </div>
        </div>

        <div className="production-stat-card">
          <div className="production-stat-label">
            Completed
          </div>

          <div className="production-stat-value">
            {completed}
          </div>
        </div>
      </div>

      <div className="production-toolbar">
        <div className="production-search">
          <span>⌕</span>

          <input
            type="text"
            placeholder="Search production..."
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
          />
        </div>

        <button
          className="production-refresh-btn"
          onClick={loadProduction}
          disabled={loading}
        >
          ↻ Refresh
        </button>
      </div>

      <div className="production-table-card">
        <div className="production-table-wrapper">
          <table className="production-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Order</th>
                <th>Department</th>
                <th>Employee</th>
                <th>Status</th>
                <th>Start Date</th>
                <th>Completion Date</th>
                <th>Notes</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td
                    colSpan="9"
                    className="production-empty"
                  >
                    Loading production...
                  </td>
                </tr>
              ) : filteredProductions.length === 0 ? (
                <tr>
                  <td
                    colSpan="9"
                    className="production-empty"
                  >
                    No production records found.
                  </td>
                </tr>
              ) : (
                filteredProductions.map((item) => (
                  <tr key={item.id}>
                    <td>#{item.id}</td>

                    <td>
                      <strong>
                        {item.order_number ||
                          `Order #${item.order_id}`}
                      </strong>
                    </td>

                    <td>
                      {item.department ||
                        item.assigned_department_id ||
                        "-"}
                    </td>

                    <td>
                      {item.assigned_employee ||
                        item.assigned_employee_id ||
                        "-"}
                    </td>

                    <td>
                      <span
                        className={getStatusClass(
                          item.status
                        )}
                      >
                        {item.status || "PENDING"}
                      </span>
                    </td>

                    <td>
                      {formatDate(item.start_date)}
                    </td>

                    <td>
                      {formatDate(item.completion_date)}
                    </td>

                    <td className="production-notes">
                      {item.notes || "-"}
                    </td>

                    <td>
                      <button
                        className="production-view-btn"
                        onClick={() =>
                          viewProduction(item)
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

      {showCreate && (
        <div
          className="production-modal-overlay"
          onMouseDown={closeCreateModal}
        >
          <div
            className="production-modal"
            onMouseDown={(event) =>
              event.stopPropagation()
            }
          >
            <div className="production-modal-header">
              <div>
                <h2>New Production</h2>
                <p>Create a production record for an order.</p>
              </div>

              <button
                className="production-close-btn"
                onClick={closeCreateModal}
                disabled={saving}
              >
                ×
              </button>
            </div>

            <form onSubmit={handleCreateProduction}>
              <div className="production-form-grid">
                <div className="production-form-group">
                  <label>Order *</label>

                  <select
                    name="order_id"
                    value={form.order_id}
                    onChange={handleInputChange}
                  >
                    <option value="">
                      Select order
                    </option>

                    {orders.map((order) => (
                      <option
                        key={order.id}
                        value={order.id}
                      >
                        {order.order_number ||
                          `Order #${order.id}`}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="production-form-group">
                  <label>Department *</label>

                  <select
                    name="assigned_department_id"
                    value={
                      form.assigned_department_id
                    }
                    onChange={handleInputChange}
                  >
                    <option value="">
                      Select department
                    </option>

                    {departments.map((department) => (
                      <option
                        key={department.id}
                        value={department.id}
                      >
                        {department.name ||
                          department.department_name ||
                          `Department #${department.id}`}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="production-form-group">
                  <label>Assigned Employee *</label>

                  <select
                    name="assigned_employee_id"
                    value={form.assigned_employee_id}
                    onChange={handleInputChange}
                  >
                    <option value="">
                      Select employee
                    </option>

                    {employees.map((employee) => (
                      <option
                        key={employee.id}
                        value={employee.id}
                      >
                        {employee.name ||
                          employee.full_name ||
                          `${employee.first_name || ""} ${
                            employee.last_name || ""
                          }`.trim() ||
                          `Employee #${employee.id}`}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="production-form-group">
                  <label>Status *</label>

                  <select
                    name="status"
                    value={form.status}
                    onChange={handleInputChange}
                  >
                    {STATUS_OPTIONS.map((status) => (
                      <option
                        key={status}
                        value={status}
                      >
                        {status}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="production-form-group">
                  <label>Start Date</label>

                  <input
                    type="datetime-local"
                    name="start_date"
                    value={form.start_date}
                    onChange={handleInputChange}
                  />
                </div>

                <div className="production-form-group">
                  <label>Completion Date</label>

                  <input
                    type="datetime-local"
                    name="completion_date"
                    value={form.completion_date}
                    onChange={handleInputChange}
                  />
                </div>

                <div className="production-form-group full-width">
                  <label>Notes</label>

                  <textarea
                    name="notes"
                    value={form.notes}
                    onChange={handleInputChange}
                    placeholder="Enter production notes..."
                    rows="4"
                  />
                </div>
              </div>

              <div className="production-modal-actions">
                <button
                  type="button"
                  className="production-cancel-btn"
                  onClick={closeCreateModal}
                  disabled={saving}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="production-save-btn"
                  disabled={saving}
                >
                  {saving
                    ? "Creating..."
                    : "Create Production"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {selectedProduction && (
        <div
          className="production-modal-overlay"
          onMouseDown={() =>
            setSelectedProduction(null)
          }
        >
          <div
            className="production-details-modal"
            onMouseDown={(event) =>
              event.stopPropagation()
            }
          >
            <div className="production-modal-header">
              <div>
                <h2>Production Details</h2>
                <p>
                  Production #{selectedProduction.id}
                </p>
              </div>

              <button
                className="production-close-btn"
                onClick={() =>
                  setSelectedProduction(null)
                }
              >
                ×
              </button>
            </div>

            <div className="production-details-grid">
              <div>
                <span>Production ID</span>
                <strong>
                  #{selectedProduction.id}
                </strong>
              </div>

              <div>
                <span>Order</span>
                <strong>
                  {selectedProduction.order_number ||
                    `Order #${selectedProduction.order_id}`}
                </strong>
              </div>

              <div>
                <span>Department</span>
                <strong>
                  {selectedProduction.department ||
                    selectedProduction.assigned_department_id ||
                    "-"}
                </strong>
              </div>

              <div>
                <span>Employee</span>
                <strong>
                  {selectedProduction.assigned_employee ||
                    selectedProduction.assigned_employee_id ||
                    "-"}
                </strong>
              </div>

              <div>
                <span>Status</span>

                <strong>
                  <span
                    className={getStatusClass(
                      selectedProduction.status
                    )}
                  >
                    {selectedProduction.status ||
                      "PENDING"}
                  </span>
                </strong>
              </div>

              <div>
                <span>Start Date</span>
                <strong>
                  {formatDateTime(
                    selectedProduction.start_date
                  )}
                </strong>
              </div>

              <div>
                <span>Completion Date</span>
                <strong>
                  {formatDateTime(
                    selectedProduction.completion_date
                  )}
                </strong>
              </div>

              <div>
                <span>Created At</span>
                <strong>
                  {formatDateTime(
                    selectedProduction.created_at
                  )}
                </strong>
              </div>

              <div className="details-full">
                <span>Notes</span>
                <strong>
                  {selectedProduction.notes || "-"}
                </strong>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}