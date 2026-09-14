import { useEffect, useMemo, useRef, useState } from "react";
import api from "./api/client";
import "./AdminIntelligence.css";

function formatCurrency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(Number(value || 0));
}

function formatNumber(value, decimals = 1) {
  return new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: decimals,
  }).format(Number(value || 0));
}

function formatRisk(risk) {
  return String(risk || "UNKNOWN")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function riskClass(risk) {
  const value = String(risk || "").toLowerCase();

  if (value === "critical") return "critical";
  if (value === "high") return "high";
  if (value === "medium") return "medium";
  if (value === "low") return "low";
  return "info";
}

function getHealthMessage(health) {
  return (
    health?.message ||
    health?.reason ||
    "Business health information is available."
  );
}

function getForecastSummary(forecast) {
  const values = Array.isArray(forecast?.forecast)
    ? forecast.forecast
        .map((item) => Number(item?.predicted_value || 0))
        .filter((value) => Number.isFinite(value))
    : [];

  if (!values.length) {
    return {
      total: 0,
      average: 0,
      first: 0,
      last: 0,
    };
  }

  return {
    total: values.reduce((sum, value) => sum + value, 0),
    average:
      values.reduce((sum, value) => sum + value, 0) /
      values.length,
    first: values[0],
    last: values[values.length - 1],
  };
}

function DepartmentCard({ name, result }) {
  const risk =
    result?.risk ||
    result?.overall_risk?.risk ||
    result?.risk_level ||
    "INFO";

  const score =
    result?.risk_score ??
    result?.overall_risk?.risk_score ??
    null;

  return (
    <div className={`bi-department-card ${riskClass(risk)}`}>
      <div className="bi-department-top">
        <div>
          <span className="bi-department-label">DEPARTMENT</span>
          <h3>{name}</h3>
        </div>

        <span className={`bi-risk-badge ${riskClass(risk)}`}>
          {formatRisk(risk)}
        </span>
      </div>

      <div className="bi-department-bottom">
        <span>
          {result?.recommendation ||
            result?.message ||
            "Operational intelligence available."}
        </span>

        {score !== null && (
          <strong>Risk {formatNumber(score, 0)}</strong>
        )}
      </div>
    </div>
  );
}

function RecommendationItem({ recommendation }) {
  const priority = recommendation?.priority || "info";

  return (
    <div className={`bi-recommendation ${riskClass(priority)}`}>
      <div className="bi-recommendation-icon">
        {priority === "critical"
          ? "!"
          : priority === "high"
            ? "▲"
            : priority === "medium"
              ? "•"
              : "i"}
      </div>

      <div className="bi-recommendation-content">
        <div className="bi-recommendation-heading">
          <strong>
            {recommendation?.title || "Business recommendation"}
          </strong>

          <span className={`bi-priority ${riskClass(priority)}`}>
            {String(priority).toUpperCase()}
          </span>
        </div>

        <p>
          {recommendation?.message ||
            recommendation?.description ||
            recommendation?.recommendation ||
            "Review this business signal."}
        </p>
      </div>
    </div>
  );
}

function ForecastCard({ title, forecast, currency = false }) {
  const summary = getForecastSummary(forecast);

  const display = (value) =>
    currency ? formatCurrency(value) : formatNumber(value, 1);

  return (
    <div className="bi-forecast-card">
      <div className="bi-forecast-heading">
        <span>{title}</span>
        <span className="bi-method">
          {forecast?.selected_method === "ml_model"
            ? forecast?.model_name || "ML model"
            : "Historical baseline"}
        </span>
      </div>

      <strong>{display(summary.total)}</strong>

      <div className="bi-forecast-meta">
        <span>
          {forecast?.forecast_periods || 0} periods
        </span>
        <span>
          Avg {display(summary.average)}
        </span>
      </div>

      <div className="bi-forecast-reliability">
        Reliability:{" "}
        <strong>
          {formatRisk(
            forecast?.reliability?.level || "unknown"
          )}
        </strong>
      </div>
    </div>
  );
}

export default function AdminIntelligence() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");
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

  const loadIntelligence = async (isRefresh = false) => {
    const requestId = ++requestIdRef.current;
    stopPolling();

    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    setProcessing(false);
    setError("");

    let attempts = 0;

    const poll = async () => {
      if (requestId !== requestIdRef.current) return;

      attempts += 1;

      try {
        const response = await api.get(
          "/ml/admin-intelligence?periods=8",
          { timeout: 30000 }
        );

        if (requestId !== requestIdRef.current) return;

        const payload = response.data || {};

        if (payload.status === "processing") {
          setProcessing(true);
          setLoading(!result);
          setRefreshing(isRefresh);

          if (attempts >= MAX_POLL_ATTEMPTS) {
            setProcessing(false);
            setLoading(false);
            setRefreshing(false);
            setError(
              "Business Intelligence is taking longer than expected. Please try again."
            );
            return;
          }

          pollTimerRef.current = window.setTimeout(
            poll,
            POLL_INTERVAL_MS
          );
          return;
        }

        if (payload.status === "success" || payload.intelligence) {
          setResult(payload);
          setProcessing(false);
          setLoading(false);
          setRefreshing(false);
          return;
        }

        throw new Error(
          "Business Intelligence returned an unexpected response."
        );
      } catch (requestError) {
        if (requestId !== requestIdRef.current) return;

        console.error(
          "Admin Intelligence API error:",
          requestError
        );

        const detail =
          requestError?.response?.data?.detail ||
          requestError?.message ||
          "Unable to load Business Intelligence. Check that the backend is running and your role has reports.view permission.";

        setProcessing(false);
        setLoading(false);
        setRefreshing(false);
        setError(detail);
      }
    };

    await poll();
  };

  const refreshIntelligence = async () => {
    const requestId = ++requestIdRef.current;
    stopPolling();

    setRefreshing(true);
    setProcessing(true);
    setError("");

    try {
      const response = await api.post(
        "/ml/admin-intelligence/refresh?periods=8",
        null,
        { timeout: 30000 }
      );

      if (requestId !== requestIdRef.current) return;

      if (response.data?.status === "processing") {
        await loadIntelligence(true);
        return;
      }

      await loadIntelligence(true);
    } catch (requestError) {
      if (requestId !== requestIdRef.current) return;

      console.error(
        "Admin Intelligence refresh error:",
        requestError
      );

      setProcessing(false);
      setRefreshing(false);
      setError(
        requestError?.response?.data?.detail ||
          requestError?.message ||
          "Unable to refresh Business Intelligence."
      );
    }
  };

  useEffect(() => {
    loadIntelligence();

    return () => {
      requestIdRef.current += 1;
      stopPolling();
    };
  }, []);

  const intelligence = result?.intelligence || {};
  const health = intelligence?.business_health || {};
  const overallRisk = intelligence?.overall_risk || {};

  const departments = intelligence?.departments || {};

  const recommendations = useMemo(() => {
    const items =
      intelligence?.executive_recommendations || [];

    return Array.isArray(items) ? items : [];
  }, [intelligence]);

  const criticalCount = recommendations.filter(
    (item) =>
      String(item?.priority || "").toLowerCase() === "critical"
  ).length;

  const highCount = recommendations.filter(
    (item) =>
      String(item?.priority || "").toLowerCase() === "high"
  ).length;

  if (loading) {
    return (
      <section className="content">
        <div className="bi-loading">
          <div className="bi-loading-icon">◌</div>
          <p className="eyebrow">MACHINE LEARNING</p>
          <h3>Generating Business Intelligence...</h3>
          <p>
            Running validated forecasts and department-level
            intelligence.
          </p>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="content">
        <div className="bi-error">
          <div className="bi-error-icon">!</div>
          <p className="eyebrow">INTELLIGENCE UNAVAILABLE</p>
          <h3>Unable to load Business Intelligence</h3>
          <p>{error}</p>

          <button
            className="primary-button"
            onClick={() => loadIntelligence()}
          >
            Retry
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="content bi-page">
      <div className="bi-header">
        <div>
          <p className="eyebrow">MACHINE LEARNING</p>
          <h3>Business Intelligence</h3>
          <p>
            Forecasts, operational risks, and recommendations
            generated from validated business data.
          </p>
        </div>

        <button
          className="primary-button"
          onClick={refreshIntelligence}
          disabled={refreshing}
        >
          {refreshing ? "Refreshing..." : "↻ Refresh Intelligence"}
        </button>
      </div>

      <div className="bi-hero-grid">
        <div className={`bi-risk-hero ${riskClass(overallRisk.risk)}`}>
          <div>
            <span className="bi-hero-label">
              OVERALL BUSINESS RISK
            </span>
            <h1>{formatRisk(overallRisk.risk)}</h1>
            <p>
              {overallRisk.reason ||
                "Overall operational risk calculated from department intelligence."}
            </p>
          </div>

          <div className="bi-risk-score">
            <span>RISK SCORE</span>
            <strong>
              {formatNumber(overallRisk.risk_score, 0)}
            </strong>
            <small>/ 100</small>
          </div>
        </div>

        <div className="bi-health-card">
          <span className="bi-hero-label">BUSINESS HEALTH</span>
          <h2>
            {formatRisk(health.health || health.status)}
          </h2>
          <strong>
            {formatNumber(health.score, 0)} / 100
          </strong>
          <p>{getHealthMessage(health)}</p>
        </div>
      </div>

      <div className="bi-summary-grid">
        <div className="bi-summary-card">
          <span>Critical Issues</span>
          <strong>{criticalCount}</strong>
        </div>

        <div className="bi-summary-card">
          <span>High Priority</span>
          <strong>{highCount}</strong>
        </div>

        <div className="bi-summary-card">
          <span>Critical Departments</span>
          <strong>
            {Array.isArray(overallRisk.critical_departments)
              ? overallRisk.critical_departments.length
              : 0}
          </strong>
        </div>

        <div className="bi-summary-card">
          <span>Forecast Horizon</span>
          <strong>
            {result?.forecasts?.revenue?.forecast_periods || 8} weeks
          </strong>
        </div>
      </div>

      <div className="bi-section">
        <div className="bi-section-heading">
          <div>
            <p className="eyebrow">OPERATIONS</p>
            <h3>Department Intelligence</h3>
          </div>
        </div>

        <div className="bi-department-grid">
          <DepartmentCard
            name="Sales"
            result={departments.sales}
          />
          <DepartmentCard
            name="Inventory"
            result={departments.inventory}
          />
          <DepartmentCard
            name="Production"
            result={departments.production}
          />
          <DepartmentCard
            name="Delivery"
            result={departments.delivery}
          />
          <DepartmentCard
            name="Accounts"
            result={departments.accounts}
          />
        </div>
      </div>

      <div className="bi-section">
        <div className="bi-section-heading">
          <div>
            <p className="eyebrow">FORECASTS</p>
            <h3>Business Forecast Outlook</h3>
          </div>
        </div>

        <div className="bi-forecast-grid">
          <ForecastCard
            title="Revenue"
            forecast={result?.forecasts?.revenue}
            currency
          />

          <ForecastCard
            title="Orders"
            forecast={result?.forecasts?.orders}
          />

          <ForecastCard
            title="Production Workload"
            forecast={result?.forecasts?.production}
          />

          <ForecastCard
            title="Delivery Workload"
            forecast={result?.forecasts?.delivery}
          />

          <ForecastCard
            title="Cash Inflow"
            forecast={result?.forecasts?.cashflow}
            currency
          />
        </div>
      </div>

      <div className="bi-section">
        <div className="bi-section-heading">
          <div>
            <p className="eyebrow">DECISION SUPPORT</p>
            <h3>Executive Recommendations</h3>
            <p>
              These recommendations are generated from the
              current forecast and operational risk signals.
            </p>
          </div>

          <span className="bi-count">
            {recommendations.length} recommendations
          </span>
        </div>

        <div className="bi-recommendations">
          {recommendations.length === 0 ? (
            <div className="bi-empty">
              No executive recommendations were generated.
            </div>
          ) : (
            recommendations.map((recommendation, index) => (
              <RecommendationItem
                key={
                  recommendation?.id ||
                  `${recommendation?.title || "recommendation"}-${index}`
                }
                recommendation={recommendation}
              />
            ))
          )}
        </div>
      </div>

      <div className="bi-disclaimer">
        <strong>Decision-support notice</strong>
        <span>
          Forecasts are based on available historical business
          data and validation results. They support operational
          decisions but should not be treated as guaranteed
          future outcomes.
        </span>
      </div>
    </section>
  );
}
