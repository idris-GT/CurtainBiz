import React, { useEffect, useMemo, useState } from "react";
import api from "./api/client";
import "./Deliveries.css";

const STATUS_OPTIONS = [
  "PENDING",
  "SCHEDULED",
  "OUT_FOR_DELIVERY",
  "DELIVERED",
  "FAILED",
];

const emptyForm = {
  order_id: "",
  delivery_address: "",
  scheduled_date: "",
  delivered_date: "",
  status: "PENDING",
  delivered_by: "",
  notes: "",
};

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
    case "DELIVERED":
      return "delivery-status delivered";

    case "OUT_FOR_DELIVERY":
      return "delivery-status out";

    case "SCHEDULED":
      return "delivery-status scheduled";

    case "FAILED":
      return "delivery-status failed";

    default:
      return "delivery-status pending";
  }
};

export default function Deliveries() {
  const [deliveries, setDeliveries] = useState([]);
  const [orders, setOrders] = useState([]);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [search, setSearch] = useState("");
  const [error, setError] = useState("");

  const [showCreate, setShowCreate] = useState(false);
  const [selectedDelivery, setSelectedDelivery] = useState(null);

  const [form, setForm] = useState(emptyForm);

  const loadDeliveries = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get("/deliveries/");

      setDeliveries(
        Array.isArray(response.data)
          ? response.data
          : []
      );
    } catch (err) {
      console.error(err);

      setError(
        err.response?.data?.detail ||
          "Unable to load deliveries."
      );
    } finally {
      setLoading(false);
    }
  };

  const loadOrders = async () => {
    try {
      const response = await api.get("/orders/");

      setOrders(
        Array.isArray(response.data)
          ? response.data
          : []
      );
    } catch (err) {
      console.error(err);

      setError(
        err.response?.data?.detail ||
          "Unable to load orders."
      );
    }
  };

  useEffect(() => {
    loadDeliveries();
    loadOrders();
  }, []);

  const filteredDeliveries = useMemo(() => {
    const value = search.trim().toLowerCase();

    if (!value) return deliveries;

    return deliveries.filter((delivery) => {
      return [
        delivery.id,
        delivery.order_id,
        delivery.order_number,
        delivery.delivery_address,
        delivery.status,
        delivery.delivered_by,
        delivery.notes,
        delivery.scheduled_date,
        delivery.delivered_date,
      ]
        .filter(Boolean)
        .some((field) =>
          String(field)
            .toLowerCase()
            .includes(value)
        );
    });
  }, [deliveries, search]);

  const totalDeliveries = deliveries.length;

  const scheduledCount = deliveries.filter(
    (delivery) => delivery.status === "SCHEDULED"
  ).length;

  const outForDeliveryCount = deliveries.filter(
    (delivery) => delivery.status === "OUT_FOR_DELIVERY"
  ).length;

  const deliveredCount = deliveries.filter(
    (delivery) => delivery.status === "DELIVERED"
  ).length;

  const handleInputChange = (event) => {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
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

  const handleCreateDelivery = async (event) => {
    event.preventDefault();

    if (!form.order_id) {
      setError("Please select an order.");
      return;
    }

    if (!form.delivery_address.trim()) {
      setError("Please enter the delivery address.");
      return;
    }

    if (!form.scheduled_date) {
      setError("Please select a scheduled date.");
      return;
    }

    try {
      setSaving(true);
      setError("");

      const payload = {
        order_id: Number(form.order_id),
        delivery_address:
          form.delivery_address.trim(),

        scheduled_date: form.scheduled_date,

        delivered_date:
          form.delivered_date || null,

        status: form.status,

        delivered_by:
          form.delivered_by.trim() || null,

        notes: form.notes.trim() || null,
      };

      await api.post("/deliveries/", payload);

      setShowCreate(false);
      setForm(emptyForm);

      await loadDeliveries();
    } catch (err) {
      console.error(err);

      setError(
        err.response?.data?.detail ||
          "Unable to create delivery."
      );
    } finally {
      setSaving(false);
    }
  };

  const viewDelivery = async (delivery) => {
    try {
      setError("");

      const response = await api.get(
        `/deliveries/${delivery.id}`
      );

      setSelectedDelivery(response.data);
    } catch (err) {
      console.error(err);

      setSelectedDelivery(delivery);
    }
  };

  return (
    <div className="deliveries-page">

      {/* HEADER */}
      <div className="deliveries-header">
        <div>
          <h1>Deliveries</h1>

          <p>
            Manage customer deliveries and monitor
            delivery progress.
          </p>
        </div>

        <button
          className="deliveries-primary-btn"
          onClick={openCreateModal}
        >
          + New Delivery
        </button>
      </div>

      {/* ERROR */}
      {error && (
        <div className="deliveries-error">
          {error}
        </div>
      )}

      {/* STATS */}
      <div className="deliveries-stats">

        <div className="delivery-stat-card">
          <span>Total Deliveries</span>
          <strong>{totalDeliveries}</strong>
        </div>

        <div className="delivery-stat-card">
          <span>Scheduled</span>
          <strong>{scheduledCount}</strong>
        </div>

        <div className="delivery-stat-card">
          <span>Out for Delivery</span>
          <strong>{outForDeliveryCount}</strong>
        </div>

        <div className="delivery-stat-card">
          <span>Delivered</span>
          <strong>{deliveredCount}</strong>
        </div>

      </div>

      {/* TOOLBAR */}
      <div className="deliveries-toolbar">

        <div className="deliveries-search">
          <span>⌕</span>

          <input
            type="text"
            placeholder="Search deliveries..."
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
          />
        </div>

        <button
          className="deliveries-refresh-btn"
          onClick={loadDeliveries}
          disabled={loading}
        >
          ↻ Refresh
        </button>

      </div>

      {/* TABLE */}
      <div className="deliveries-table-card">

        <div className="deliveries-table-wrapper">

          <table className="deliveries-table">

            <thead>
              <tr>
                <th>ID</th>
                <th>Order</th>
                <th>Delivery Address</th>
                <th>Scheduled Date</th>
                <th>Delivered Date</th>
                <th>Status</th>
                <th>Delivered By</th>
                <th>Notes</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>

              {loading ? (
                <tr>
                  <td
                    colSpan="9"
                    className="deliveries-empty"
                  >
                    Loading deliveries...
                  </td>
                </tr>
              ) : filteredDeliveries.length === 0 ? (
                <tr>
                  <td
                    colSpan="9"
                    className="deliveries-empty"
                  >
                    No deliveries found.
                  </td>
                </tr>
              ) : (
                filteredDeliveries.map((delivery) => (
                  <tr key={delivery.id}>

                    <td>
                      #{delivery.id}
                    </td>

                    <td>
                      <strong>
                        {delivery.order_number ||
                          `Order #${delivery.order_id}`}
                      </strong>
                    </td>

                    <td className="delivery-address">
                      {delivery.delivery_address ||
                        "-"}
                    </td>

                    <td>
                      {formatDate(
                        delivery.scheduled_date
                      )}
                    </td>

                    <td>
                      {formatDate(
                        delivery.delivered_date
                      )}
                    </td>

                    <td>
                      <span
                        className={getStatusClass(
                          delivery.status
                        )}
                      >
                        {delivery.status ||
                          "PENDING"}
                      </span>
                    </td>

                    <td>
                      {delivery.delivered_by ||
                        "-"}
                    </td>

                    <td className="delivery-notes">
                      {delivery.notes || "-"}
                    </td>

                    <td>
                      <button
                        className="delivery-view-btn"
                        onClick={() =>
                          viewDelivery(delivery)
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

      {/* CREATE MODAL */}
      {showCreate && (
        <div
          className="delivery-modal-overlay"
          onMouseDown={closeCreateModal}
        >

          <div
            className="delivery-modal"
            onMouseDown={(event) =>
              event.stopPropagation()
            }
          >

            <div className="delivery-modal-header">

              <div>
                <h2>New Delivery</h2>

                <p>
                  Create a delivery record for an order.
                </p>
              </div>

              <button
                className="delivery-close-btn"
                onClick={closeCreateModal}
                disabled={saving}
              >
                ×
              </button>

            </div>

            <form
              onSubmit={handleCreateDelivery}
            >

              <div className="delivery-form-grid">

                <div className="delivery-form-group">
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

                <div className="delivery-form-group">
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

                <div className="delivery-form-group full-width">
                  <label>
                    Delivery Address *
                  </label>

                  <input
                    type="text"
                    name="delivery_address"
                    value={
                      form.delivery_address
                    }
                    onChange={handleInputChange}
                    placeholder="Enter delivery address"
                  />
                </div>

                <div className="delivery-form-group">
                  <label>
                    Scheduled Date *
                  </label>

                  <input
                    type="date"
                    name="scheduled_date"
                    value={
                      form.scheduled_date
                    }
                    onChange={handleInputChange}
                  />
                </div>

                <div className="delivery-form-group">
                  <label>
                    Delivered Date
                  </label>

                  <input
                    type="date"
                    name="delivered_date"
                    value={
                      form.delivered_date
                    }
                    onChange={handleInputChange}
                  />
                </div>

                <div className="delivery-form-group full-width">
                  <label>
                    Delivered By
                  </label>

                  <input
                    type="text"
                    name="delivered_by"
                    value={
                      form.delivered_by
                    }
                    onChange={handleInputChange}
                    placeholder="Enter user UUID"
                  />

                  <small>
                    Leave empty if delivery has not
                    been assigned/completed.
                  </small>
                </div>

                <div className="delivery-form-group full-width">
                  <label>Notes</label>

                  <textarea
                    name="notes"
                    value={form.notes}
                    onChange={handleInputChange}
                    placeholder="Enter delivery notes..."
                    rows="4"
                  />
                </div>

              </div>

              <div className="delivery-modal-actions">

                <button
                  type="button"
                  className="delivery-cancel-btn"
                  onClick={closeCreateModal}
                  disabled={saving}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="delivery-save-btn"
                  disabled={saving}
                >
                  {saving
                    ? "Creating..."
                    : "Create Delivery"}
                </button>

              </div>

            </form>

          </div>

        </div>
      )}

      {/* DETAILS MODAL */}
      {selectedDelivery && (
        <div
          className="delivery-modal-overlay"
          onMouseDown={() =>
            setSelectedDelivery(null)
          }
        >

          <div
            className="delivery-details-modal"
            onMouseDown={(event) =>
              event.stopPropagation()
            }
          >

            <div className="delivery-modal-header">

              <div>
                <h2>Delivery Details</h2>

                <p>
                  Delivery #{selectedDelivery.id}
                </p>
              </div>

              <button
                className="delivery-close-btn"
                onClick={() =>
                  setSelectedDelivery(null)
                }
              >
                ×
              </button>

            </div>

            <div className="delivery-details-grid">

              <div>
                <span>Delivery ID</span>
                <strong>
                  #{selectedDelivery.id}
                </strong>
              </div>

              <div>
                <span>Order</span>
                <strong>
                  {selectedDelivery.order_number ||
                    `Order #${selectedDelivery.order_id}`}
                </strong>
              </div>

              <div className="details-full">
                <span>Delivery Address</span>
                <strong>
                  {selectedDelivery.delivery_address ||
                    "-"}
                </strong>
              </div>

              <div>
                <span>Scheduled Date</span>
                <strong>
                  {formatDate(
                    selectedDelivery.scheduled_date
                  )}
                </strong>
              </div>

              <div>
                <span>Delivered Date</span>
                <strong>
                  {formatDate(
                    selectedDelivery.delivered_date
                  )}
                </strong>
              </div>

              <div>
                <span>Status</span>

                <strong>
                  <span
                    className={getStatusClass(
                      selectedDelivery.status
                    )}
                  >
                    {selectedDelivery.status ||
                      "PENDING"}
                  </span>
                </strong>
              </div>

              <div>
                <span>Delivered By</span>
                <strong>
                  {selectedDelivery.delivered_by ||
                    "-"}
                </strong>
              </div>

              <div>
                <span>Created At</span>
                <strong>
                  {formatDateTime(
                    selectedDelivery.created_at
                  )}
                </strong>
              </div>

              <div>
                <span>Updated At</span>
                <strong>
                  {formatDateTime(
                    selectedDelivery.updated_at
                  )}
                </strong>
              </div>

              <div className="details-full">
                <span>Notes</span>
                <strong>
                  {selectedDelivery.notes || "-"}
                </strong>
              </div>

            </div>

          </div>

        </div>
      )}

    </div>
  );
}