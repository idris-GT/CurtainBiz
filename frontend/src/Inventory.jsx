import { useEffect, useMemo, useState } from "react";
import api from "./api/client";
import "./Inventory.css";

function Inventory() {
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  const [editingItem, setEditingItem] = useState(null);

  const [form, setForm] = useState({
    material_id: "",
    quantity_available: "",
    reserved_quantity: "",
    location: "",
  });

  const loadInventory = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get("/inventory/");
      setInventory(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      console.error("Inventory loading error:", err);

      if (err.response?.status === 401) {
        setError("Authentication required. Please log in again.");
      } else {
        setError(
          err.response?.data?.detail ||
            "Unable to load inventory."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInventory();
  }, []);

  const filteredInventory = useMemo(() => {
    const value = search.trim().toLowerCase();

    if (!value) {
      return inventory;
    }

    return inventory.filter((item) => {
      return (
        String(item.material || "")
          .toLowerCase()
          .includes(value) ||
        String(item.material_code || "")
          .toLowerCase()
          .includes(value) ||
        String(item.location || "")
          .toLowerCase()
          .includes(value)
      );
    });
  }, [inventory, search]);

  const getStockStatus = (item) => {
    const available = Number(item.quantity_available || 0);
    const reserved = Number(item.reserved_quantity || 0);
    const usable = available - reserved;

    if (usable <= 0) {
      return {
        label: "OUT OF STOCK",
        className: "inventory-status out",
      };
    }

    if (usable <= 20) {
      return {
        label: "LOW STOCK",
        className: "inventory-status low",
      };
    }

    return {
      label: "IN STOCK",
      className: "inventory-status good",
    };
  };

  const openEdit = (item) => {
    setEditingItem(item);

    setForm({
      material_id: item.material_id ?? "",
      quantity_available: item.quantity_available ?? "",
      reserved_quantity: item.reserved_quantity ?? "",
      location: item.location ?? "",
    });
  };

  const closeEdit = () => {
    if (saving) return;

    setEditingItem(null);

    setForm({
      material_id: "",
      quantity_available: "",
      reserved_quantity: "",
      location: "",
    });
  };

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const handleUpdate = async (event) => {
    event.preventDefault();

    if (!editingItem) return;

    try {
      setSaving(true);
      setError("");

      const payload = {
        material_id: Number(form.material_id),
        quantity_available: Number(form.quantity_available),
        reserved_quantity: Number(form.reserved_quantity),
        location: form.location.trim(),
      };

      if (!payload.material_id) {
        setError("Material ID is required.");
        return;
      }

      if (payload.quantity_available < 0) {
        setError("Available quantity cannot be negative.");
        return;
      }

      if (payload.reserved_quantity < 0) {
        setError("Reserved quantity cannot be negative.");
        return;
      }

      if (payload.reserved_quantity > payload.quantity_available) {
        setError(
          "Reserved quantity cannot be greater than available quantity."
        );
        return;
      }

      if (!payload.location) {
        setError("Location is required.");
        return;
      }

      await api.put(
        `/inventory/${editingItem.id}`,
        payload
      );

      await loadInventory();
      closeEdit();
    } catch (err) {
      console.error("Inventory update error:", err);

      if (err.response?.status === 401) {
        setError("Authentication required. Please log in again.");
      } else {
        setError(
          err.response?.data?.detail ||
            "Unable to update inventory."
        );
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="inventory-page">
      <div className="inventory-header">
        <div>
          <p className="inventory-eyebrow">
            INVENTORY MANAGEMENT
          </p>

          <h1>Inventory</h1>

          <p>
            Monitor material stock, reservations and warehouse
            locations.
          </p>
        </div>
      </div>

      {error && (
        <div className="inventory-error">
          <strong>Something went wrong</strong>
          <span>{error}</span>

          <button
            type="button"
            onClick={loadInventory}
          >
            Try Again
          </button>
        </div>
      )}

      <div className="inventory-toolbar">
        <div className="inventory-count">
          <strong>{inventory.length}</strong>
          <span>inventory items</span>
        </div>

        <div className="inventory-search">
          <span>⌕</span>

          <input
            type="text"
            placeholder="Search inventory..."
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
          />
        </div>

        <button
          type="button"
          className="inventory-refresh"
          onClick={loadInventory}
          disabled={loading}
        >
          ↻ Refresh
        </button>
      </div>

      <div className="inventory-table-card">
        <div className="inventory-table-wrapper">
          <table className="inventory-table">
            <thead>
              <tr>
                <th>MATERIAL</th>
                <th>CODE</th>
                <th>AVAILABLE</th>
                <th>RESERVED</th>
                <th>USABLE</th>
                <th>LOCATION</th>
                <th>STATUS</th>
                <th>ACTIONS</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td
                    colSpan="8"
                    className="inventory-empty"
                  >
                    Loading inventory...
                  </td>
                </tr>
              ) : filteredInventory.length === 0 ? (
                <tr>
                  <td
                    colSpan="8"
                    className="inventory-empty"
                  >
                    {search
                      ? "No inventory matches your search."
                      : "No inventory found."}
                  </td>
                </tr>
              ) : (
                filteredInventory.map((item) => {
                  const available = Number(
                    item.quantity_available || 0
                  );

                  const reserved = Number(
                    item.reserved_quantity || 0
                  );

                  const usable = available - reserved;

                  const status = getStockStatus(item);

                  return (
                    <tr key={item.id}>
                      <td>
                        <div className="inventory-material">
                          <div className="inventory-avatar">
                            {String(
                              item.material || "M"
                            )
                              .charAt(0)
                              .toUpperCase()}
                          </div>

                          <div>
                            <strong>
                              {item.material || "Unknown Material"}
                            </strong>

                            <span>
                              Material ID: {item.material_id}
                            </span>
                          </div>
                        </div>
                      </td>

                      <td>
                        <span className="inventory-code">
                          {item.material_code || "-"}
                        </span>
                      </td>

                      <td>
                        <strong className="quantity-value">
                          {available}
                        </strong>
                      </td>

                      <td>
                        {reserved}
                      </td>

                      <td>
                        <strong
                          className={
                            usable <= 0
                              ? "usable-danger"
                              : usable <= 20
                              ? "usable-warning"
                              : "usable-good"
                          }
                        >
                          {usable}
                        </strong>
                      </td>

                      <td>
                        {item.location || "-"}
                      </td>

                      <td>
                        <span className={status.className}>
                          {status.label}
                        </span>
                      </td>

                      <td>
                        <button
                          type="button"
                          className="inventory-edit-button"
                          onClick={() =>
                            openEdit(item)
                          }
                        >
                          Edit
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

      {editingItem && (
        <div
          className="inventory-modal-overlay"
          onMouseDown={(event) => {
            if (
              event.target === event.currentTarget
            ) {
              closeEdit();
            }
          }}
        >
          <div className="inventory-modal">
            <div className="inventory-modal-header">
              <div>
                <p>UPDATE INVENTORY</p>

                <h2>Edit Inventory</h2>
              </div>

              <button
                type="button"
                className="inventory-close-button"
                onClick={closeEdit}
                disabled={saving}
              >
                ×
              </button>
            </div>

            <form onSubmit={handleUpdate}>
              <div className="inventory-form-grid">
                <div className="inventory-field">
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

                <div className="inventory-field">
                  <label>Material</label>

                  <input
                    type="text"
                    value={
                      editingItem.material || ""
                    }
                    disabled
                  />
                </div>

                <div className="inventory-field">
                  <label>Available Quantity</label>

                  <input
                    type="number"
                    name="quantity_available"
                    value={
                      form.quantity_available
                    }
                    onChange={handleChange}
                    min="0"
                    required
                  />
                </div>

                <div className="inventory-field">
                  <label>Reserved Quantity</label>

                  <input
                    type="number"
                    name="reserved_quantity"
                    value={
                      form.reserved_quantity
                    }
                    onChange={handleChange}
                    min="0"
                    required
                  />
                </div>

                <div className="inventory-field inventory-full">
                  <label>Location</label>

                  <input
                    type="text"
                    name="location"
                    value={form.location}
                    onChange={handleChange}
                    placeholder="e.g. Main Warehouse"
                    required
                  />
                </div>
              </div>

              <div className="inventory-modal-footer">
                <button
                  type="button"
                  className="inventory-cancel-button"
                  onClick={closeEdit}
                  disabled={saving}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="inventory-save-button"
                  disabled={saving}
                >
                  {saving
                    ? "Saving..."
                    : "Save Changes"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default Inventory;