import React, { useEffect, useState } from "react";
import api from "./api/client";
import "./SalesIntelligence.css";

function safeNumber(value, fallback = 0) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function formatNumber(value, decimals = 1) {
  const number = safeNumber(value);

  return number.toLocaleString("en-IN", {
    maximumFractionDigits: decimals,
    minimumFractionDigits: decimals,
  });
}

function formatCurrency(value) {
  const number = safeNumber(value);

  return `₹${number.toLocaleString("en-IN", {
    maximumFractionDigits: 0,
  })}`;
}

function titleCase(value) {
  if (!value) return "—";

  return String(value)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

/* =========================================================
   FORECAST HELPERS
========================================================= */

function getForecastPeriods(forecast) {
  return safeNumber(
    forecast?.forecast_periods ??
      forecast?.periods ??
      forecast?.horizon ??
      0
  );
}

function getForecastValues(forecast) {
  if (!forecast) return [];

  if (Array.isArray(forecast.forecast)) {
    return forecast.forecast.map((item) =>
      safeNumber(
        item?.predicted_value ??
          item?.prediction ??
          item?.value ??
          item?.forecast ??
          0
      )
    );
  }

  return [];
}

function getForecastTotal(forecast) {
  if (!forecast) return 0;

  if (forecast.forecast_total !== undefined) {
    return safeNumber(forecast.forecast_total);
  }

  if (forecast.total_forecast !== undefined) {
    return safeNumber(forecast.total_forecast);
  }

  if (forecast.expected_total !== undefined) {
    return safeNumber(forecast.expected_total);
  }

  const values = getForecastValues(forecast);

  if (values.length > 0) {
    return values.reduce((sum, value) => sum + value, 0);
  }

  return 0;
}

function getForecastAverage(forecast) {
  if (!forecast) return 0;

  if (forecast.forecast_average !== undefined) {
    return safeNumber(forecast.forecast_average);
  }

  if (forecast.average_forecast !== undefined) {
    return safeNumber(forecast.average_forecast);
  }

  if (forecast.average_weekly_demand !== undefined) {
    return safeNumber(forecast.average_weekly_demand);
  }

  const values = getForecastValues(forecast);

  if (values.length > 0) {
    return (
      values.reduce((sum, value) => sum + value, 0) /
      values.length
    );
  }

  const total = getForecastTotal(forecast);
  const periods = getForecastPeriods(forecast);

  if (periods > 0) {
    return total / periods;
  }

  return safeNumber(forecast.historical_mean);
}

function getMethod(forecast) {
  if (!forecast) return "—";

  return (
    forecast.selected_method ||
    forecast.method ||
    forecast.model_name ||
    "—"
  );
}

function getReliability(forecast) {
  if (!forecast) return "unknown";

  return (
    forecast.reliability?.level ||
    forecast.reliability ||
    "unknown"
  );
}

function getReliabilityClass(value) {
  const reliability = String(value || "").toLowerCase();

  if (reliability === "high") return "high";
  if (reliability === "moderate") return "moderate";

  return "low";
}

/* =========================================================
   SMALL COMPONENTS
========================================================= */

function MetricCard({ label, value, helper }) {
  return (
    <div className="si-metric-card">
      <span className="si-metric-label">
        {label}
      </span>

      <strong className="si-metric-value">
        {value}
      </strong>

      {helper && (
        <span className="si-metric-helper">
          {helper}
        </span>
      )}
    </div>
  );
}

function ForecastCard({
  title,
  forecast,
  currency = false,
}) {
  const total = getForecastTotal(forecast);
  const average = getForecastAverage(forecast);
  const periods = getForecastPeriods(forecast);
  const reliability = getReliability(forecast);
  const method = getMethod(forecast);

  return (
    <div className="si-forecast-card">
      <div className="si-forecast-header">
        <div>
          <span className="si-card-eyebrow">
            FORECAST
          </span>

          <h3>{title}</h3>
        </div>

        <span className="si-method-badge">
          {titleCase(method)}
        </span>
      </div>

      <div className="si-forecast-main">
        {currency
          ? formatCurrency(total)
          : formatNumber(total)}
      </div>

      <div className="si-forecast-meta">
        <div>
          <span>Horizon</span>

          <strong>
            {periods > 0
              ? `${periods} periods`
              : "—"}
          </strong>
        </div>

        <div>
          <span>Average</span>

          <strong>
            {currency
              ? formatCurrency(average)
              : formatNumber(average)}
          </strong>
        </div>
      </div>

      <div className="si-reliability">
        Reliability:{" "}
        <strong>
          {titleCase(reliability)}
        </strong>
      </div>
    </div>
  );
}

/* =========================================================
   FORECAST PERIOD TABLE
========================================================= */

function ForecastPeriodTable({
  forecast,
  currency = false,
}) {
  const values = getForecastValues(forecast);

  if (values.length === 0) {
    return (
      <div className="si-empty">
        No forecast period data available.
      </div>
    );
  }

  return (
    <div className="si-period-table-wrap">
      <table className="si-period-table">
        <thead>
          <tr>
            <th>PERIOD</th>
            <th>EXPECTED VALUE</th>
          </tr>
        </thead>

        <tbody>
          {values.map((value, index) => (
            <tr key={index}>
              <td>
                Period {index + 1}
              </td>

              <td>
                <strong>
                  {currency
                    ? formatCurrency(value)
                    : formatNumber(value)}
                </strong>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* =========================================================
   PRODUCT DEMAND TABLE
========================================================= */

function ProductDemandTable({
  productDemand,
}) {
  if (!productDemand) {
    return (
      <div className="si-empty">
        Product demand intelligence is not available.
      </div>
    );
  }

  const products = Array.isArray(productDemand.products)
    ? productDemand.products
    : [];

  if (products.length === 0) {
    return (
      <div className="si-empty">
        No product-level demand forecasts are available.
      </div>
    );
  }

  return (
    <div className="si-product-table-wrap">
      <table className="si-product-table">
        <thead>
          <tr>
            <th>PRODUCT</th>
            <th>FORECAST DEMAND</th>
            <th>AVG / WEEK</th>
            <th>METHOD</th>
            <th>RELIABILITY</th>
          </tr>
        </thead>

        <tbody>
          {products.map((product, index) => {
            const forecastTotal = safeNumber(
              product?.forecast_total ??
                product?.total_forecast ??
                product?.expected_total ??
                0
            );

            const averageDemand = safeNumber(
              product?.average_weekly_demand ??
                product?.forecast_average ??
                0
            );

            const method =
              product?.selected_method ||
              product?.method ||
              product?.model_name ||
              "—";

            const reliability =
              product?.reliability?.level ||
              product?.reliability ||
              "unknown";

            const productName =
              product?.product_name ||
              product?.name ||
              product?.product?.name ||
              `Product #${product?.product_id ?? index + 1}`;

            return (
              <tr
                key={
                  product?.product_id ??
                  `${productName}-${index}`
                }
              >
                <td>
                  <strong>{productName}</strong>

                  {product?.product_id !== undefined && (
                    <small>
                      ID: {product.product_id}
                    </small>
                  )}
                </td>

                <td>
                  <strong>
                    {formatNumber(forecastTotal)}
                  </strong>
                </td>

                <td>
                  {formatNumber(averageDemand)}
                </td>

                <td>
                  <span className="si-product-method">
                    {titleCase(method)}
                  </span>
                </td>

                <td>
                  <span
                    className={`si-reliability-badge ${getReliabilityClass(
                      reliability
                    )}`}
                  >
                    {titleCase(reliability)}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/* =========================================================
   MAIN PAGE
========================================================= */

export default function SalesIntelligence() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadSalesIntelligence() {
    try {
      setError("");
      setLoading(true);

      const response = await api.get(
        "/ml/sales-intelligence",
        {
          params: {
            periods: 8,
          },
        }
      );

      console.log(
        "Sales Intelligence response:",
        response.data
      );

      setData(response.data);
    } catch (err) {
      console.error(
        "Sales Intelligence error:",
        err
      );

      setError(
        err?.response?.data?.detail ||
          "Unable to load Sales Intelligence."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSalesIntelligence();
  }, []);

  /* =======================================================
     BACKEND DATA
  ======================================================= */

  const revenueForecast =
    data?.revenue_forecast ||
    data?.sales_forecast ||
    null;

  const orderForecast =
    data?.order_forecast ||
    null;

  const productDemandForecast =
    data?.product_demand_forecast ||
    data?.product_demand ||
    null;

  const revenueTotal =
    getForecastTotal(revenueForecast);

  const orderTotal =
    getForecastTotal(orderForecast);

  const revenueAverage =
    getForecastAverage(revenueForecast);

  const orderAverage =
    getForecastAverage(orderForecast);

  const forecastPeriods =
    getForecastPeriods(revenueForecast) ||
    getForecastPeriods(orderForecast);

  const productCount = safeNumber(
    productDemandForecast?.product_count ??
      productDemandForecast?.products?.length ??
      0
  );

  /* =======================================================
     LOADING
  ======================================================= */

  if (loading) {
    return (
      <div className="si-page">
        <div className="si-loading">
          <div className="si-loading-spinner" />

          <span className="si-card-eyebrow">
            MACHINE LEARNING
          </span>

          <h2>
            Loading Sales Intelligence...
          </h2>

          <p>
            Loading validated sales forecasts
            and product demand intelligence.
          </p>
        </div>
      </div>
    );
  }

  /* =======================================================
     ERROR
  ======================================================= */

  if (error) {
    return (
      <div className="si-page">
        <div className="si-error">
          <span className="si-error-icon">
            !
          </span>

          <div>
            <h2>
              Sales Intelligence unavailable
            </h2>

            <p>{error}</p>

            <button
              type="button"
              className="si-retry-button"
              onClick={loadSalesIntelligence}
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  /* =======================================================
     PAGE
  ======================================================= */

  return (
    <div className="si-page">

      {/* =================================================
          HERO
      ================================================= */}

      <section className="si-hero">
        <span className="si-card-eyebrow">
          SALES &amp; DEMAND
        </span>

        <h1>
          Sales Intelligence
        </h1>

        <p>
          Forecast revenue, order activity and
          product-level demand using validated
          historical business data.
        </p>

        <span className="si-source">
          Machine-learning decision support
        </span>
      </section>

      {/* =================================================
          SUMMARY
      ================================================= */}

      <section className="si-summary-grid">

        <MetricCard
          label="FORECAST REVENUE"
          value={formatCurrency(revenueTotal)}
          helper={
            forecastPeriods > 0
              ? `${forecastPeriods}-period forecast`
              : "Forecast horizon"
          }
        />

        <MetricCard
          label="EXPECTED ORDERS"
          value={formatNumber(orderTotal)}
          helper={
            forecastPeriods > 0
              ? `${forecastPeriods}-period forecast`
              : "Forecast horizon"
          }
        />

        <MetricCard
          label="AVG REVENUE / PERIOD"
          value={formatCurrency(revenueAverage)}
          helper="Expected average"
        />

        <MetricCard
          label="AVG ORDERS / PERIOD"
          value={formatNumber(orderAverage)}
          helper="Expected average"
        />

      </section>

      {/* =================================================
          SALES OUTLOOK
      ================================================= */}

      <section className="si-section">

        <div className="si-section-heading">
          <span className="si-card-eyebrow">
            FORECASTS
          </span>

          <h2>
            Sales Outlook
          </h2>

          <p>
            Expected sales activity over the
            selected forecast horizon.
          </p>
        </div>

        <div className="si-forecast-grid">

          <ForecastCard
            title="Revenue"
            forecast={revenueForecast}
            currency
          />

          <ForecastCard
            title="Orders"
            forecast={orderForecast}
          />

        </div>

      </section>

      {/* =================================================
          REVENUE PERIOD DETAILS
      ================================================= */}

      <section className="si-section">

        <div className="si-section-heading">
          <span className="si-card-eyebrow">
            REVENUE TREND
          </span>

          <h2>
            Revenue Forecast Periods
          </h2>

          <p>
            Individual forecast values generated
            by the selected forecasting method.
          </p>
        </div>

        <ForecastPeriodTable
          forecast={revenueForecast}
          currency
        />

      </section>

      {/* =================================================
          ORDER PERIOD DETAILS
      ================================================= */}

      <section className="si-section">

        <div className="si-section-heading">
          <span className="si-card-eyebrow">
            ORDER TREND
          </span>

          <h2>
            Order Forecast Periods
          </h2>

          <p>
            Expected order workload for each
            forecast period.
          </p>
        </div>

        <ForecastPeriodTable
          forecast={orderForecast}
        />

      </section>

      {/* =================================================
          PRODUCT DEMAND
      ================================================= */}

      <section className="si-section">

        <div className="si-section-heading">
          <span className="si-card-eyebrow">
            PRODUCT DEMAND
          </span>

          <h2>
            Product Demand Intelligence
          </h2>

          <p>
            Forecasted demand for individual
            products based on historical order
            activity.
          </p>
        </div>

        <div className="si-product-summary">
          <MetricCard
            label="PRODUCTS ANALYZED"
            value={formatNumber(productCount, 0)}
            helper="Products with demand forecasts"
          />

          <MetricCard
            label="FORECAST HORIZON"
            value={
              productDemandForecast?.forecast_periods
                ? `${productDemandForecast.forecast_periods} weeks`
                : "8 weeks"
            }
            helper="Product demand forecast"
          />
        </div>

        <ProductDemandTable
          productDemand={productDemandForecast}
        />

      </section>

      {/* =================================================
          DECISION SUPPORT
      ================================================= */}

      <section className="si-section">

        <div className="si-insight-card">

          <div className="si-insight-icon">
            ✓
          </div>

          <div>

            <span className="si-card-eyebrow">
              DECISION SUPPORT
            </span>

            <h2>
              Sales Planning Signal
            </h2>

            <p>
              Use the revenue, order and product
              demand forecasts alongside customer
              demand, product availability and
              operational capacity when planning
              upcoming sales activity.
            </p>

            <small>
              Forecasts are decision-support signals.
              Always interpret them according to
              their reported reliability.
            </small>

          </div>

        </div>

      </section>

    </div>
  );
}