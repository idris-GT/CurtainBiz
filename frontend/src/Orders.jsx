import { useEffect, useMemo, useState } from "react";
import api from "./api/client";
import "./Orders.css";

const STATUS_OPTIONS = [
  "NEW",
  "CONFIRMED",
  "IN_PRODUCTION",
  "QUALITY_CHECK",
  "READY",
  "DELIVERED",
  "CANCELLED",
];

function getArray(data) {
  if (Array.isArray(data)) return data;

  if (Array.isArray(data?.items)) return data.items;

  if (Array.isArray(data?.data)) return data.data;

  return [];
}

function decodeJwtPayload(token) {
  try {
    const payload = token.split(".")[1];

    if (!payload) return null;

    const normalized = payload
      .replace(/-/g, "+")
      .replace(/_/g, "/");

    const decoded = decodeURIComponent(
      atob(normalized)
        .split("")
        .map(
          (char) =>
            "%" + ("00" + char.charCodeAt(0).toString(16)).slice(-2)
        )
        .join("")
    );

    return JSON.parse(decoded);
  } catch (error) {
    console.error("Unable to decode access token:", error);
    return null;
  }
}

function getCurrentUserId() {
  const token = localStorage.getItem("access_token");

  if (!token) return "";

  const payload = decodeJwtPayload(token);

  return payload?.sub || payload?.user_id || "";
}

function formatDate(dateValue) {
  if (!dateValue) return "-";

  const date = new Date(`${dateValue}T00:00:00`);

  if (Number.isNaN(date.getTime())) return dateValue;

  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function formatCurrency(value) {
  const amount = Number(value || 0);

  return `₹${amount.toLocaleString("en-IN", {
    maximumFractionDigits: 2,
  })}`;
}

function getStatusClass(status) {
  const value = String(status || "").toUpperCase();

  if (value === "NEW") return "order-status new";
  if (value === "CONFIRMED") return "order-status confirmed";
  if (value === "IN_PRODUCTION") return "order-status production";
  if (value === "QUALITY_CHECK") return "order-status quality";
  if (value === "READY") return "order-status ready";
  if (value === "DELIVERED") return "order-status delivered";
  if (value === "CANCELLED") return "order-status cancelled";

  return "order-status";
}

function Orders() {
  const [orders, setOrders] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [quotations, setQuotations] = useState([]);

  const [loading, setLoading] = useState(true);
  const [loadingFormData, setLoadingFormData] = useState(false);
  const [saving, setSaving] = useState(false);

  const [search, setSearch] = useState("");
  const [error, setError] = useState("");

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);

  const [form, setForm] = useState({
    order_number: "",
    customer_id: "",
    quotation_id: "",
    order_date: new Date().toISOString().split("T")[0],
    expected_delivery_date: "",
    status: "NEW",
    subtotal: "",
    tax_amount: "",
    notes: "",
  });

  const loadOrders = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get("/orders/");
      setOrders(getArray(response.data));
    } catch (err) {
      console.error("Orders loading error:", err);

      if (err.response?.status === 401) {
        setError("Authentication required. Please log in again.");
      } else {
        setError(
          err.response?.data?.detail ||
            "Unable to load orders."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  const loadFormData = async () => {
    try {
      setLoadingFormData(true);

      const [customersResponse, quotationsResponse] =
        await Promise.all([
          api.get("/customers/"),
          api.get("/quotations/"),
        ]);

      setCustomers(getArray(customersResponse.data));
      setQuotations(getArray(quotationsResponse.data));
    } catch (err) {
      console.error("Order form data loading error:", err);

      if (err.response?.status === 401) {
        setError("Authentication required. Please log in again.");
      } else {
        setError(
          err.response?.data?.detail ||
            "Unable to load customers or quotations."
        );
      }
    } finally {
      setLoadingFormData(false);
    }
  };

  useEffect(() => {
    loadOrders();
  }, []);

  const filteredOrders = useMemo(() => {
    const value = search.trim().toLowerCase();

    if (!value) return orders;

    return orders.filter((order) => {
      return (
        String(order.order_number || "")
          .toLowerCase()
          .includes(value) ||
        String(order.customer || "")
          .toLowerCase()
          .includes(value) ||
        String(order.customer_id || "")
          .toLowerCase()
          .includes(value) ||
        String(order.quotation_number || "")
          .toLowerCase()
          .includes(value) ||
        String(order.status || "")
          .toLowerCase()
          .includes(value)
      );
    });
  }, [orders, search]);

  const totalOrderValue = useMemo(() => {
    return orders.reduce(
      (sum, order) => sum + Number(order.total_amount || 0),
      0
    );
  }, [orders]);

  const activeOrders = useMemo(() => {
    return orders.filter(
      (order) =>
        !["DELIVERED", "CANCELLED"].includes(
          String(order.status || "").toUpperCase()
        )
    ).length;
  }, [orders]);

  const generateOrderNumber = () => {
    const year = new Date().getFullYear();

    const numbers = orders
      .map((order) => {
        const match = String(order.order_number || "").match(
          /(\d+)$/
        );

        return match ? Number(match[1]) : 0;
      })
      .filter((number) => number > 0);

    const nextNumber =
      numbers.length > 0 ? Math.max(...numbers) + 1 : orders.length + 1;

    return `ORD-${year}-${String(nextNumber).padStart(3, "0")}`;
  };

  const openCreateModal = async () => {
    setError("");

    setForm({
      order_number: generateOrderNumber(),
      customer_id: "",
      quotation_id: "",
      order_date: new Date().toISOString().split("T")[0],
      expected_delivery_date: "",
      status: "NEW",
      subtotal: "",
      tax_amount: "",
      notes: "",
    });

    setShowCreateModal(true);

    if (customers.length === 0 || quotations.length === 0) {
      await loadFormData();
    }
  };

  const closeCreateModal = () => {
    if (saving) return;

    setShowCreateModal(false);
  };

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const subtotalValue = Number(form.subtotal || 0);
  const taxValue = Number(form.tax_amount || 0);
  const totalValue = subtotalValue + taxValue;

  const handleCreateOrder = async (event) => {
    event.preventDefault();

    try {
      setSaving(true);
      setError("");

      const createdBy = getCurrentUserId();

      if (!createdBy) {
        setError(
          "Unable to identify the logged-in user. Please log in again."
        );
        return;
      }

      if (!form.order_number.trim()) {
        setError("Order number is required.");
        return;
      }

      if (!form.customer_id) {
        setError("Please select a customer.");
        return;
      }

      if (!form.quotation_id) {
        setError("Please select a quotation.");
        return;
      }

      if (!form.order_date) {
        setError("Order date is required.");
        return;
      }

      if (!form.expected_delivery_date) {
        setError("Expected delivery date is required.");
        return;
      }

      if (form.expected_delivery_date < form.order_date) {
        setError(
          "Expected delivery date cannot be before the order date."
        );
        return;
      }

      if (subtotalValue < 0) {
        setError("Subtotal cannot be negative.");
        return;
      }

      if (taxValue < 0) {
        setError("Tax amount cannot be negative.");
        return;
      }

      const payload = {
        order_number: form.order_number.trim(),
        customer_id: Number(form.customer_id),
        quotation_id: Number(form.quotation_id),
        created_by: createdBy,
        order_date: form.order_date,
        expected_delivery_date: form.expected_delivery_date,
        status: form.status,
        subtotal: subtotalValue,
        tax_amount: taxValue,
        total_amount: totalValue,
        notes: form.notes.trim(),
      };

      await api.post("/orders/", payload);

      await loadOrders();

      setShowCreateModal(false);
    } catch (err) {
      console.error("Order creation error:", err);

      if (err.response?.status === 401) {
        setError("Authentication required. Please log in again.");
      } else {
        const detail = err.response?.data?.detail;

        if (Array.isArray(detail)) {
          setError(
            detail
              .map((item) => item.msg)
              .filter(Boolean)
              .join(" ")
          );
        } else {
          setError(detail || "Unable to create order.");
        }
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="orders-page">
      <div className="orders-header">
        <div>
          <p className="orders-eyebrow">SALES MANAGEMENT</p>
          <h1>Orders</h1>
          <p>
            Manage customer orders and track their progress from confirmation
            to delivery.
          </p>
        </div>

        <button
          type="button"
          className="orders-primary-button"
          onClick={openCreateModal}
        >
          + New Order
        </button>
      </div>

      {error && (
        <div className="orders-error">
          <div>
            <strong>Something went wrong</strong>
            <span>{error}</span>
          </div>

          <button
            type="button"
            onClick={() => setError("")}
          >
            ×
          </button>
        </div>
      )}

      <div className="orders-summary">
        <div className="orders-summary-card">
          <span>Total Orders</span>
          <strong>{orders.length}</strong>
        </div>

        <div className="orders-summary-card">
          <span>Active Orders</span>
          <strong>{activeOrders}</strong>
        </div>

        <div className="orders-summary-card">
          <span>Total Order Value</span>
          <strong>{formatCurrency(totalOrderValue)}</strong>
        </div>
      </div>

      <div className="orders-toolbar">
        <div className="orders-count">
          <strong>{filteredOrders.length}</strong>
          <span>
            {search ? "matching orders" : "orders"}
          </span>
        </div>

        <div className="orders-search">
          <span>⌕</span>

          <input
            type="text"
            placeholder="Search orders..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>

        <button
          type="button"
          className="orders-refresh-button"
          onClick={loadOrders}
          disabled={loading}
        >
          ↻ Refresh
        </button>
      </div>

      <div className="orders-table-card">
        <div className="orders-table-wrapper">
          <table className="orders-table">
            <thead>
              <tr>
                <th>ORDER</th>
                <th>CUSTOMER</th>
                <th>QUOTATION</th>
                <th>ORDER DATE</th>
                <th>DELIVERY</th>
                <th>STATUS</th>
                <th>TOTAL</th>
                <th>ACTION</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td
                    colSpan="8"
                    className="orders-empty"
                  >
                    Loading orders...
                  </td>
                </tr>
              ) : filteredOrders.length === 0 ? (
                <tr>
                  <td
                    colSpan="8"
                    className="orders-empty"
                  >
                    {search
                      ? "No orders match your search."
                      : "No orders found."}
                  </td>
                </tr>
              ) : (
                filteredOrders.map((order) => (
                  <tr key={order.id}>
                    <td>
                      <div className="order-number-cell">
                        <strong>
                          {order.order_number || "-"}
                        </strong>

                        <span>
                          Order ID: {order.id}
                        </span>
                      </div>
                    </td>

                    <td>
                      <div className="order-customer-cell">
                        <strong>
                          {order.customer || "Unknown Customer"}
                        </strong>

                        <span>
                          Customer ID: {order.customer_id}
                        </span>
                      </div>
                    </td>

                    <td>
                      <span className="order-reference">
                        {order.quotation_number || "-"}
                      </span>
                    </td>

                    <td>
                      {formatDate(order.order_date)}
                    </td>

                    <td>
                      {formatDate(order.expected_delivery_date)}
                    </td>

                    <td>
                      <span
                        className={getStatusClass(
                          order.status
                        )}
                      >
                        {String(
                          order.status || "-"
                        ).replaceAll("_", " ")}
                      </span>
                    </td>

                    <td>
                      <strong className="order-total">
                        {formatCurrency(
                          order.total_amount
                        )}
                      </strong>
                    </td>

                    <td>
                      <button
                        type="button"
                        className="order-view-button"
                        onClick={() =>
                          setSelectedOrder(order)
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

      {showCreateModal && (
        <div
          className="orders-modal-overlay"
          onMouseDown={(event) => {
            if (
              event.target === event.currentTarget &&
              !saving
            ) {
              closeCreateModal();
            }
          }}
        >
          <div className="orders-modal">
            <div className="orders-modal-header">
              <div>
                <p>SALES ORDER</p>
                <h2>New Order</h2>
              </div>

              <button
                type="button"
                className="orders-close-button"
                onClick={closeCreateModal}
                disabled={saving}
              >
                ×
              </button>
            </div>

            <form onSubmit={handleCreateOrder}>
              <div className="orders-modal-body">
                {loadingFormData && (
                  <div className="orders-loading-form">
                    Loading customers and quotations...
                  </div>
                )}

                <div className="orders-form-grid">
                  <div className="orders-field">
                    <label>Order Number</label>

                    <input
                      type="text"
                      name="order_number"
                      value={form.order_number}
                      onChange={handleChange}
                      required
                    />
                  </div>

                  <div className="orders-field">
                    <label>Customer</label>

                    <select
                      name="customer_id"
                      value={form.customer_id}
                      onChange={handleChange}
                      required
                    >
                      <option value="">
                        Select customer
                      </option>

                      {customers.map((customer) => (
                        <option
                          key={customer.id}
                          value={customer.id}
                        >
                          {customer.name ||
                            customer.customer_name ||
                            `Customer #${customer.id}`}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="orders-field">
                    <label>Quotation</label>

                    <select
                      name="quotation_id"
                      value={form.quotation_id}
                      onChange={handleChange}
                      required
                    >
                      <option value="">
                        Select quotation
                      </option>

                      {quotations.map((quotation) => (
                        <option
                          key={quotation.id}
                          value={quotation.id}
                        >
                          {quotation.quotation_number ||
                            `Quotation #${quotation.id}`}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="orders-field">
                    <label>Status</label>

                    <select
                      name="status"
                      value={form.status}
                      onChange={handleChange}
                    >
                      {STATUS_OPTIONS.map((status) => (
                        <option
                          key={status}
                          value={status}
                        >
                          {status.replaceAll("_", " ")}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="orders-field">
                    <label>Order Date</label>

                    <input
                      type="date"
                      name="order_date"
                      value={form.order_date}
                      onChange={handleChange}
                      required
                    />
                  </div>

                  <div className="orders-field">
                    <label>Expected Delivery Date</label>

                    <input
                      type="date"
                      name="expected_delivery_date"
                      value={form.expected_delivery_date}
                      onChange={handleChange}
                      min={form.order_date}
                      required
                    />
                  </div>

                  <div className="orders-field">
                    <label>Subtotal</label>

                    <input
                      type="number"
                      name="subtotal"
                      value={form.subtotal}
                      onChange={handleChange}
                      min="0"
                      step="0.01"
                      placeholder="0"
                      required
                    />
                  </div>

                  <div className="orders-field">
                    <label>Tax Amount</label>

                    <input
                      type="number"
                      name="tax_amount"
                      value={form.tax_amount}
                      onChange={handleChange}
                      min="0"
                      step="0.01"
                      placeholder="0"
                      required
                    />
                  </div>

                  <div className="orders-field orders-full-field">
                    <label>Notes</label>

                    <textarea
                      name="notes"
                      value={form.notes}
                      onChange={handleChange}
                      placeholder="Add order notes..."
                      rows="4"
                    />
                  </div>
                </div>

                <div className="orders-total-preview">
                  <span>Total Amount</span>
                  <strong>
                    {formatCurrency(totalValue)}
                  </strong>
                </div>
              </div>

              <div className="orders-modal-footer">
                <button
                  type="button"
                  className="orders-cancel-button"
                  onClick={closeCreateModal}
                  disabled={saving}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="orders-save-button"
                  disabled={saving || loadingFormData}
                >
                  {saving
                    ? "Creating..."
                    : "Create Order"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {selectedOrder && (
        <div
          className="orders-modal-overlay"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              setSelectedOrder(null);
            }
          }}
        >
          <div className="orders-detail-modal">
            <div className="orders-modal-header">
              <div>
                <p>ORDER DETAILS</p>
                <h2>
                  {selectedOrder.order_number}
                </h2>
              </div>

              <button
                type="button"
                className="orders-close-button"
                onClick={() =>
                  setSelectedOrder(null)
                }
              >
                ×
              </button>
            </div>

            <div className="orders-detail-body">
              <div className="orders-detail-grid">
                <div>
                  <span>Customer</span>
                  <strong>
                    {selectedOrder.customer || "-"}
                  </strong>
                </div>

                <div>
                  <span>Quotation</span>
                  <strong>
                    {selectedOrder.quotation_number ||
                      "-"}
                  </strong>
                </div>

                <div>
                  <span>Order Date</span>
                  <strong>
                    {formatDate(
                      selectedOrder.order_date
                    )}
                  </strong>
                </div>

                <div>
                  <span>Expected Delivery</span>
                  <strong>
                    {formatDate(
                      selectedOrder.expected_delivery_date
                    )}
                  </strong>
                </div>

                <div>
                  <span>Status</span>

                  <strong>
                    <span
                      className={getStatusClass(
                        selectedOrder.status
                      )}
                    >
                      {String(
                        selectedOrder.status || "-"
                      ).replaceAll("_", " ")}
                    </span>
                  </strong>
                </div>

                <div>
                  <span>Subtotal</span>
                  <strong>
                    {formatCurrency(
                      selectedOrder.subtotal
                    )}
                  </strong>
                </div>

                <div>
                  <span>Tax</span>
                  <strong>
                    {formatCurrency(
                      selectedOrder.tax_amount
                    )}
                  </strong>
                </div>

                <div>
                  <span>Total Amount</span>
                  <strong className="detail-total">
                    {formatCurrency(
                      selectedOrder.total_amount
                    )}
                  </strong>
                </div>
              </div>

              <div className="orders-detail-notes">
                <span>Notes</span>

                <p>
                  {selectedOrder.notes ||
                    "No notes added."}
                </p>
              </div>
            </div>

            <div className="orders-modal-footer">
              <button
                type="button"
                className="orders-cancel-button"
                onClick={() =>
                  setSelectedOrder(null)
                }
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Orders;