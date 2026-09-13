import React, { useEffect, useMemo, useState } from "react";
import api from "./api/client";
import "./Payments.css";

const formatDate = (value) => {
  if (!value) return "-";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return String(value);

  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
};

const formatDateTime = (value) => {
  if (!value) return "-";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return String(value);

  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const findField = (payment, possibleNames) => {
  const key = Object.keys(payment || {}).find((key) =>
    possibleNames.includes(key.toLowerCase())
  );

  return key ? payment[key] : null;
};

const getAmount = (payment) => {
  const value = findField(payment, [
    "amount",
    "payment_amount",
    "paid_amount",
    "total_amount",
  ]);

  const number = Number(value);

  return Number.isFinite(number) ? number : 0;
};

const getStatus = (payment) => {
  return (
    findField(payment, [
      "status",
      "payment_status",
      "state",
    ]) || "-"
  );
};

const getOrder = (payment) => {
  return (
    findField(payment, [
      "order_number",
      "order",
      "order_no",
    ]) ||
    (payment.order_id
      ? `Order #${payment.order_id}`
      : "-")
  );
};

const getPaymentDate = (payment) => {
  return findField(payment, [
    "payment_date",
    "paid_date",
    "transaction_date",
    "date",
  ]);
};

const getPaymentMethod = (payment) => {
  return (
    findField(payment, [
      "payment_method",
      "method",
      "mode",
    ]) || "-"
  );
};

const getStatusClass = (status) => {
  const normalized = String(status)
    .toUpperCase()
    .replaceAll(" ", "_");

  if (
    normalized.includes("PAID") ||
    normalized.includes("COMPLETED") ||
    normalized.includes("SUCCESS")
  ) {
    return "payment-status completed";
  }

  if (
    normalized.includes("PENDING") ||
    normalized.includes("PARTIAL")
  ) {
    return "payment-status pending";
  }

  if (
    normalized.includes("FAILED") ||
    normalized.includes("CANCEL")
  ) {
    return "payment-status failed";
  }

  return "payment-status neutral";
};

const isDateField = (key) => {
  return [
    "created_at",
    "updated_at",
    "payment_date",
    "paid_date",
    "transaction_date",
    "date",
  ].includes(key.toLowerCase());
};

export default function Payments() {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState("");
  const [error, setError] = useState("");

  const [selectedPayment, setSelectedPayment] =
    useState(null);

  const loadPayments = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get("/payments/");

      setPayments(
        Array.isArray(response.data)
          ? response.data
          : []
      );
    } catch (err) {
      console.error(err);

      setError(
        err.response?.data?.detail ||
          "Unable to load payments."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPayments();
  }, []);

  const filteredPayments = useMemo(() => {
    const value = search.trim().toLowerCase();

    if (!value) return payments;

    return payments.filter((payment) =>
      Object.values(payment || {}).some((field) =>
        String(field ?? "")
          .toLowerCase()
          .includes(value)
      )
    );
  }, [payments, search]);

  const totalAmount = payments.reduce(
    (sum, payment) => sum + getAmount(payment),
    0
  );

  const completedCount = payments.filter((payment) => {
    const status = String(getStatus(payment)).toUpperCase();

    return (
      status.includes("PAID") ||
      status.includes("COMPLETED") ||
      status.includes("SUCCESS")
    );
  }).length;

  const pendingCount = payments.filter((payment) => {
    const status = String(getStatus(payment)).toUpperCase();

    return (
      status.includes("PENDING") ||
      status.includes("PARTIAL")
    );
  }).length;

  const formatAmount = (amount) => {
    return amount.toLocaleString("en-IN", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  };

  const viewPayment = async (payment) => {
    try {
      setError("");

      const response = await api.get(
        `/payments/${payment.id}`
      );

      setSelectedPayment(response.data);
    } catch (err) {
      console.error(err);

      setSelectedPayment(payment);
    }
  };

  return (
    <div className="payments-page">

      {/* HEADER */}
      <div className="payments-header">
        <div>
          <h1>Payments</h1>

          <p>
            Monitor payment records and financial
            transactions.
          </p>
        </div>
      </div>

      {/* ERROR */}
      {error && (
        <div className="payments-error">
          {error}
        </div>
      )}

      {/* STATS */}
      <div className="payments-stats">

        <div className="payment-stat-card">
          <span>Total Payments</span>
          <strong>{payments.length}</strong>
        </div>

        <div className="payment-stat-card">
          <span>Total Amount</span>
          <strong>
            ₹{formatAmount(totalAmount)}
          </strong>
        </div>

        <div className="payment-stat-card">
          <span>Completed</span>
          <strong>{completedCount}</strong>
        </div>

        <div className="payment-stat-card">
          <span>Pending</span>
          <strong>{pendingCount}</strong>
        </div>

      </div>

      {/* TOOLBAR */}
      <div className="payments-toolbar">

        <div className="payments-search">
          <span>⌕</span>

          <input
            type="text"
            placeholder="Search payments..."
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
          />
        </div>

        <button
          className="payments-refresh-btn"
          onClick={loadPayments}
          disabled={loading}
        >
          ↻ Refresh
        </button>

      </div>

      {/* TABLE */}
      <div className="payments-table-card">

        <div className="payments-table-wrapper">

          <table className="payments-table">

            <thead>
              <tr>
                <th>ID</th>
                <th>Order</th>
                <th>Amount</th>
                <th>Payment Date</th>
                <th>Payment Method</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>

              {loading ? (
                <tr>
                  <td
                    colSpan="7"
                    className="payments-empty"
                  >
                    Loading payments...
                  </td>
                </tr>
              ) : filteredPayments.length === 0 ? (
                <tr>
                  <td
                    colSpan="7"
                    className="payments-empty"
                  >
                    No payments found.
                  </td>
                </tr>
              ) : (
                filteredPayments.map((payment) => {

                  const status =
                    getStatus(payment);

                  return (
                    <tr key={payment.id}>

                      <td>
                        #{payment.id}
                      </td>

                      <td>
                        <strong>
                          {getOrder(payment)}
                        </strong>
                      </td>

                      <td>
                        ₹
                        {formatAmount(
                          getAmount(payment)
                        )}
                      </td>

                      <td>
                        {formatDate(
                          getPaymentDate(payment)
                        )}
                      </td>

                      <td>
                        {getPaymentMethod(payment)}
                      </td>

                      <td>
                        <span
                          className={getStatusClass(
                            status
                          )}
                        >
                          {status}
                        </span>
                      </td>

                      <td>
                        <button
                          className="payment-view-btn"
                          onClick={() =>
                            viewPayment(payment)
                          }
                        >
                          View
                        </button>
                      </td>

                    </tr>
                  );
                })
              )}

            </tbody>

          </table>

        </div>

      </div>

      {/* DETAILS MODAL */}
      {selectedPayment && (
        <div
          className="payment-modal-overlay"
          onMouseDown={() =>
            setSelectedPayment(null)
          }
        >

          <div
            className="payment-details-modal"
            onMouseDown={(event) =>
              event.stopPropagation()
            }
          >

            <div className="payment-modal-header">

              <div>
                <h2>Payment Details</h2>

                <p>
                  Payment #
                  {selectedPayment.id}
                </p>
              </div>

              <button
                className="payment-close-btn"
                onClick={() =>
                  setSelectedPayment(null)
                }
              >
                ×
              </button>

            </div>

            <div className="payment-details-grid">

              {Object.entries(
                selectedPayment
              ).map(([key, value]) => {

                let displayValue = value;

                if (
                  value === null ||
                  value === undefined ||
                  value === ""
                ) {
                  displayValue = "-";
                } else if (
                  isDateField(key)
                ) {
                  displayValue =
                    formatDateTime(value);
                } else if (
                  typeof value === "object"
                ) {
                  displayValue =
                    JSON.stringify(value);
                }

                return (
                  <div
                    key={key}
                    className={
                      key === "notes" ||
                      key === "description"
                        ? "payment-detail-full"
                        : ""
                    }
                  >
                    <span>
                      {key
                        .replaceAll("_", " ")
                        .replace(
                          /\b\w/g,
                          (letter) =>
                            letter.toUpperCase()
                        )}
                    </span>

                    <strong>
                      {String(displayValue)}
                    </strong>
                  </div>
                );
              })}

            </div>

          </div>

        </div>
      )}

    </div>
  );
}