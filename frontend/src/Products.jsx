import { useEffect, useMemo, useState } from "react";
import api from "./api/client";
import "./Products.css";

const emptyForm = {
  product_code: "",
  name: "",
  category: "",
  description: "",
  unit: "",
  selling_price: "",
  is_active: true,
};

const getArray = (response) => {
  if (Array.isArray(response.data)) return response.data;
  if (Array.isArray(response.data?.data)) return response.data.data;
  if (Array.isArray(response.data?.items)) return response.data.items;
  return [];
};

const formatCurrency = (value) => {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(Number(value || 0));
};

function Products() {
  const [products, setProducts] = useState([]);
  const [search, setSearch] = useState("");

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const [showModal, setShowModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);

  const [form, setForm] = useState(emptyForm);

  const loadProducts = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get("/products/");
      setProducts(getArray(response));
    } catch (err) {
      console.error("Products error:", err);

      if (err.response?.status === 401) {
        setError("Authentication required. Please log in again.");
      } else {
        setError("Unable to load products from the server.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, []);

  const filteredProducts = useMemo(() => {
    const term = search.trim().toLowerCase();

    if (!term) return products;

    return products.filter((product) => {
      return (
        String(product.product_code || "")
          .toLowerCase()
          .includes(term) ||
        String(product.name || "")
          .toLowerCase()
          .includes(term) ||
        String(product.category || "")
          .toLowerCase()
          .includes(term) ||
        String(product.description || "")
          .toLowerCase()
          .includes(term) ||
        String(product.unit || "")
          .toLowerCase()
          .includes(term)
      );
    });
  }, [products, search]);

  const openAddModal = () => {
    setEditingProduct(null);
    setForm(emptyForm);
    setError("");
    setShowModal(true);
  };

  const openEditModal = (product) => {
    setEditingProduct(product);

    setForm({
      product_code: product.product_code || "",
      name: product.name || "",
      category: product.category || "",
      description: product.description || "",
      unit: product.unit || "",
      selling_price: product.selling_price ?? "",
      is_active: product.is_active !== false,
    });

    setError("");
    setShowModal(true);
  };

  const closeModal = () => {
    if (saving) return;

    setShowModal(false);
    setEditingProduct(null);
    setForm(emptyForm);
    setError("");
  };

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!form.product_code.trim()) {
      setError("Product code is required.");
      return;
    }

    if (!form.name.trim()) {
      setError("Product name is required.");
      return;
    }

    if (!form.category.trim()) {
      setError("Category is required.");
      return;
    }

    if (!form.unit.trim()) {
      setError("Unit is required.");
      return;
    }

    if (
      form.selling_price === "" ||
      Number(form.selling_price) < 0
    ) {
      setError("Please enter a valid selling price.");
      return;
    }

    const payload = {
      product_code: form.product_code.trim(),
      name: form.name.trim(),
      category: form.category.trim(),
      description: form.description.trim(),
      unit: form.unit.trim(),
      selling_price: Number(form.selling_price),
      is_active: form.is_active,
    };

    try {
      setSaving(true);
      setError("");

      if (editingProduct) {
        const productId =
          editingProduct.product_id ?? editingProduct.id;

        await api.put(`/products/${productId}`, payload);
      } else {
        await api.post("/products/", payload);
      }

      await loadProducts();
      closeModal();
    } catch (err) {
      console.error("Save product error:", err);

      const detail = err.response?.data?.detail;

      if (Array.isArray(detail)) {
        setError(
          detail
            .map((item) => item.msg || "Invalid value")
            .join(", ")
        );
      } else {
        setError(
          detail ||
            "Unable to save the product. Please check the information and try again."
        );
      }
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (product) => {
    const productId = product.product_id ?? product.id;

    const confirmed = window.confirm(
      `Are you sure you want to deactivate "${product.name}"?`
    );

    if (!confirmed) return;

    try {
      setError("");

      await api.delete(`/products/${productId}`);

      await loadProducts();
    } catch (err) {
      console.error("Delete product error:", err);

      const detail = err.response?.data?.detail;

      setError(
        detail ||
          "Unable to deactivate this product."
      );
    }
  };

  return (
    <section className="products-page">
      {/* HEADER */}
      <div className="products-header">
        <div>
          <p className="products-eyebrow">
            PRODUCT MANAGEMENT
          </p>

          <h1>Products</h1>

          <p className="products-subtitle">
            Manage your products, categories, pricing and availability.
          </p>
        </div>

        <button
          className="products-primary-button"
          onClick={openAddModal}
        >
          + Add Product
        </button>
      </div>

      {/* TOOLBAR */}
      <div className="products-toolbar">
        <div className="products-count">
          <strong>{filteredProducts.length}</strong>
          <span>
            {filteredProducts.length === 1
              ? "product"
              : "products"}
          </span>
        </div>

        <div className="products-toolbar-actions">
          <div className="products-search">
            <span>⌕</span>

            <input
              type="text"
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
              placeholder="Search products..."
            />

            {search && (
              <button
                type="button"
                className="clear-search"
                onClick={() => setSearch("")}
              >
                ×
              </button>
            )}
          </div>

          <button
            className="products-refresh"
            onClick={loadProducts}
            disabled={loading}
          >
            ↻ Refresh
          </button>
        </div>
      </div>

      {/* ERROR */}
      {error && !showModal && (
        <div className="products-error">
          <strong>Something went wrong</strong>
          <span>{error}</span>

          <button onClick={loadProducts}>
            Try Again
          </button>
        </div>
      )}

      {/* TABLE */}
      <div className="products-table-card">
        <div className="table-scroll">
          <table className="products-table">
            <thead>
              <tr>
                <th>PRODUCT</th>
                <th>CATEGORY</th>
                <th>DESCRIPTION</th>
                <th>UNIT</th>
                <th>PRICE</th>
                <th>STATUS</th>
                <th>ACTIONS</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td
                    colSpan="7"
                    className="products-empty"
                  >
                    Loading products...
                  </td>
                </tr>
              ) : filteredProducts.length === 0 ? (
                <tr>
                  <td
                    colSpan="7"
                    className="products-empty"
                  >
                    {search
                      ? "No products match your search."
                      : "No products found."}
                  </td>
                </tr>
              ) : (
                filteredProducts.map((product) => {
                  const productId =
                    product.product_id ?? product.id;

                  const active =
                    product.is_active !== false;

                  return (
                    <tr key={productId}>
                      <td>
                        <div className="product-main">
                          <div className="product-avatar">
                            {String(
                              product.name || "P"
                            )
                              .charAt(0)
                              .toUpperCase()}
                          </div>

                          <div>
                            <strong>
                              {product.name}
                            </strong>

                            <small>
                              {product.product_code}
                            </small>
                          </div>
                        </div>
                      </td>

                      <td>
                        <span className="category-badge">
                          {product.category || "—"}
                        </span>
                      </td>

                      <td>
                        <span className="description-text">
                          {product.description || "—"}
                        </span>
                      </td>

                      <td>
                        {product.unit || "—"}
                      </td>

                      <td>
                        <strong>
                          {formatCurrency(
                            product.selling_price
                          )}
                        </strong>
                      </td>

                      <td>
                        <span
                          className={`product-status ${
                            active
                              ? "active"
                              : "inactive"
                          }`}
                        >
                          {active
                            ? "Active"
                            : "Inactive"}
                        </span>
                      </td>

                      <td>
                        <div className="product-actions">
                          <button
                            className="edit-product"
                            onClick={() =>
                              openEditModal(product)
                            }
                          >
                            Edit
                          </button>

                          {active && (
                            <button
                              className="delete-product"
                              onClick={() =>
                                handleDelete(product)
                              }
                            >
                              Deactivate
                            </button>
                          )}
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

      {/* MODAL */}
      {showModal && (
        <div className="product-modal-overlay">
          <div className="product-modal">
            <div className="product-modal-header">
              <div>
                <p className="products-eyebrow">
                  {editingProduct
                    ? "EDIT PRODUCT"
                    : "NEW PRODUCT"}
                </p>

                <h2>
                  {editingProduct
                    ? "Edit Product"
                    : "Add Product"}
                </h2>
              </div>

              <button
                className="modal-close"
                onClick={closeModal}
                disabled={saving}
              >
                ×
              </button>
            </div>

            <form
              className="product-form"
              onSubmit={handleSubmit}
            >
              <div className="product-form-grid">
                <div className="form-group">
                  <label>
                    Product Code
                  </label>

                  <input
                    name="product_code"
                    value={form.product_code}
                    onChange={handleChange}
                    placeholder="e.g. CUR001"
                    disabled={saving}
                  />
                </div>

                <div className="form-group">
                  <label>
                    Product Name
                  </label>

                  <input
                    name="name"
                    value={form.name}
                    onChange={handleChange}
                    placeholder="e.g. Blackout Curtains"
                    disabled={saving}
                  />
                </div>

                <div className="form-group">
                  <label>
                    Category
                  </label>

                  <input
                    name="category"
                    value={form.category}
                    onChange={handleChange}
                    placeholder="e.g. Curtains"
                    disabled={saving}
                  />
                </div>

                <div className="form-group">
                  <label>
                    Unit
                  </label>

                  <input
                    name="unit"
                    value={form.unit}
                    onChange={handleChange}
                    placeholder="e.g. Meter"
                    disabled={saving}
                  />
                </div>

                <div className="form-group full-width">
                  <label>
                    Description
                  </label>

                  <textarea
                    name="description"
                    value={form.description}
                    onChange={handleChange}
                    placeholder="Describe the product..."
                    rows="3"
                    disabled={saving}
                  />
                </div>

                <div className="form-group">
                  <label>
                    Selling Price
                  </label>

                  <div className="price-input">
                    <span>₹</span>

                    <input
                      type="number"
                      name="selling_price"
                      value={form.selling_price}
                      onChange={handleChange}
                      min="0"
                      step="0.01"
                      placeholder="0.00"
                      disabled={saving}
                    />
                  </div>
                </div>

                <div className="form-group status-field">
                  <label>Product Status</label>

                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      name="is_active"
                      checked={form.is_active}
                      onChange={handleChange}
                      disabled={saving}
                    />

                    <span>
                      Product is active
                    </span>
                  </label>
                </div>
              </div>

              {error && (
                <div className="form-error">
                  {error}
                </div>
              )}

              <div className="product-form-footer">
                <button
                  type="button"
                  className="cancel-button"
                  onClick={closeModal}
                  disabled={saving}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="save-product-button"
                  disabled={saving}
                >
                  {saving
                    ? "Saving..."
                    : editingProduct
                    ? "Save Changes"
                    : "Create Product"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  );
}

export default Products;