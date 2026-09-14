import React, { useEffect, useRef, useState } from "react";
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

/*
  ---------------------------------------------------------
  FORECAST DATA HELPERS
  ---------------------------------------------------------

  Backend forecast structure:

  {
    forecast_periods: 8,
    historical_mean: ...,
    historical_total: ...,
    forecast: [
      {
        period: 1,
        predicted_value: ...
      }
    ],
    selected_method: ...,
    model_name: ...,
    reliability: {
      level: "low"
    }
  }
*/

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
          item?.forecast
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
    return null;
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
   MAIN PAGE
========================================================= */

export default function SalesIntelligence() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [processing, setProcessing] = useState(false);
  const pollTimerRef = useRef(null);
  const requestIdRef = useRef(0);

  const POLL_INTERVAL_MS = 3000;
  const MAX_POLL_ATTEMPTS = 200;

  function stopPolling() {
    if (pollTimerRef.current) {
      window.clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }

  async function loadSalesIntelligence() {
    const requestId = ++requestIdRef.current;
    stopPolling();
    setError("");
    setLoading(true);
    setProcessing(false);

    let attempts = 0;

    const poll = async () => {
      if (requestId !== requestIdRef.current) return;

      attempts += 1;

      try {
        const response = await api.get(
          "/ml/sales-intelligence",
          { timeout: 30000 }
        );

        if (requestId !== requestIdRef.current) return;

        console.log(
          "Sales Intelligence response:",
          response.data
        );

        if (response.data?.status === "processing") {
          setProcessing(true);
          setLoading(true);

          if (attempts >= MAX_POLL_ATTEMPTS) {
            setProcessing(false);
            setLoading(false);
            setError(
              "Sales Intelligence is taking longer than expected. Please try again."
            );
            return;
          }

          pollTimerRef.current = window.setTimeout(
            poll,
            POLL_INTERVAL_MS
          );
          return;
        }

        if (response.data?.status === "success" || response.data) {
          setData(response.data);
          setProcessing(false);
          setLoading(false);
          return;
        }

        throw new Error(
          "Sales Intelligence returned an unexpected response."
        );
      } catch (err) {
        if (requestId !== requestIdRef.current) return;

        console.error(
          "Sales Intelligence error:",
          err
        );

        setProcessing(false);
        setLoading(false);
        setError(
          err?.response?.data?.detail ||
            err?.message ||
            "Unable to load Sales Intelligence."
        );
      }
    };

    await poll();
  }

  useEffect(() => {
    loadSalesIntelligence();

    return () => {
      requestIdRef.current += 1;
      stopPolling();
    };
  }, []);

  /*
    The backend returns the sales intelligence
    object with revenue and order forecasts.
  */

  const revenueForecast =
    data?.revenue_forecast ||
    data?.sales_forecast ||
    null;

  const orderForecast =
    data?.order_forecast ||
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
            {processing
              ? "Generating Sales Intelligence..."
              : "Loading Sales Intelligence..."}
          </h2>

          <p>
            {processing
              ? "The backend is calculating validated forecasts. This page will update automatically when the result is ready."
              : "Loading validated sales forecasts and demand intelligence."}
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
          Forecast revenue and order activity
          using validated historical business data.
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
          
          IMPORTANT:
          The current sales-intelligence API does not
          provide product-demand forecasts.

          We deliberately do NOT invent product numbers.
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
            Product-level forecasting will be connected
            when the product-demand intelligence endpoint
            is exposed by the backend.
          </p>
        </div>

        <div className="si-empty">
          Product-level forecast data is not currently
          returned by the Sales Intelligence API.
          No artificial values are displayed.
        </div>

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
              Use the revenue and order forecasts
              alongside current customer demand,
              product availability and operational
              capacity when planning upcoming sales
              activity.
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