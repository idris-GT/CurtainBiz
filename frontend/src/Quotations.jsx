import { useEffect, useMemo, useState } from "react";
import api from "./api/client";
import "./Quotations.css";

const EMPTY_ITEM = {
  product_id: "",
  quantity: 1,
  unit_price: "",
  specifications: "",
};

function getArray(response) {
  if (Array.isArray(response?.data)) return response.data;
  if (Array.isArray(response?.data?.data)) return response.data.data;
  if (Array.isArray(response?.data?.items)) return response.data.items;
  return [];
}

function getCustomerName(customer) {
  return (
    customer?.name ||
    customer?.customer_name ||
    customer?.full_name ||
    customer?.company_name ||
    `Customer #${customer?.id ?? "—"}`
  );
}

function getProductName(product) {
  return (
    product?.name ||
    product?.product_name ||
    product?.title ||
    `Product #${product?.id ?? "—"}`
  );
}

function getProductCode(product) {
  return (
    product?.product_code ||
    product?.code ||
    `PROD${String(product?.id ?? "").padStart(3, "0")}`
  );
}

function getProductPrice(product) {
  return Number(
    product?.unit_price ??
      product?.selling_price ??
      product?.price ??
      product?.sale_price ??
      product?.default_price ??
      0
  );
}

function formatCurrency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(Number(value || 0));
}

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function createQuotationNumber(quotations) {
  const year = new Date().getFullYear();

  const numbers = quotations
    .map((quotation) =>
      String(quotation?.quotation_number || "")
    )
    .map((number) => {
      const match = number.match(/(\d+)$/);
      return match ? Number(match[1]) : 0;
    });

  const next =
    (numbers.length ? Math.max(...numbers) : 0) + 1;

  return `QUO-${year}-${String(next).padStart(3, "0")}`;
}

function Quotations() {
  const [quotations, setQuotations] = useState([]);
  const [quotationItems, setQuotationItems] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [products, setProducts] = useState([]);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  const [showCreate, setShowCreate] = useState(false);
  const [selectedQuotation, setSelectedQuotation] =
    useState(null);
  const [prediction, setPrediction] = useState(null);
  const [predictionLoading, setPredictionLoading] = useState(false);
  const [predictionError, setPredictionError] = useState("");

  const today = new Date()
    .toISOString()
    .slice(0, 10);

  const defaultValidUntil = new Date(
    Date.now() + 7 * 86400000
  )
    .toISOString()
    .slice(0, 10);

  const [form, setForm] = useState({
    quotation_number: "",
    customer_id: "",
    quotation_date: today,
    valid_until: defaultValidUntil,
    status: "DRAFT",
    tax_rate: 0,
    notes: "",
    items: [{ ...EMPTY_ITEM }],
  });

  const loadData = async () => {
    try {
      setLoading(true);
      setError("");

      const [
        quotationsResponse,
        itemsResponse,
        customersResponse,
        productsResponse,
      ] = await Promise.all([
        api.get("/quotations/"),
        api.get("/quotation-items/"),
        api.get("/customers/"),
        api.get("/products/"),
      ]);

      setQuotations(getArray(quotationsResponse));
      setQuotationItems(getArray(itemsResponse));
      setCustomers(getArray(customersResponse));
      setProducts(getArray(productsResponse));
    } catch (err) {
      console.error(
        "Quotation loading error:",
        err
      );

      setError(
        err.response?.status === 401
          ? "Authentication required. Please log in again."
          : err.response?.data?.detail ||
              "Unable to load quotations."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const filteredQuotations = useMemo(() => {
    const value = search.trim().toLowerCase();

    if (!value) {
      return quotations;
    }

    return quotations.filter((quotation) => {
      const customer = customers.find(
        (item) =>
          Number(item?.id) ===
          Number(quotation?.customer_id)
      );

      return (
        String(
          quotation?.quotation_number || ""
        )
          .toLowerCase()
          .includes(value) ||
        String(quotation?.status || "")
          .toLowerCase()
          .includes(value) ||
        getCustomerName(customer)
          .toLowerCase()
          .includes(value)
      );
    });
  }, [quotations, customers, search]);

  const itemCountFor = (quotationId) => {
    return quotationItems.filter(
      (item) =>
        Number(item?.quotation_id) ===
        Number(quotationId)
    ).length;
  };

  const openCreate = () => {
    setError("");

    setForm({
      quotation_number:
        createQuotationNumber(quotations),
      customer_id: "",
      quotation_date: today,
      valid_until: defaultValidUntil,
      status: "DRAFT",
      tax_rate: 0,
      notes: "",
      items: [{ ...EMPTY_ITEM }],
    });

    setShowCreate(true);
  };

  const closeCreate = () => {
    if (saving) return;
    setShowCreate(false);
  };

  const updateForm = (name, value) => {
    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const updateItem = (
    index,
    name,
    value
  ) => {
    setForm((previous) => {
      const items = [...previous.items];

      items[index] = {
        ...items[index],
        [name]: value,
      };

      if (name === "product_id") {
        const product = products.find(
          (item) =>
            Number(item?.id) === Number(value)
        );

        items[index].unit_price = product
          ? getProductPrice(product)
          : "";
      }

      return {
        ...previous,
        items,
      };
    });
  };

  const addItem = () => {
    setForm((previous) => ({
      ...previous,
      items: [
        ...previous.items,
        { ...EMPTY_ITEM },
      ],
    }));
  };

  const removeItem = (index) => {
    setForm((previous) => {
      if (previous.items.length === 1) {
        return previous;
      }

      return {
        ...previous,
        items: previous.items.filter(
          (_, itemIndex) =>
            itemIndex !== index
        ),
      };
    });
  };

  const subtotal = form.items.reduce(
    (total, item) =>
      total +
      Number(item.quantity || 0) *
        Number(item.unit_price || 0),
    0
  );

  const taxAmount =
    subtotal *
    (Number(form.tax_rate || 0) / 100);

  const totalAmount =
    subtotal + taxAmount;

  const handleCreate = async (event) => {
    event.preventDefault();

    if (!form.customer_id) {
      setError("Please select a customer.");
      return;
    }

    if (!form.quotation_number.trim()) {
      setError(
        "Quotation number is required."
      );
      return;
    }

    if (
      form.valid_until <
      form.quotation_date
    ) {
      setError(
        "Valid until date cannot be before quotation date."
      );
      return;
    }

    const cleanItems =
      form.items.map((item) => ({
        product_id: Number(
          item.product_id
        ),
        quantity: Number(
          item.quantity
        ),
        unit_price: Number(
          item.unit_price
        ),
        specifications:
          item.specifications.trim(),
      }));

    if (
      cleanItems.some(
        (item) => !item.product_id
      )
    ) {
      setError(
        "Please select a product for every item."
      );
      return;
    }

    if (
      cleanItems.some(
        (item) => item.quantity <= 0
      )
    ) {
      setError(
        "Quantity must be greater than zero."
      );
      return;
    }

    if (
      cleanItems.some(
        (item) => item.unit_price < 0
      )
    ) {
      setError(
        "Unit price cannot be negative."
      );
      return;
    }

    try {
      setSaving(true);
      setError("");

      /*
       * Get the currently authenticated user.
       * The quotation API requires created_by.
       */
      const authResponse =
        await api.get("/auth-test/");

      const createdBy =
        authResponse.data?.user_id;

      if (!createdBy) {
        throw new Error(
          "Unable to determine the logged-in user."
        );
      }

      /*
       * STEP 1:
       * Create quotation header.
       */
      const quotationPayload = {
        quotation_number:
          form.quotation_number.trim(),

        customer_id:
          Number(form.customer_id),

        created_by: createdBy,

        quotation_date:
          form.quotation_date,

        valid_until:
          form.valid_until,

        status: form.status,

        subtotal:
          Number(subtotal.toFixed(2)),

        tax_amount:
          Number(taxAmount.toFixed(2)),

        total_amount:
          Number(totalAmount.toFixed(2)),

        notes:
          form.notes.trim(),
      };

      const quotationResponse =
        await api.post(
          "/quotations/",
          quotationPayload
        );

      const createdQuotation =
        quotationResponse.data;

      const quotationId =
        createdQuotation?.id ||
        createdQuotation?.quotation_id;

      if (!quotationId) {
        throw new Error(
          "Quotation was created, but no quotation ID was returned."
        );
      }

      /*
       * STEP 2:
       * Create every quotation item using
       * the newly-created quotation ID.
       */
      for (const item of cleanItems) {
        await api.post(
          "/quotation-items/",
          {
            quotation_id:
              Number(quotationId),

            product_id:
              item.product_id,

            quantity:
              item.quantity,

            unit_price:
              item.unit_price,

            total_price:
              Number(
                (
                  item.quantity *
                  item.unit_price
                ).toFixed(2)
              ),

            specifications:
              item.specifications,
          }
        );
      }

      setShowCreate(false);

      await loadData();
    } catch (err) {
      console.error(
        "Quotation creation error:",
        err
      );

      setError(
        err.response?.status === 401
          ? "Authentication required. Please log in again."
          : err.response?.data?.detail ||
              err.message ||
              "Unable to create quotation."
      );
    } finally {
      setSaving(false);
    }
  };

  const selectedItems =
    selectedQuotation
      ? quotationItems.filter(
          (item) =>
            Number(
              item?.quotation_id
            ) ===
            Number(
              selectedQuotation?.id
            )
        )
      : [];

  const getConversionPrediction = async (quotation) => {
    const quotationId = quotation?.id;

    if (!quotationId) {
      setPredictionError("Quotation ID is missing.");
      return;
    }

    try {
      setPredictionLoading(true);
      setPredictionError("");
      setPrediction(null);

      const response = await api.get(
        `/ml/quotation/${Number(quotationId)}/conversion`
      );

      setPrediction(response.data);
    } catch (err) {
      console.error("ML prediction error:", err);

      setPredictionError(
        err.response?.status === 401
          ? "Authentication required. Please log in again."
          : err.response?.status === 403
          ? "You do not have permission to view AI predictions."
          : err.response?.data?.detail ||
              err.message ||
              "Unable to generate AI conversion prediction."
      );
    } finally {
      setPredictionLoading(false);
    }
  };

  const closeDetails = () => {
    setSelectedQuotation(null);
    setPrediction(null);
    setPredictionError("");
  };

  const predictionProbability = Number(
    prediction?.prediction?.conversion_probability ?? 0
  );

  const predictionRisk =
    prediction?.prediction?.risk_level ||
    (predictionProbability >= 70
      ? "High likelihood"
      : predictionProbability >= 40
      ? "Medium likelihood"
      : "Low likelihood");


  return (
    <div className="quotations-page">
      <div className="quotations-header">
        <div>
          <p className="quotations-eyebrow">
            SALES MANAGEMENT
          </p>

          <h1>Quotations</h1>

          <p>
            Create, track and manage customer
            quotations.
          </p>
        </div>

        <button
          className="quotations-primary-button"
          onClick={openCreate}
        >
          + New Quotation
        </button>
      </div>

      {error && (
        <div className="quotations-error">
          <div>
            <strong>
              Something went wrong
            </strong>

            <span>{error}</span>
          </div>

          <button
            type="button"
            onClick={loadData}
          >
            Try Again
          </button>
        </div>
      )}

      <div className="quotations-toolbar">
        <div className="quotations-count">
          <strong>
            {quotations.length}
          </strong>

          <span>quotations</span>
        </div>

        <div className="quotations-search">
          <span>⌕</span>

          <input
            type="text"
            placeholder="Search quotations..."
            value={search}
            onChange={(event) =>
              setSearch(
                event.target.value
              )
            }
          />
        </div>

        <button
          className="quotations-refresh"
          onClick={loadData}
          disabled={loading}
        >
          ↻ Refresh
        </button>
      </div>

      <div className="quotations-table-card">
        <div className="quotations-table-wrapper">
          <table className="quotations-table">
            <thead>
              <tr>
                <th>QUOTATION</th>
                <th>CUSTOMER</th>
                <th>DATE</th>
                <th>VALID UNTIL</th>
                <th>ITEMS</th>
                <th>TOTAL</th>
                <th>STATUS</th>
                <th>ACTIONS</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td
                    colSpan="8"
                    className="quotations-empty"
                  >
                    Loading quotations...
                  </td>
                </tr>
              ) : filteredQuotations.length ===
                0 ? (
                <tr>
                  <td
                    colSpan="8"
                    className="quotations-empty"
                  >
                    {search
                      ? "No quotations match your search."
                      : "No quotations found."}
                  </td>
                </tr>
              ) : (
                filteredQuotations.map(
                  (quotation) => {
                    const customer =
                      customers.find(
                        (item) =>
                          Number(
                            item?.id
                          ) ===
                          Number(
                            quotation?.customer_id
                          )
                      );

                    const status =
                      String(
                        quotation?.status ||
                          "DRAFT"
                      ).toUpperCase();

                    return (
                      <tr
                        key={
                          quotation.id
                        }
                      >
                        <td>
                          <strong className="quotation-number">
                            {quotation?.quotation_number ||
                              `QUO-${quotation?.id}`}
                          </strong>

                          <span className="quotation-id">
                            ID:{" "}
                            {quotation?.id ??
                              "—"}
                          </span>
                        </td>

                        <td>
                          {getCustomerName(
                            customer
                          )}
                        </td>

                        <td>
                          {formatDate(
                            quotation?.quotation_date
                          )}
                        </td>

                        <td>
                          {formatDate(
                            quotation?.valid_until
                          )}
                        </td>

                        <td>
                          {itemCountFor(
                            quotation?.id
                          )}
                        </td>

                        <td>
                          <strong>
                            {formatCurrency(
                              quotation?.total_amount ??
                                quotation?.total ??
                                0
                            )}
                          </strong>
                        </td>

                        <td>
                          <span
                            className={`quotation-status ${status
                              .toLowerCase()
                              .replaceAll(
                                "_",
                                "-"
                              )}`}
                          >
                            {status.replaceAll(
                              "_",
                              " "
                            )}
                          </span>
                        </td>

                        <td>
                          <button
                            className="quotation-view-button"
                            onClick={() => {
                              setSelectedQuotation(quotation);
                              setPrediction(null);
                              setPredictionError("");
                            }}
                          >
                            View
                          </button>

                          <button
                            className="quotation-view-button"
                            onClick={() => {
                              setSelectedQuotation(quotation);
                              setPrediction(null);
                              setPredictionError("");
                              getConversionPrediction(quotation);
                            }}
                            disabled={predictionLoading && Number(prediction?.quotation_id) === Number(quotation?.id)}
                            title="Predict quotation conversion with AI"
                          >
                            🤖 AI
                          </button>
                        </td>
                      </tr>
                    );
                  }
                )
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* CREATE QUOTATION MODAL */}

      {showCreate && (
        <div
          className="quotation-modal-overlay"
          onMouseDown={(event) => {
            if (
              event.target ===
              event.currentTarget
            ) {
              closeCreate();
            }
          }}
        >
          <div className="quotation-modal">
            <div className="quotation-modal-header">
              <div>
                <p>
                  SALES QUOTATION
                </p>

                <h2>
                  New Quotation
                </h2>
              </div>

              <button
                type="button"
                className="quotation-close-button"
                onClick={closeCreate}
                disabled={saving}
              >
                ×
              </button>
            </div>

            <form
              onSubmit={handleCreate}
            >
              <div className="quotation-form-scroll">
                <div className="quotation-form-grid">
                  <div className="quotation-field">
                    <label>
                      Quotation Number
                    </label>

                    <input
                      value={
                        form.quotation_number
                      }
                      onChange={(event) =>
                        updateForm(
                          "quotation_number",
                          event.target.value
                        )
                      }
                      required
                    />
                  </div>

                  <div className="quotation-field">
                    <label>
                      Customer
                    </label>

                    <select
                      value={
                        form.customer_id
                      }
                      onChange={(event) =>
                        updateForm(
                          "customer_id",
                          event.target.value
                        )
                      }
                      required
                    >
                      <option value="">
                        Select customer
                      </option>

                      {customers.map(
                        (customer) => (
                          <option
                            key={
                              customer.id
                            }
                            value={
                              customer.id
                            }
                          >
                            {getCustomerName(
                              customer
                            )}
                          </option>
                        )
                      )}
                    </select>
                  </div>

                  <div className="quotation-field">
                    <label>
                      Quotation Date
                    </label>

                    <input
                      type="date"
                      value={
                        form.quotation_date
                      }
                      onChange={(event) =>
                        updateForm(
                          "quotation_date",
                          event.target.value
                        )
                      }
                      required
                    />
                  </div>

                  <div className="quotation-field">
                    <label>
                      Valid Until
                    </label>

                    <input
                      type="date"
                      value={
                        form.valid_until
                      }
                      onChange={(event) =>
                        updateForm(
                          "valid_until",
                          event.target.value
                        )
                      }
                      required
                    />
                  </div>

                  <div className="quotation-field">
                    <label>
                      Status
                    </label>

                    <select
                      value={
                        form.status
                      }
                      onChange={(event) =>
                        updateForm(
                          "status",
                          event.target.value
                        )
                      }
                    >
                      <option value="DRAFT">
                        Draft
                      </option>

                      <option value="SENT">
                        Sent
                      </option>

                      <option value="APPROVED">
                        Approved
                      </option>

                      <option value="REJECTED">
                        Rejected
                      </option>

                      <option value="EXPIRED">
                        Expired
                      </option>
                    </select>
                  </div>

                  <div className="quotation-field">
                    <label>
                      Tax Rate (%)
                    </label>

                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={
                        form.tax_rate
                      }
                      onChange={(event) =>
                        updateForm(
                          "tax_rate",
                          event.target.value
                        )
                      }
                    />
                  </div>
                </div>

                <div className="quotation-items-section">
                  <div className="quotation-section-heading">
                    <div>
                      <p>
                        LINE ITEMS
                      </p>

                      <h3>
                        Products in this quotation
                      </h3>
                    </div>

                    <button
                      type="button"
                      className="quotation-add-item"
                      onClick={addItem}
                    >
                      + Add Item
                    </button>
                  </div>

                  {form.items.map(
                    (item, index) => (
                      <div
                        className="quotation-item-row"
                        key={index}
                      >
                        <div className="quotation-field product-field">
                          <label>
                            Product
                          </label>

                          <select
                            value={
                              item.product_id
                            }
                            onChange={(event) =>
                              updateItem(
                                index,
                                "product_id",
                                event.target.value
                              )
                            }
                            required
                          >
                            <option value="">
                              Select product
                            </option>

                            {products.map(
                              (product) => (
                                <option
                                  key={
                                    product.id
                                  }
                                  value={
                                    product.id
                                  }
                                >
                                  {
                                    getProductCode(
                                      product
                                    )
                                  }{" "}
                                  —{" "}
                                  {
                                    getProductName(
                                      product
                                    )
                                  }
                                </option>
                              )
                            )}
                          </select>
                        </div>

                        <div className="quotation-field small-field">
                          <label>
                            Qty
                          </label>

                          <input
                            type="number"
                            min="1"
                            step="1"
                            value={
                              item.quantity
                            }
                            onChange={(event) =>
                              updateItem(
                                index,
                                "quantity",
                                event.target.value
                              )
                            }
                            required
                          />
                        </div>

                        <div className="quotation-field price-field">
                          <label>
                            Unit Price
                          </label>

                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            value={
                              item.unit_price
                            }
                            onChange={(event) =>
                              updateItem(
                                index,
                                "unit_price",
                                event.target.value
                              )
                            }
                            required
                          />
                        </div>

                        <div className="quotation-field specification-field">
                          <label>
                            Specifications
                          </label>

                          <input
                            value={
                              item.specifications
                            }
                            placeholder="Measurements / finish / notes"
                            onChange={(event) =>
                              updateItem(
                                index,
                                "specifications",
                                event.target.value
                              )
                            }
                          />
                        </div>

                        <button
                          type="button"
                          className="quotation-remove-item"
                          onClick={() =>
                            removeItem(index)
                          }
                          disabled={
                            form.items
                              .length === 1
                          }
                        >
                          ×
                        </button>
                      </div>
                    )
                  )}
                </div>

                <div className="quotation-bottom-grid">
                  <div className="quotation-field">
                    <label>
                      Notes
                    </label>

                    <textarea
                      rows="4"
                      value={form.notes}
                      placeholder="Add quotation notes..."
                      onChange={(event) =>
                        updateForm(
                          "notes",
                          event.target.value
                        )
                      }
                    />
                  </div>

                  <div className="quotation-summary">
                    <div>
                      <span>
                        Subtotal
                      </span>

                      <strong>
                        {formatCurrency(
                          subtotal
                        )}
                      </strong>
                    </div>

                    <div>
                      <span>
                        Tax
                      </span>

                      <strong>
                        {formatCurrency(
                          taxAmount
                        )}
                      </strong>
                    </div>

                    <div className="quotation-grand-total">
                      <span>
                        Total
                      </span>

                      <strong>
                        {formatCurrency(
                          totalAmount
                        )}
                      </strong>
                    </div>
                  </div>
                </div>
              </div>

              <div className="quotation-modal-footer">
                <button
                  type="button"
                  className="quotation-cancel-button"
                  onClick={closeCreate}
                  disabled={saving}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="quotation-save-button"
                  disabled={saving}
                >
                  {saving
                    ? "Creating..."
                    : "Create Quotation"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* DETAILS MODAL */}

      {selectedQuotation && (
        <div
          className="quotation-modal-overlay"
          onMouseDown={(event) => {
            if (
              event.target ===
              event.currentTarget
            ) {
              closeDetails();
            }
          }}
        >
          <div className="quotation-details-modal">
            <div className="quotation-modal-header">
              <div>
                <p>
                  QUOTATION DETAILS
                </p>

                <h2>
                  {selectedQuotation.quotation_number ||
                    `QUO-${selectedQuotation.id}`}
                </h2>

                <p>
                  Use the AI prediction to estimate the likelihood that this quotation will convert into an order.
                </p>
              </div>

              <button
                className="quotation-close-button"
                onClick={closeDetails}
              >
                ×
              </button>
            </div>

            <div className="quotation-details-body">
              <div className="quotation-detail-grid">
                <div>
                  <span>
                    Customer
                  </span>

                  <strong>
                    {getCustomerName(
                      customers.find(
                        (customer) =>
                          Number(
                            customer.id
                          ) ===
                          Number(
                            selectedQuotation.customer_id
                          )
                      )
                    )}
                  </strong>
                </div>

                <div>
                  <span>
                    Status
                  </span>

                  <strong>
                    {String(
                      selectedQuotation.status ||
                        "DRAFT"
                    ).replaceAll(
                      "_",
                      " "
                    )}
                  </strong>
                </div>

                <div>
                  <span>
                    Date
                  </span>

                  <strong>
                    {formatDate(
                      selectedQuotation.quotation_date
                    )}
                  </strong>
                </div>

                <div>
                  <span>
                    Valid Until
                  </span>

                  <strong>
                    {formatDate(
                      selectedQuotation.valid_until
                    )}
                  </strong>
                </div>
              </div>

              <div className="quotation-ai-section">
                <div className="quotation-ai-header">
                  <div>
                    <p>AI INSIGHT</p>
                    <h3>Quotation Conversion Prediction</h3>
                  </div>

                  <button
                    type="button"
                    className="quotation-ai-button"
                    onClick={() =>
                      getConversionPrediction(selectedQuotation)
                    }
                    disabled={predictionLoading}
                  >
                    {predictionLoading
                      ? "Analyzing..."
                      : "🤖 Run AI Prediction"}
                  </button>
                </div>

                {predictionError && (
                  <div className="quotation-ai-error">
                    {predictionError}
                  </div>
                )}

                {prediction && !predictionError && (
                  <div className="quotation-ai-result">
                    <div className="quotation-ai-probability">
                      <span>Conversion Probability</span>
                      <strong>{predictionProbability.toFixed(2)}%</strong>
                    </div>

                    <div className="quotation-ai-meta">
                      <div>
                        <span>Prediction</span>
                        <strong>
                          {prediction?.prediction?.converted_to_order
                            ? "Likely to convert"
                            : "Unlikely to convert"}
                        </strong>
                      </div>

                      <div>
                        <span>Likelihood</span>
                        <strong>{predictionRisk}</strong>
                      </div>

                      <div>
                        <span>Model</span>
                        <strong>
                          {prediction?.model?.name ||
                            "quotation_conversion_model"}
                          {prediction?.model?.version
                            ? ` v${prediction.model.version}`
                            : ""}
                        </strong>
                      </div>
                    </div>

                    <p className="quotation-ai-note">
                      This estimate is generated from the trained quotation conversion model using the quotation's available business data.
                    </p>
                  </div>
                )}
              </div>

              <div className="quotation-detail-items">
                <h3>
                  Items
                </h3>

                {selectedItems.length ===
                0 ? (
                  <p>
                    No quotation items found.
                  </p>
                ) : (
                  <div className="quotation-detail-table-wrapper">
                    <table>
                      <thead>
                        <tr>
                          <th>
                            PRODUCT
                          </th>
                          <th>
                            QTY
                          </th>
                          <th>
                            UNIT PRICE
                          </th>
                          <th>
                            TOTAL
                          </th>
                          <th>
                            SPECIFICATIONS
                          </th>
                        </tr>
                      </thead>

                      <tbody>
                        {selectedItems.map(
                          (item) => (
                            <tr
                              key={
                                item.id
                              }
                            >
                              <td>
                                {item.product ||
                                  item.product_name ||
                                  item.product_code ||
                                  `Product #${item.product_id}`}
                              </td>

                              <td>
                                {
                                  item.quantity
                                }
                              </td>

                              <td>
                                {formatCurrency(
                                  item.unit_price
                                )}
                              </td>

                              <td>
                                {formatCurrency(
                                  item.total_price
                                )}
                              </td>

                              <td>
                                {item.specifications ||
                                  "—"}
                              </td>
                            </tr>
                          )
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {selectedQuotation.notes && (
                <div className="quotation-detail-notes">
                  <span>
                    Notes
                  </span>

                  <p>
                    {
                      selectedQuotation.notes
                    }
                  </p>
                </div>
              )}
            </div>

            <div className="quotation-details-footer">
              <strong>
                Total:{" "}
                {formatCurrency(
                  selectedQuotation.total_amount ??
                    selectedQuotation.total ??
                    0
                )}
              </strong>

              <button
                className="quotation-cancel-button"
                onClick={closeDetails}
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

export default Quotations;