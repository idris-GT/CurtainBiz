import { useEffect, useMemo, useState } from "react";
import api from "./api/client";
import "./StockTransactions.css";

function getCurrentUserId() {
  try {
    const token = localStorage.getItem("access_token");

    if (!token) return "";

    const payload = JSON.parse(atob(token.split(".")[1]));

    return payload.sub || "";
  } catch {
    return "";
  }
}

function StockTransactions() {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);

  const [form, setForm] = useState({
    material_id: "",
    transaction_type: "",
    quantity: "",
    reference_type: "",
    reference_id: "",
    notes: "",
  });

  const loadTransactions = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get("/stock-transactions/");

      setTransactions(
        Array.isArray(response.data) ? response.data : []
      );
    } catch (err) {
      console.error("Stock transactions loading error:", err);

      if (err.response?.status === 401) {
        setError("Authentication required. Please log in again.");
      } else {
        setError(
          err.response?.data?.detail ||
            "Unable to load stock transactions."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTransactions();
  }, []);

  const filteredTransactions = useMemo(() => {
    const value = search.trim().toLowerCase();

    if (!value) return transactions;

    return transactions.filter((item) => {
      return (
        String(item.material || "")
          .toLowerCase()
          .includes(value) ||
        String(item.material_code || "")
          .toLowerCase()
          .includes(value) ||
        String(item.transaction_type || "")
          .toLowerCase()
          .includes(value) ||
        String(item.reference_type || "")
          .toLowerCase()
          .includes(value) ||
        String(item.notes || "")
          .toLowerCase()
          .includes(value)
      );
    });
  }, [transactions, search]);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const closeCreate = () => {
    if (saving) return;

    setShowCreate(false);

    setForm({
      material_id: "",
      transaction_type: "",
      quantity: "",
      reference_type: "",
      reference_id: "",
      notes: "",
    });
  };

  const handleCreate = async (event) => {
    event.preventDefault();

    try {
      setSaving(true);
      setError("");

      const createdBy = getCurrentUserId();

      const payload = {
        material_id: Number(form.material_id),
        transaction_type: form.transaction_type.trim(),
        quantity: Number(form.quantity),
        reference_type: form.reference_type.trim() || null,
        reference_id: form.reference_id
          ? Number(form.reference_id)
          : null,
        notes: form.notes.trim() || null,
        created_by: createdBy,
      };

      if (!payload.material_id) {
        setError("Material ID is required.");
        return;
      }

      if (!payload.transaction_type) {
        setError("Transaction type is required.");
        return;
      }

      if (!payload.quantity || payload.quantity <= 0) {
        setError("Quantity must be greater than 0.");
        return;
      }

      if (!payload.created_by) {
        setError("User session not found. Please log in again.");
        return;
      }

      await api.post("/stock-transactions/", payload);

      await loadTransactions();
      closeCreate();
    } catch (err) {
      console.error("Stock transaction creation error:", err);

      if (err.response?.status === 401) {
        setError("Authentication required. Please log in again.");
      } else {
        setError(
          err.response?.data?.detail ||
            "Unable to create stock transaction."
        );
      }
    } finally {
      setSaving(false);
    }
  };

  const getTransactionClass = (type) => {
    const value = String(type || "").toLowerCase();

    if (
      value.includes("in") ||
      value.includes("receive") ||
      value.includes("add")
    ) {
      return "stock-transaction-type in";
    }

    if (
      value.includes("out") ||
      value.includes("issue") ||
      value.includes("remove")
    ) {
      return "stock-transaction-type out";
    }

    return "stock-transaction-type adjustment";
  };

  return (
    <div className="stock-transactions-page">
      <div className="stock-transactions-header">
        <div>
          <p className="stock-transactions-eyebrow">
            INVENTORY ACTIVITY
          </p>

          <h1>Stock Transactions</h1>

          <p>
            Record and monitor material stock movements and adjustments.
          </p>
        </div>

        <button
          type="button"
          className="stock-create-button"
          onClick={() => setShowCreate(true)}
        >
          + New Transaction
        </button>
      </div>

      {error && (
        <div className="stock-error">
          <strong>Something went wrong</strong>
          <span>{error}</span>

          <button type="button" onClick={loadTransactions}>
            Try Again
          </button>
        </div>
      )}

      <div className="stock-toolbar">
        <div className="stock-count">
          <strong>{transactions.length}</strong>
          <span>transactions</span>
        </div>

        <div className="stock-search">
          <span>⌕</span>

          <input
            type="text"
            placeholder="Search transactions..."
            value={search}
            onChange={handleChange}
            name="search"
          />
        </div>

        <button
          type="button"
          className="stock-refresh-button"
          onClick={loadTransactions}
          disabled={loading}
        >
          ↻ Refresh
        </button>
      </div>

      <div className="stock-table-card">
        <div className="stock-table-wrapper">
          <table className="stock-table">
            <thead>
              <tr>
                <th>MATERIAL</th>
                <th>TYPE</th>
                <th>QUANTITY</th>
                <th>REFERENCE</th>
                <th>NOTES</th>
                <th>CREATED BY</th>
                <th>DATE</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="7" className="stock-empty">
                    Loading transactions...
                  </td>
                </tr>
              ) : filteredTransactions.length === 0 ? (
                <tr>
                  <td colSpan="7" className="stock-empty">
                    {search
                      ? "No transactions match your search."
                      : "No stock transactions found."}
                  </td>
                </tr>
              ) : (
                filteredTransactions.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <div className="stock-material">
                        <div className="stock-avatar">
                          {String(
                            item.material ||
                              item.material_code ||
                              "M"
                          )
                            .charAt(0)
                            .toUpperCase()}
                        </div>

                        <div>
                          <strong>
                            {item.material ||
                              item.material_code ||
                              "Unknown Material"}
                          </strong>

                          <span>
                            Material ID: {item.material_id ?? "-"}
                          </span>
                        </div>
                      </div>
                    </td>

                    <td>
                      <span
                        className={getTransactionClass(
                          item.transaction_type
                        )}
                      >
                        {item.transaction_type || "-"}
                      </span>
                    </td>

                    <td>
                      <strong className="stock-quantity">
                        {item.quantity ?? "-"}
                      </strong>
                    </td>

                    <td>
                      <div className="stock-reference">
                        <strong>
                          {item.reference_type || "-"}
                        </strong>

                        {item.reference_id != null && (
                          <span>
                            ID: {item.reference_id}
                          </span>
                        )}
                      </div>
                    </td>

                    <td>{item.notes || "-"}</td>

                    <td>
                      <span className="stock-created-by">
                        {item.created_by || "-"}
                      </span>
                    </td>

                    <td>
                      {item.created_at
                        ? new Date(
                            item.created_at
                          ).toLocaleString()
                        : "-"}
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
          className="stock-modal-overlay"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              closeCreate();
            }
          }}
        >
          <div className="stock-modal">
            <div className="stock-modal-header">
              <div>
                <p>STOCK MOVEMENT</p>
                <h2>New Transaction</h2>
              </div>

              <button
                type="button"
                className="stock-close-button"
                onClick={closeCreate}
                disabled={saving}
              >
                ×
              </button>
            </div>

            <form onSubmit={handleCreate}>
              <div className="stock-form-grid">
                <div className="stock-field">
                  <label>Material ID</label>

                  <input
                    type="number"
                    name="material_id"
                    value={form.material_id}
                    onChange={handleChange}
                    min="1"
                    required
                  />
                </div>

                <div className="stock-field">
                  <label>Transaction Type</label>

                  <input
                    type="text"
                    name="transaction_type"
                    value={form.transaction_type}
                    onChange={handleChange}
                    placeholder="e.g. IN / OUT / ADJUSTMENT"
                    required
                  />
                </div>

                <div className="stock-field">
                  <label>Quantity</label>

                  <input
                    type="number"
                    name="quantity"
                    value={form.quantity}
                    onChange={handleChange}
                    min="1"
                    required
                  />
                </div>

                <div className="stock-field">
                  <label>Reference Type</label>

                  <input
                    type="text"
                    name="reference_type"
                    value={form.reference_type}
                    onChange={handleChange}
                    placeholder="e.g. PURCHASE / ORDER"
                  />
                </div>

                <div className="stock-field">
                  <label>Reference ID</label>

                  <input
                    type="number"
                    name="reference_id"
                    value={form.reference_id}
                    onChange={handleChange}
                    min="1"
                    placeholder="Optional"
                  />
                </div>

                <div className="stock-field stock-full">
                  <label>Notes</label>

                  <textarea
                    name="notes"
                    value={form.notes}
                    onChange={handleChange}
                    placeholder="Add transaction notes..."
                    rows="4"
                  />
                </div>
              </div>

              <div className="stock-modal-footer">
                <button
                  type="button"
                  className="stock-cancel-button"
                  onClick={closeCreate}
                  disabled={saving}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="stock-save-button"
                  disabled={saving}
                >
                  {saving ? "Creating..." : "Create Transaction"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default StockTransactions;