import { useEffect, useState } from "react";
import api from "./api/client";
import "./Employees.css";

const emptyForm = {
  employee_code: "",
  first_name: "",
  last_name: "",
  email: "",
  phone: "",
  department_id: "",
  job_title: "",
  joining_date: "",
  employment_status: "ACTIVE",
};

const getArray = (response) => {
  if (Array.isArray(response.data)) return response.data;
  if (Array.isArray(response.data?.data)) return response.data.data;
  if (Array.isArray(response.data?.items)) return response.data.items;
  return [];
};

function Employees() {
  const [employees, setEmployees] = useState([]);
  const [departments, setDepartments] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");

  const [showModal, setShowModal] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState(null);

  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);

  const loadEmployees = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get("/employees/");
      setEmployees(getArray(response));
    } catch (err) {
      console.error("Employees API error:", err);
      setError("Unable to load employees.");
    } finally {
      setLoading(false);
    }
  };

  const loadDepartments = async () => {
    try {
      const response = await api.get("/departments/");
      setDepartments(getArray(response));
    } catch (err) {
      console.error("Departments API error:", err);
    }
  };

  useEffect(() => {
    loadEmployees();
    loadDepartments();
  }, []);

  const filteredEmployees = employees.filter((employee) => {
    const text = [
      employee.employee_code,
      employee.first_name,
      employee.last_name,
      employee.email,
      employee.phone,
      employee.job_title,
      employee.employment_status,
    ]
      .join(" ")
      .toLowerCase();

    return text.includes(search.toLowerCase());
  });

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const openAddModal = () => {
    setEditingEmployee(null);

    setForm({
      ...emptyForm,
      joining_date: new Date().toISOString().split("T")[0],
    });

    setShowModal(true);
  };

  const openEditModal = (employee) => {
    setEditingEmployee(employee);

    setForm({
      employee_code: employee.employee_code || "",
      first_name: employee.first_name || "",
      last_name: employee.last_name || "",
      email: employee.email || "",
      phone: employee.phone || "",
      department_id: employee.department_id || "",
      job_title: employee.job_title || "",
      joining_date: employee.joining_date
        ? String(employee.joining_date).split("T")[0]
        : "",
      employment_status:
        employee.employment_status || "ACTIVE",
    });

    setShowModal(true);
  };

  const closeModal = () => {
    if (saving) return;

    setShowModal(false);
    setEditingEmployee(null);
    setForm(emptyForm);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (
      !form.employee_code ||
      !form.first_name ||
      !form.last_name ||
      !form.email ||
      !form.phone ||
      !form.department_id ||
      !form.job_title ||
      !form.joining_date
    ) {
      alert("Please fill in all required fields.");
      return;
    }

    const payload = {
      employee_code: form.employee_code.trim(),
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),
      email: form.email.trim(),
      phone: form.phone.trim(),
      department_id: Number(form.department_id),
      job_title: form.job_title.trim(),
      joining_date: form.joining_date,
      employment_status: form.employment_status,
    };

    try {
      setSaving(true);

      if (editingEmployee) {
        await api.put(
          `/employees/${editingEmployee.employee_id}`,
          payload
        );
      } else {
        await api.post("/employees/", payload);
      }

      closeModal();
      await loadEmployees();
    } catch (err) {
      console.error("Employee save error:", err);

      const message =
        err.response?.data?.detail ||
        "Unable to save employee.";

      alert(message);
    } finally {
      setSaving(false);
    }
  };

  const handleDeactivate = async (employee) => {
    const employeeName = `${employee.first_name || ""} ${
      employee.last_name || ""
    }`.trim();

    const confirmed = window.confirm(
      `Deactivate ${employeeName || "this employee"}?`
    );

    if (!confirmed) return;

    try {
      await api.delete(
        `/employees/${employee.employee_id}`
      );

      await loadEmployees();
    } catch (err) {
      console.error("Employee deactivate error:", err);

      const message =
        err.response?.data?.detail ||
        "Unable to deactivate employee.";

      alert(message);
    }
  };

  const getDepartmentName = (departmentId) => {
    const department = departments.find(
      (item) =>
        Number(item.department_id || item.id) ===
        Number(departmentId)
    );

    return department?.name || `Department #${departmentId || "—"}`;
  };

  const getInitial = (employee) => {
    return (
      employee.first_name?.charAt(0)?.toUpperCase() ||
      "E"
    );
  };

  return (
    <section className="employees-page">
      <div className="employees-header">
        <div>
          <p className="employees-eyebrow">
            EMPLOYEE MANAGEMENT
          </p>

          <h1>Employees</h1>

          <p>
            Manage your employees, departments and workforce
            information.
          </p>
        </div>

        <button
          className="employees-primary-button"
          onClick={openAddModal}
        >
          + Add Employee
        </button>
      </div>

      {error && (
        <div className="employees-error">
          {error}
        </div>
      )}

      <div className="employees-toolbar">
        <div className="employees-count">
          <strong>{employees.length}</strong>
          <span>employees</span>
        </div>

        <div className="employees-search">
          <span>⌕</span>

          <input
            type="text"
            placeholder="Search employees..."
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
          />
        </div>

        <button
          className="employees-refresh"
          onClick={loadEmployees}
          disabled={loading}
        >
          ↻ Refresh
        </button>
      </div>

      <div className="employees-table-card">
        <table className="employees-table">
          <thead>
            <tr>
              <th>EMPLOYEE</th>
              <th>CONTACT</th>
              <th>DEPARTMENT</th>
              <th>JOB TITLE</th>
              <th>STATUS</th>
              <th>ACTIONS</th>
            </tr>
          </thead>

          <tbody>
            {loading ? (
              <tr>
                <td colSpan="6" className="employees-empty">
                  Loading employees...
                </td>
              </tr>
            ) : filteredEmployees.length === 0 ? (
              <tr>
                <td colSpan="6" className="employees-empty">
                  {search
                    ? "No employees match your search."
                    : "No employees found."}
                </td>
              </tr>
            ) : (
              filteredEmployees.map((employee) => (
                <tr key={employee.employee_id}>
                  <td>
                    <div className="employee-main">
                      <div className="employee-avatar">
                        {getInitial(employee)}
                      </div>

                      <div>
                        <strong>
                          {employee.first_name}{" "}
                          {employee.last_name}
                        </strong>

                        <span>
                          {employee.employee_code}
                        </span>
                      </div>
                    </div>
                  </td>

                  <td>
                    <div className="employee-contact">
                      <span>
                        {employee.email || "—"}
                      </span>

                      <small>
                        {employee.phone || "—"}
                      </small>
                    </div>
                  </td>

                  <td>
                    {getDepartmentName(
                      employee.department_id
                    )}
                  </td>

                  <td>
                    {employee.job_title || "—"}
                  </td>

                  <td>
                    <span
                      className={`employee-status ${
                        String(
                          employee.employment_status || ""
                        ).toLowerCase()
                      }`}
                    >
                      {employee.employment_status ||
                        "UNKNOWN"}
                    </span>
                  </td>

                  <td>
                    <div className="employee-actions">
                      <button
                        className="employee-edit-button"
                        onClick={() =>
                          openEditModal(employee)
                        }
                      >
                        Edit
                      </button>

                      <button
                        className="employee-delete-button"
                        onClick={() =>
                          handleDeactivate(employee)
                        }
                      >
                        Deactivate
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* ADD / EDIT MODAL */}
      {showModal && (
        <div className="employee-modal-overlay">
          <div className="employee-modal">
            <div className="employee-modal-header">
              <div>
                <p className="employees-eyebrow">
                  {editingEmployee
                    ? "EDIT EMPLOYEE"
                    : "NEW EMPLOYEE"}
                </p>

                <h2>
                  {editingEmployee
                    ? "Edit Employee"
                    : "Add Employee"}
                </h2>
              </div>

              <button
                className="employee-close-button"
                onClick={closeModal}
              >
                ×
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="employee-form-grid">
                <div className="employee-field">
                  <label>Employee Code</label>

                  <input
                    name="employee_code"
                    value={form.employee_code}
                    onChange={handleChange}
                    placeholder="e.g. EMP001"
                    required
                  />
                </div>

                <div className="employee-field">
                  <label>First Name</label>

                  <input
                    name="first_name"
                    value={form.first_name}
                    onChange={handleChange}
                    placeholder="e.g. Arun"
                    required
                  />
                </div>

                <div className="employee-field">
                  <label>Last Name</label>

                  <input
                    name="last_name"
                    value={form.last_name}
                    onChange={handleChange}
                    placeholder="e.g. Kumar"
                    required
                  />
                </div>

                <div className="employee-field">
                  <label>Email</label>

                  <input
                    type="email"
                    name="email"
                    value={form.email}
                    onChange={handleChange}
                    placeholder="employee@example.com"
                    required
                  />
                </div>

                <div className="employee-field">
                  <label>Phone</label>

                  <input
                    name="phone"
                    value={form.phone}
                    onChange={handleChange}
                    placeholder="9876543210"
                    required
                  />
                </div>

                <div className="employee-field">
                  <label>Department</label>

                  {departments.length > 0 ? (
                    <select
                      name="department_id"
                      value={form.department_id}
                      onChange={handleChange}
                      required
                    >
                      <option value="">
                        Select department
                      </option>

                      {departments.map((department) => (
                        <option
                          key={
                            department.department_id ||
                            department.id
                          }
                          value={
                            department.department_id ||
                            department.id
                          }
                        >
                          {department.name ||
                            department.department_name ||
                            `Department #${
                              department.department_id ||
                              department.id
                            }`}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="number"
                      name="department_id"
                      value={form.department_id}
                      onChange={handleChange}
                      placeholder="Department ID"
                      required
                    />
                  )}
                </div>

                <div className="employee-field">
                  <label>Job Title</label>

                  <input
                    name="job_title"
                    value={form.job_title}
                    onChange={handleChange}
                    placeholder="e.g. Production Manager"
                    required
                  />
                </div>

                <div className="employee-field">
                  <label>Joining Date</label>

                  <input
                    type="date"
                    name="joining_date"
                    value={form.joining_date}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className="employee-field employee-full">
                  <label>Employment Status</label>

                  <select
                    name="employment_status"
                    value={form.employment_status}
                    onChange={handleChange}
                  >
                    <option value="ACTIVE">
                      Active
                    </option>

                    <option value="INACTIVE">
                      Inactive
                    </option>
                  </select>
                </div>
              </div>

              <div className="employee-modal-footer">
                <button
                  type="button"
                  className="employee-cancel-button"
                  onClick={closeModal}
                  disabled={saving}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="employees-primary-button"
                  disabled={saving}
                >
                  {saving
                    ? "Saving..."
                    : editingEmployee
                    ? "Update Employee"
                    : "Create Employee"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  );
}

export default Employees;