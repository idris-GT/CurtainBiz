import { useEffect, useMemo, useState } from "react";
import api from "./api/client";
import "./Customers.css";

const emptyForm = {
  customer_code: "",
  name: "",
  email: "",
  phone: "",
  address: "",
  city: "",
  state: "",
};

function Customers() {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [search, setSearch] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState(null);

  const [form, setForm] = useState(emptyForm);

  const loadCustomers = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await api.get("/customers/");

      const data = Array.isArray(response.data)
        ? response.data
        : response.data?.items || response.data?.data || [];

      setCustomers(data);
    } catch (err) {
      console.error("Customer loading error:", err);

      if (err.response?.status === 401) {
        setError("Your session has expired. Please log in again.");
      } else {
        setError("Unable to load customers.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCustomers();
  }, []);

  const filteredCustomers = useMemo(() => {
    const term = search.trim().toLowerCase();

    if (!term) {
      return customers;
    }

    return customers.filter((customer) =>
      [
        customer.customer_code,
        customer.name,
        customer.email,
        customer.phone,
        customer.city,
        customer.state,
      ]
        .filter(Boolean)
        .some((value) =>
          String(value).toLowerCase().includes(term)
        )
    );
  }, [customers, search]);

  const openAddForm = () => {
    setEditingCustomer(null);
    setForm(emptyForm);
    setError("");
    setSuccess("");
    setShowForm(true);
  };

  const openEditForm = (customer) => {
    setEditingCustomer(customer);

    setForm({
      customer_code: customer.customer_code || "",
      name: customer.name || "",
      email: customer.email || "",
      phone: customer.phone || "",
      address: customer.address || "",
      city: customer.city || "",
      state: customer.state || "",
    });

    setError("");
    setSuccess("");
    setShowForm(true);
  };

  const closeForm = () => {
    if (saving) return;

    setShowForm(false);
    setEditingCustomer(null);
    setForm(emptyForm);
  };

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setSaving(true);
    setError("");
    setSuccess("");

    try {
      if (editingCustomer) {
        const customerId =
          editingCustomer.customer_id ?? editingCustomer.id;

        await api.put(`/customers/${customerId}`, form);

        setSuccess("Customer updated successfully.");
      } else {
        await api.post("/customers/", form);

        setSuccess("Customer created successfully.");
      }

      await loadCustomers();

      setShowForm(false);
      setEditingCustomer(null);
      setForm(emptyForm);
    } catch (err) {
      console.error("Customer save error:", err);

      const detail = err.response?.data?.detail;

      if (typeof detail === "string") {
        setError(detail);
      } else if (Array.isArray(detail)) {
        setError(
          detail
            .map((item) => item.msg || "Invalid customer data")
            .join(", ")
        );
      } else {
        setError(
          editingCustomer
            ? "Unable to update customer."
            : "Unable to create customer."
        );
      }
    } finally {
      setSaving(false);
    }
  };

  const handleDeactivate = async (customer) => {
    const customerId = customer.customer_id ?? customer.id;

    const confirmed = window.confirm(
      `Deactivate ${customer.name || "this customer"}?`
    );

    if (!confirmed) return;

    setError("");
    setSuccess("");

    try {
      await api.delete(`/customers/${customerId}`);

      setSuccess("Customer deactivated successfully.");

      await loadCustomers();
    } catch (err) {
      console.error("Customer deactivation error:", err);

      const detail = err.response?.data?.detail;

      setError(
        typeof detail === "string"
          ? detail
          : "Unable to deactivate customer."
      );
    }
  };

  return (
    <section className="customers-page">
      <div className="customers-header">
        <div>
          <p className="eyebrow">CUSTOMER MANAGEMENT</p>
          <h3>Customers</h3>
          <p>Manage your customer database and contact information.</p>
        </div>

        <button className="primary-button" onClick={openAddForm}>
          + Add Customer
        </button>
      </div>

      {error && (
        <div className="customers-alert error">
          {error}
        </div>
      )}

      {success && (
        <div className="customers-alert success">
          {success}
        </div>
      )}

      <div className="customers-toolbar">
        <div className="customer-count">
          <strong>{filteredCustomers.length}</strong>
          <span>
            {search
              ? ` of ${customers.length} customers`
              : " customers"}
          </span>
        </div>

        <div className="customer-search">
          <span>⌕</span>

          <input
            type="text"
            placeholder="Search customers..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />

          {search && (
            <button
              type="button"
              onClick={() => setSearch("")}
              title="Clear search"
            >
              ×
            </button>
          )}
        </div>

        <button
          className="refresh-button"
          onClick={loadCustomers}
          disabled={loading}
          title="Refresh customers"
        >
          ↻ Refresh
        </button>
      </div>

      <div className="customers-panel">
        <div className="table-wrapper">
          <table className="customers-table">
            <thead>
              <tr>
                <th>CUSTOMER</th>
                <th>CONTACT</th>
                <th>LOCATION</th>
                <th>PHONE</th>
                <th>ACTIONS</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="5" className="table-message">
                    Loading customers...
                  </td>
                </tr>
              ) : filteredCustomers.length === 0 ? (
                <tr>
                  <td colSpan="5" className="table-message">
                    {search
                      ? "No customers match your search."
                      : "No customers found."}
                  </td>
                </tr>
              ) : (
                filteredCustomers.map((customer) => {
                  const customerId =
                    customer.customer_id ?? customer.id;

                  return (
                    <tr key={customerId}>
                      <td>
                        <div className="customer-name">
                          <div className="customer-avatar">
                            {(customer.name || "C")
                              .charAt(0)
                              .toUpperCase()}
                          </div>

                          <div>
                            <strong>
                              {customer.name || "Unnamed Customer"}
                            </strong>

                            <small>
                              {customer.customer_code || "No code"}
                            </small>
                          </div>
                        </div>
                      </td>

                      <td>
                        {customer.email || "—"}
                      </td>

                      <td>
                        {[customer.city, customer.state]
                          .filter(Boolean)
                          .join(", ") || "—"}
                      </td>

                      <td>
                        {customer.phone || "—"}
                      </td>

                      <td>
                        <div className="customer-actions">
                          <button
                            className="edit-button"
                            onClick={() =>
                              openEditForm(customer)
                            }
                          >
                            Edit
                          </button>

                          <button
                            className="deactivate-button"
                            onClick={() =>
                              handleDeactivate(customer)
                            }
                          >
                            Deactivate
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {showForm && (
        <div className="modal-backdrop">
          <div className="customer-modal">
            <div className="modal-header">
              <div>
                <p className="eyebrow">
                  {editingCustomer
                    ? "EDIT CUSTOMER"
                    : "NEW CUSTOMER"}
                </p>

                <h3>
                  {editingCustomer
                    ? "Edit Customer"
                    : "Add Customer"}
                </h3>
              </div>

              <button
                className="modal-close"
                onClick={closeForm}
                disabled={saving}
              >
                ×
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="customer-form-grid">
                <div className="form-field">
                  <label htmlFor="customer_code">
                    Customer Code
                  </label>

                  <input
                    id="customer_code"
                    name="customer_code"
                    value={form.customer_code}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className="form-field">
                  <label htmlFor="name">Name</label>

                  <input
                    id="name"
                    name="name"
                    value={form.name}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className="form-field">
                  <label htmlFor="email">Email</label>

                  <input
                    id="email"
                    name="email"
                    type="email"
                    value={form.email}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className="form-field">
                  <label htmlFor="phone">Phone</label>

                  <input
                    id="phone"
                    name="phone"
                    value={form.phone}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className="form-field full-width">
                  <label htmlFor="address">Address</label>

                  <input
                    id="address"
                    name="address"
                    value={form.address}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className="form-field">
                  <label htmlFor="city">City</label>

                  <input
                    id="city"
                    name="city"
                    value={form.city}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className="form-field">
                  <label htmlFor="state">State</label>

                  <input
                    id="state"
                    name="state"
                    value={form.state}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="cancel-button"
                  onClick={closeForm}
                  disabled={saving}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="primary-button"
                  disabled={saving}
                >
                  {saving
                    ? "Saving..."
                    : editingCustomer
                      ? "Update Customer"
                      : "Create Customer"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  );
}

export default Customers;