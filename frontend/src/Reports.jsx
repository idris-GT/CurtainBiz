import { useEffect, useMemo, useState } from "react";
import "./Reports.css";
import api from "./api/client";

/* =========================================================
   HELPERS
========================================================= */

function getArray(response) {
  if (Array.isArray(response.data)) return response.data;
  if (Array.isArray(response.data?.data)) return response.data.data;
  if (Array.isArray(response.data?.items)) return response.data.items;
  return [];
}

function toNumber(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
}

function formatCurrency(value) {
  const number = toNumber(value);

  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: Number.isInteger(number) ? 0 : 2,
    maximumFractionDigits: 2,
  }).format(number);
}

function formatNumber(value) {
  return new Intl.NumberFormat("en-IN").format(
    Math.round(toNumber(value))
  );
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

function formatMonth(value) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString("en-IN", {
    month: "short",
    year: "numeric",
  });
}

function titleCase(value) {
  return String(value || "UNKNOWN")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function isCompletedPayment(payment) {
  return ["COMPLETED", "PAID"].includes(
    String(payment.status || "").toUpperCase()
  );
}

function isDeliveredOrder(order) {
  return String(order.status || "").toUpperCase() === "DELIVERED";
}

function parseDate(value) {
  if (!value) return null;

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return null;
  }

  return date;
}

function startOfDay(date) {
  const result = new Date(date);
  result.setHours(0, 0, 0, 0);
  return result;
}

function endOfDay(date) {
  const result = new Date(date);
  result.setHours(23, 59, 59, 999);
  return result;
}

/* =========================================================
   SIMPLE BAR CHART
========================================================= */

function BarChart({
  items,
  valueFormatter = (value) => value,
  emptyText = "No data available",
}) {
  const max = Math.max(
    ...items.map((item) => toNumber(item.value)),
    0
  );

  if (!items.length) {
    return (
      <div className="chart-empty">
        {emptyText}
      </div>
    );
  }

  return (
    <div className="bar-chart">
      {items.map((item, index) => {
        const value = toNumber(item.value);

        const width =
          max > 0 ? Math.max((value / max) * 100, 3) : 0;

        return (
          <div className="bar-row" key={`${item.label}-${index}`}>
            <div className="bar-label" title={item.label}>
              {item.label}
            </div>

            <div className="bar-track">
              <div
                className="bar-fill"
                style={{ width: `${width}%` }}
              ></div>
            </div>

            <div className="bar-value">
              {valueFormatter(value)}
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* =========================================================
   DONUT / STATUS CHART
========================================================= */

function StatusChart({ items }) {
  const total = items.reduce(
    (sum, item) => sum + toNumber(item.value),
    0
  );

  if (!items.length || total === 0) {
    return (
      <div className="chart-empty">
        No status data available
      </div>
    );
  }

  let accumulated = 0;

  const gradientParts = items.map((item, index) => {
    const value = toNumber(item.value);

    const start = accumulated;
    const percentage = (value / total) * 100;
    accumulated += percentage;

    return `${getChartColor(index)} ${start}% ${accumulated}%`;
  });

  return (
    <div className="status-chart-area">
      <div
        className="donut-chart"
        style={{
          background: `conic-gradient(${gradientParts.join(", ")})`,
        }}
      >
        <div className="donut-center">
          <strong>{total}</strong>
          <span>Total</span>
        </div>
      </div>

      <div className="legend">
        {items.map((item, index) => (
          <div
            className="legend-item"
            key={`${item.label}-${index}`}
          >
            <span
              className="legend-dot"
              style={{
                background: getChartColor(index),
              }}
            ></span>

            <span className="legend-label">
              {item.label}
            </span>

            <strong>{item.value}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

function getChartColor(index) {
  const colors = [
    "#4f8edc",
    "#63b48a",
    "#e4a44b",
    "#d86b6b",
    "#8067c7",
    "#5ba6a6",
    "#8b9bb0",
  ];

  return colors[index % colors.length];
}

/* =========================================================
   LINE / TREND CHART
========================================================= */

function TrendChart({
  items,
  valueFormatter = (value) => value,
}) {
  if (!items.length) {
    return (
      <div className="chart-empty">
        No trend data available
      </div>
    );
  }

  const values = items.map((item) =>
    toNumber(item.value)
  );

  const max = Math.max(...values, 0);
  const min = Math.min(...values, 0);

  const width = 760;
  const height = 250;
  const paddingX = 35;
  const paddingY = 30;

  const chartWidth = width - paddingX * 2;
  const chartHeight = height - paddingY * 2;

  const range = Math.max(max - min, 1);

  const points = items.map((item, index) => {
    const x =
      items.length === 1
        ? width / 2
        : paddingX +
          (index / (items.length - 1)) *
            chartWidth;

    const y =
      height -
      paddingY -
      ((toNumber(item.value) - min) / range) *
        chartHeight;

    return {
      x,
      y,
      value: toNumber(item.value),
    };
  });

  const path = points
    .map((point, index) => {
      return `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`;
    })
    .join(" ");

  const areaPath = `
    M ${points[0].x} ${height - paddingY}
    ${points
      .map(
        (point) =>
          `L ${point.x} ${point.y}`
      )
      .join(" ")}
    L ${points[points.length - 1].x} ${
    height - paddingY
  }
    Z
  `;

  return (
    <div className="trend-chart-wrapper">
      <svg
        className="trend-chart"
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
      >
        <line
          x1={paddingX}
          y1={height - paddingY}
          x2={width - paddingX}
          y2={height - paddingY}
          className="chart-axis"
        />

        <line
          x1={paddingX}
          y1={paddingY}
          x2={paddingX}
          y2={height - paddingY}
          className="chart-axis"
        />

        <path
          d={areaPath}
          className="chart-area"
        />

        <path
          d={path}
          className="chart-line"
        />

        {points.map((point, index) => (
          <circle
            key={index}
            cx={point.x}
            cy={point.y}
            r="4"
            className="chart-point"
          />
        ))}
      </svg>

      <div className="trend-labels">
        {items.map((item, index) => (
          <div
            className="trend-label"
            key={`${item.label}-${index}`}
          >
            <span>{item.label}</span>

            <strong>
              {valueFormatter(
                toNumber(item.value)
              )}
            </strong>
          </div>
        ))}
      </div>
    </div>
  );
}

/* =========================================================
   REPORTS
========================================================= */

function Reports() {
  const [data, setData] = useState({
    orders: [],
    payments: [],
    quotations: [],
    customers: [],
    inventory: [],
    production: [],
    deliveries: [],
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [range, setRange] = useState("all");

  const [customFrom, setCustomFrom] = useState("");
  const [customTo, setCustomTo] = useState("");

  const [lastUpdated, setLastUpdated] = useState(null);

  /* =======================================================
     LOAD ALL REPORT DATA
  ======================================================= */

  const loadReports = async () => {
    try {
      setLoading(true);
      setError("");

      const [
        ordersResponse,
        paymentsResponse,
        quotationsResponse,
        customersResponse,
        inventoryResponse,
        productionResponse,
        deliveriesResponse,
      ] = await Promise.all([
        api.get("/orders/"),
        api.get("/payments/"),
        api.get("/quotations/"),
        api.get("/customers/"),
        api.get("/inventory/"),
        api.get("/production/"),
        api.get("/deliveries/"),
      ]);

      setData({
        orders: getArray(ordersResponse),
        payments: getArray(paymentsResponse),
        quotations: getArray(quotationsResponse),
        customers: getArray(customersResponse),
        inventory: getArray(inventoryResponse),
        production: getArray(productionResponse),
        deliveries: getArray(deliveriesResponse),
      });

      setLastUpdated(new Date());
    } catch (err) {
      console.error("Reports API error:", err);

      setError(
        "Unable to load report data. Please check that the backend is running and your account has permission to view the required data."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  /* =======================================================
     DATE FILTER
  ======================================================= */

  const dateRange = useMemo(() => {
    const now = new Date();

    if (range === "7") {
      const from = new Date(now);
      from.setDate(from.getDate() - 6);

      return {
        from: startOfDay(from),
        to: endOfDay(now),
      };
    }

    if (range === "30") {
      const from = new Date(now);
      from.setDate(from.getDate() - 29);

      return {
        from: startOfDay(from),
        to: endOfDay(now),
      };
    }

    if (range === "90") {
      const from = new Date(now);
      from.setDate(from.getDate() - 89);

      return {
        from: startOfDay(from),
        to: endOfDay(now),
      };
    }

    if (range === "custom") {
      return {
        from: customFrom
          ? startOfDay(
              new Date(`${customFrom}T00:00:00`)
            )
          : null,

        to: customTo
          ? endOfDay(
              new Date(`${customTo}T23:59:59`)
            )
          : null,
      };
    }

    return {
      from: null,
      to: null,
    };
  }, [range, customFrom, customTo]);

  const isInRange = (value) => {
    if (range === "all") return true;

    const date = parseDate(value);

    if (!date) return false;

    if (
      dateRange.from &&
      date < dateRange.from
    ) {
      return false;
    }

    if (
      dateRange.to &&
      date > dateRange.to
    ) {
      return false;
    }

    return true;
  };

  const filteredOrders = useMemo(() => {
    return data.orders.filter((order) =>
      isInRange(
        order.order_date ||
          order.created_at ||
          order.created_date
      )
    );
  }, [data.orders, dateRange, range]);

  const filteredPayments = useMemo(() => {
    return data.payments.filter((payment) =>
      isInRange(
        payment.payment_date ||
          payment.created_at
      )
    );
  }, [data.payments, dateRange, range]);

  const filteredQuotations = useMemo(() => {
    return data.quotations.filter((quotation) =>
      isInRange(
        quotation.quotation_date ||
          quotation.created_at
      )
    );
  }, [data.quotations, dateRange, range]);

  const filteredProduction = useMemo(() => {
    return data.production.filter((production) =>
      isInRange(
        production.start_date ||
          production.created_at
      )
    );
  }, [data.production, dateRange, range]);

  const filteredDeliveries = useMemo(() => {
    return data.deliveries.filter((delivery) =>
      isInRange(
        delivery.scheduled_date ||
          delivery.created_at
      )
    );
  }, [data.deliveries, dateRange, range]);

  /* =======================================================
     ORDER ANALYTICS
  ======================================================= */

  const orderAnalytics = useMemo(() => {
    const totalOrders = filteredOrders.length;

    const totalOrderValue = filteredOrders.reduce(
      (sum, order) =>
        sum + toNumber(order.total_amount),
      0
    );

    const subtotal = filteredOrders.reduce(
      (sum, order) =>
        sum + toNumber(order.subtotal),
      0
    );

    const tax = filteredOrders.reduce(
      (sum, order) =>
        sum + toNumber(order.tax_amount),
      0
    );

    const averageOrderValue =
      totalOrders > 0
        ? totalOrderValue / totalOrders
        : 0;

    const deliveredOrders =
      filteredOrders.filter(isDeliveredOrder)
        .length;

    const activeOrders =
      filteredOrders.filter((order) => {
        const status = String(
          order.status || ""
        ).toUpperCase();

        return ![
          "DELIVERED",
          "CANCELLED",
        ].includes(status);
      }).length;

    const statusMap = {};

    filteredOrders.forEach((order) => {
      const status = String(
        order.status || "UNKNOWN"
      ).toUpperCase();

      statusMap[status] =
        (statusMap[status] || 0) + 1;
    });

    const statusItems = Object.entries(statusMap)
      .map(([label, value]) => ({
        label: titleCase(label),
        value,
      }))
      .sort((a, b) => b.value - a.value);

    return {
      totalOrders,
      totalOrderValue,
      subtotal,
      tax,
      averageOrderValue,
      deliveredOrders,
      activeOrders,
      statusItems,
    };
  }, [filteredOrders]);

  /* =======================================================
     PAYMENT ANALYTICS
  ======================================================= */

  const paymentAnalytics = useMemo(() => {
    const completedPayments =
      filteredPayments.filter(
        isCompletedPayment
      );

    const pendingPayments =
      filteredPayments.filter((payment) => {
        const status = String(
          payment.status || ""
        ).toUpperCase();

        return ![
          "COMPLETED",
          "PAID",
        ].includes(status);
      });

    const collectedAmount =
      completedPayments.reduce(
        (sum, payment) =>
          sum + toNumber(payment.amount),
        0
      );

    const pendingAmount =
      pendingPayments.reduce(
        (sum, payment) =>
          sum + toNumber(payment.amount),
        0
      );

    const methodMap = {};

    filteredPayments.forEach((payment) => {
      const method = String(
        payment.payment_method || "OTHER"
      ).toUpperCase();

      methodMap[method] =
        (methodMap[method] || 0) +
        toNumber(payment.amount);
    });

    const methodItems = Object.entries(methodMap)
      .map(([label, value]) => ({
        label: titleCase(label),
        value,
      }))
      .sort((a, b) => b.value - a.value);

    return {
      completedCount: completedPayments.length,
      pendingCount: pendingPayments.length,
      collectedAmount,
      pendingAmount,
      methodItems,
    };
  }, [filteredPayments]);

  /* =======================================================
     QUOTATION ANALYTICS
  ======================================================= */

  const quotationAnalytics = useMemo(() => {
    const total = filteredQuotations.length;

    const totalValue = filteredQuotations.reduce(
      (sum, quotation) =>
        sum + toNumber(quotation.total_amount),
      0
    );

    const approved =
      filteredQuotations.filter(
        (quotation) =>
          String(
            quotation.status || ""
          ).toUpperCase() === "APPROVED"
      );

    const rejected =
      filteredQuotations.filter(
        (quotation) =>
          String(
            quotation.status || ""
          ).toUpperCase() === "REJECTED"
      );

    const sent =
      filteredQuotations.filter(
        (quotation) =>
          String(
            quotation.status || ""
          ).toUpperCase() === "SENT"
      );

    const draft =
      filteredQuotations.filter(
        (quotation) =>
          String(
            quotation.status || ""
          ).toUpperCase() === "DRAFT"
      );

    const expired =
      filteredQuotations.filter(
        (quotation) =>
          String(
            quotation.status || ""
          ).toUpperCase() === "EXPIRED"
      );

    const approvedValue =
      approved.reduce(
        (sum, quotation) =>
          sum + toNumber(quotation.total_amount),
        0
      );

    const statusMap = {};

    filteredQuotations.forEach((quotation) => {
      const status = String(
        quotation.status || "UNKNOWN"
      ).toUpperCase();

      statusMap[status] =
        (statusMap[status] || 0) + 1;
    });

    const statusItems = Object.entries(statusMap)
      .map(([label, value]) => ({
        label: titleCase(label),
        value,
      }))
      .sort((a, b) => b.value - a.value);

    return {
      total,
      totalValue,
      approvedCount: approved.length,
      approvedValue,
      rejectedCount: rejected.length,
      sentCount: sent.length,
      draftCount: draft.length,
      expiredCount: expired.length,
      statusItems,
    };
  }, [filteredQuotations]);

  /* =======================================================
     PRODUCTION ANALYTICS
  ======================================================= */

  const productionAnalytics = useMemo(() => {
    const total = filteredProduction.length;

    const completed =
      filteredProduction.filter(
        (item) =>
          String(item.status || "")
            .toUpperCase() ===
          "COMPLETED"
      ).length;

    const inProgress =
      filteredProduction.filter(
        (item) =>
          String(item.status || "")
            .toUpperCase() ===
          "IN_PROGRESS"
      ).length;

    const pending =
      filteredProduction.filter(
        (item) =>
          String(item.status || "")
            .toUpperCase() ===
          "PENDING"
      ).length;

    const qualityCheck =
      filteredProduction.filter(
        (item) =>
          String(item.status || "")
            .toUpperCase() ===
          "QUALITY_CHECK"
      ).length;

    const completionRate =
      total > 0
        ? (completed / total) * 100
        : 0;

    const departmentMap = {};

    filteredProduction.forEach((item) => {
      const department =
        item.department ||
        `Department #${
          item.assigned_department_id || "—"
        }`;

      departmentMap[department] =
        (departmentMap[department] || 0) + 1;
    });

    const departmentItems = Object.entries(
      departmentMap
    )
      .map(([label, value]) => ({
        label,
        value,
      }))
      .sort((a, b) => b.value - a.value);

    return {
      total,
      completed,
      inProgress,
      pending,
      qualityCheck,
      completionRate,
      departmentItems,
    };
  }, [filteredProduction]);

  /* =======================================================
     DELIVERY ANALYTICS
  ======================================================= */

  const deliveryAnalytics = useMemo(() => {
    const total = filteredDeliveries.length;

    const delivered =
      filteredDeliveries.filter(
        (item) =>
          String(item.status || "")
            .toUpperCase() ===
          "DELIVERED"
      );

    const pending =
      filteredDeliveries.filter(
        (item) =>
          String(item.status || "")
            .toUpperCase() ===
          "PENDING"
      );

    const scheduled =
      filteredDeliveries.filter(
        (item) =>
          String(item.status || "")
            .toUpperCase() ===
          "SCHEDULED"
      );

    const outForDelivery =
      filteredDeliveries.filter(
        (item) =>
          String(item.status || "")
            .toUpperCase() ===
          "OUT_FOR_DELIVERY"
      );

    const failed =
      filteredDeliveries.filter(
        (item) =>
          String(item.status || "")
            .toUpperCase() ===
          "FAILED"
      );

    const deliveryRate =
      total > 0
        ? (delivered.length / total) * 100
        : 0;

    const statusMap = {};

    filteredDeliveries.forEach((delivery) => {
      const status = String(
        delivery.status || "UNKNOWN"
      ).toUpperCase();

      statusMap[status] =
        (statusMap[status] || 0) + 1;
    });

    const statusItems = Object.entries(statusMap)
      .map(([label, value]) => ({
        label: titleCase(label),
        value,
      }))
      .sort((a, b) => b.value - a.value);

    return {
      total,
      delivered: delivered.length,
      pending: pending.length,
      scheduled: scheduled.length,
      outForDelivery: outForDelivery.length,
      failed: failed.length,
      deliveryRate,
      statusItems,
    };
  }, [filteredDeliveries]);

  /* =======================================================
     INVENTORY ANALYTICS
  ======================================================= */

  const inventoryAnalytics = useMemo(() => {
    const totalMaterials =
      data.inventory.length;

    const available = data.inventory.reduce(
      (sum, item) =>
        sum +
        toNumber(item.quantity_available),
      0
    );

    const reserved = data.inventory.reduce(
      (sum, item) =>
        sum +
        toNumber(item.reserved_quantity),
      0
    );

    const totalPhysical =
      available + reserved;

    const materialItems = data.inventory
      .map((item) => ({
        label:
          item.material ||
          item.material_code ||
          `Material #${item.material_id}`,
        value: toNumber(
          item.quantity_available
        ),
      }))
      .sort((a, b) => b.value - a.value);

    return {
      totalMaterials,
      available,
      reserved,
      totalPhysical,
      materialItems,
    };
  }, [data.inventory]);

  /* =======================================================
     CUSTOMER ANALYTICS
  ======================================================= */

  const customerAnalytics = useMemo(() => {
    const customerOrderMap = {};

    filteredOrders.forEach((order) => {
      const customer =
        order.customer ||
        `Customer #${order.customer_id || "—"}`;

      if (!customerOrderMap[customer]) {
        customerOrderMap[customer] = {
          count: 0,
          value: 0,
        };
      }

      customerOrderMap[customer].count += 1;
      customerOrderMap[customer].value +=
        toNumber(order.total_amount);
    });

    const topCustomers = Object.entries(
      customerOrderMap
    )
      .map(([label, item]) => ({
        label,
        value: item.value,
        count: item.count,
      }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 6);

    return {
      topCustomers,
      activeCustomers:
        Object.keys(customerOrderMap).length,
    };
  }, [filteredOrders]);

  /* =======================================================
     QUOTATION → ORDER CONVERSION
  ======================================================= */

  const conversionAnalytics = useMemo(() => {
    const quotationIdsWithOrders =
      new Set(
        filteredOrders
          .map((order) =>
            toNumber(order.quotation_id)
          )
          .filter((id) => id > 0)
      );

    const approvedCount =
      filteredQuotations.filter(
        (quotation) =>
          String(
            quotation.status || ""
          ).toUpperCase() === "APPROVED"
      ).length;

    const convertedApproved =
      filteredQuotations.filter(
        (quotation) =>
          String(
            quotation.status || ""
          ).toUpperCase() === "APPROVED" &&
          quotationIdsWithOrders.has(
            toNumber(quotation.id)
          )
      ).length;

    const conversionRate =
      approvedCount > 0
        ? (convertedApproved /
            approvedCount) *
          100
        : 0;

    return {
      approvedCount,
      convertedApproved,
      conversionRate,
    };
  }, [filteredOrders, filteredQuotations]);

  /* =======================================================
     TREND DATA
  ======================================================= */

  const monthlyOrderTrend = useMemo(() => {
    const map = {};

    filteredOrders.forEach((order) => {
      const date = parseDate(
        order.order_date
      );

      if (!date) return;

      const key = `${date.getFullYear()}-${String(
        date.getMonth() + 1
      ).padStart(2, "0")}`;

      if (!map[key]) {
        map[key] = {
          date,
          value: 0,
        };
      }

      map[key].value +=
        toNumber(order.total_amount);
    });

    return Object.entries(map)
      .sort((a, b) =>
        a[0].localeCompare(b[0])
      )
      .map(([, item]) => ({
        label: formatMonth(item.date),
        value: item.value,
      }));
  }, [filteredOrders]);

  const monthlyPaymentTrend = useMemo(() => {
    const map = {};

    filteredPayments.forEach((payment) => {
      if (!isCompletedPayment(payment)) {
        return;
      }

      const date = parseDate(
        payment.payment_date ||
          payment.created_at
      );

      if (!date) return;

      const key = `${date.getFullYear()}-${String(
        date.getMonth() + 1
      ).padStart(2, "0")}`;

      if (!map[key]) {
        map[key] = {
          date,
          value: 0,
        };
      }

      map[key].value +=
        toNumber(payment.amount);
    });

    return Object.entries(map)
      .sort((a, b) =>
        a[0].localeCompare(b[0])
      )
      .map(([, item]) => ({
        label: formatMonth(item.date),
        value: item.value,
      }));
  }, [filteredPayments]);

  /* =======================================================
     RECENT ORDERS
  ======================================================= */

  const recentOrders = useMemo(() => {
    return [...filteredOrders]
      .sort((a, b) => {
        const dateA = parseDate(
          a.order_date
        );

        const dateB = parseDate(
          b.order_date
        );

        return (
          (dateB?.getTime() || 0) -
          (dateA?.getTime() || 0)
        );
      })
      .slice(0, 8);
  }, [filteredOrders]);

  /* =======================================================
     EXPORT REPORT
  ======================================================= */

  const exportReport = () => {
    const rows = [
      [
        "Metric",
        "Value",
      ],
      [
        "Total Orders",
        orderAnalytics.totalOrders,
      ],
      [
        "Total Order Value",
        orderAnalytics.totalOrderValue,
      ],
      [
        "Average Order Value",
        orderAnalytics.averageOrderValue,
      ],
      [
        "Collected Payments",
        paymentAnalytics.collectedAmount,
      ],
      [
        "Pending Payments",
        paymentAnalytics.pendingAmount,
      ],
      [
        "Total Quotations",
        quotationAnalytics.total,
      ],
      [
        "Approved Quotations",
        quotationAnalytics.approvedCount,
      ],
      [
        "Quotation Conversion Rate",
        `${conversionAnalytics.conversionRate.toFixed(
          1
        )}%`,
      ],
      [
        "Production Completion Rate",
        `${productionAnalytics.completionRate.toFixed(
          1
        )}%`,
      ],
      [
        "Delivery Rate",
        `${deliveryAnalytics.deliveryRate.toFixed(
          1
        )}%`,
      ],
      [
        "Available Inventory",
        inventoryAnalytics.available,
      ],
      [
        "Reserved Inventory",
        inventoryAnalytics.reserved,
      ],
    ];

    const csv = rows
      .map((row) =>
        row
          .map((value) => {
            const text = String(value ?? "");

            return `"${text.replaceAll(
              '"',
              '""'
            )}"`;
          })
          .join(",")
      )
      .join("\n");

    const blob = new Blob(
      [csv],
      {
        type: "text/csv;charset=utf-8;",
      }
    );

    const url =
      URL.createObjectURL(blob);

    const link =
      document.createElement("a");

    link.href = url;
    link.download =
      "curtainbiz-report.csv";

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  };

  /* =======================================================
     RENDER
  ======================================================= */

  return (
    <section className="reports-page">
      {/* PAGE HEADER */}
      <div className="reports-header">
        <div>
          <p className="eyebrow">
            BUSINESS INTELLIGENCE
          </p>

          <h3>Reports & Analytics</h3>

          <p>
            Real-time business insights generated from
            your operational data.
          </p>
        </div>

        <div className="reports-header-actions">
          <button
            className="secondary-report-button"
            onClick={exportReport}
            disabled={loading}
          >
            ↓ Export CSV
          </button>

          <button
            className="primary-button"
            onClick={loadReports}
            disabled={loading}
          >
            {loading
              ? "Refreshing..."
              : "↻ Refresh"}
          </button>
        </div>
      </div>

      {/* FILTERS */}
      <div className="report-filter-card">
        <div className="filter-title">
          <strong>Report Period</strong>

          <span>
            Choose the period used for date-based
            analytics.
          </span>
        </div>

        <div className="filter-buttons">
          <button
            className={
              range === "all"
                ? "filter-button active"
                : "filter-button"
            }
            onClick={() =>
              setRange("all")
            }
          >
            All Time
          </button>

          <button
            className={
              range === "7"
                ? "filter-button active"
                : "filter-button"
            }
            onClick={() =>
              setRange("7")
            }
          >
            Last 7 Days
          </button>

          <button
            className={
              range === "30"
                ? "filter-button active"
                : "filter-button"
            }
            onClick={() =>
              setRange("30")
            }
          >
            Last 30 Days
          </button>

          <button
            className={
              range === "90"
                ? "filter-button active"
                : "filter-button"
            }
            onClick={() =>
              setRange("90")
            }
          >
            Last 90 Days
          </button>

          <button
            className={
              range === "custom"
                ? "filter-button active"
                : "filter-button"
            }
            onClick={() =>
              setRange("custom")
            }
          >
            Custom
          </button>
        </div>

        {range === "custom" && (
          <div className="custom-date-fields">
            <label>
              From

              <input
                type="date"
                value={customFrom}
                onChange={(event) =>
                  setCustomFrom(
                    event.target.value
                  )
                }
              />
            </label>

            <label>
              To

              <input
                type="date"
                value={customTo}
                onChange={(event) =>
                  setCustomTo(
                    event.target.value
                  )
                }
              />
            </label>
          </div>
        )}

        <div className="filter-status">
          {range === "all"
            ? "Showing all available records"
            : range === "custom"
            ? "Showing custom date range"
            : `Showing records from the last ${
                range
              } days`}
        </div>
      </div>

      {/* ERROR */}
      {error && (
        <div className="reports-error">
          <div>
            <strong>
              Report data could not be loaded
            </strong>

            <span>{error}</span>
          </div>

          <button onClick={loadReports}>
            Retry
          </button>
        </div>
      )}

      {/* ===================================================
          KPI CARDS
      =================================================== */}

      <div className="report-kpi-grid">
        <div className="report-kpi-card">
          <div className="report-kpi-icon">
            ◫
          </div>

          <div>
            <span>Total Orders</span>

            <strong>
              {loading
                ? "..."
                : formatNumber(
                    orderAnalytics.totalOrders
                  )}
            </strong>

            <small>
              {orderAnalytics.activeOrders} active
            </small>
          </div>
        </div>

        <div className="report-kpi-card">
          <div className="report-kpi-icon">
            ₹
          </div>

          <div>
            <span>Order Value</span>

            <strong>
              {loading
                ? "..."
                : formatCurrency(
                    orderAnalytics.totalOrderValue
                  )}
            </strong>

            <small>
              Avg{" "}
              {formatCurrency(
                orderAnalytics.averageOrderValue
              )}
            </small>
          </div>
        </div>

        <div className="report-kpi-card">
          <div className="report-kpi-icon">
            ✓
          </div>

          <div>
            <span>Collected</span>

            <strong>
              {loading
                ? "..."
                : formatCurrency(
                    paymentAnalytics.collectedAmount
                  )}
            </strong>

            <small>
              {paymentAnalytics.completedCount} completed
            </small>
          </div>
        </div>

        <div className="report-kpi-card">
          <div className="report-kpi-icon">
            !
          </div>

          <div>
            <span>Pending Payments</span>

            <strong>
              {loading
                ? "..."
                : formatCurrency(
                    paymentAnalytics.pendingAmount
                  )}
            </strong>

            <small>
              {paymentAnalytics.pendingCount} pending
            </small>
          </div>
        </div>

        <div className="report-kpi-card">
          <div className="report-kpi-icon">
            ▧
          </div>

          <div>
            <span>Quotations</span>

            <strong>
              {loading
                ? "..."
                : formatNumber(
                    quotationAnalytics.total
                  )}
            </strong>

            <small>
              {quotationAnalytics.approvedCount} approved
            </small>
          </div>
        </div>

        <div className="report-kpi-card">
          <div className="report-kpi-icon">
            ⚙
          </div>

          <div>
            <span>Production</span>

            <strong>
              {loading
                ? "..."
                : formatNumber(
                    productionAnalytics.total
                  )}
            </strong>

            <small>
              {productionAnalytics.completionRate.toFixed(
                0
              )}
              % completed
            </small>
          </div>
        </div>

        <div className="report-kpi-card">
          <div className="report-kpi-icon">
            ➜
          </div>

          <div>
            <span>Deliveries</span>

            <strong>
              {loading
                ? "..."
                : formatNumber(
                    deliveryAnalytics.total
                  )}
            </strong>

            <small>
              {deliveryAnalytics.deliveryRate.toFixed(
                0
              )}
              % delivered
            </small>
          </div>
        </div>

        <div className="report-kpi-card">
          <div className="report-kpi-icon">
            ▤
          </div>

          <div>
            <span>Inventory</span>

            <strong>
              {loading
                ? "..."
                : formatNumber(
                    inventoryAnalytics.available
                  )}
            </strong>

            <small>
              {inventoryAnalytics.totalMaterials} materials
            </small>
          </div>
        </div>
      </div>

      {/* ===================================================
          SALES + PAYMENT TRENDS
      =================================================== */}

      <div className="report-grid-two">
        <div className="report-panel">
          <div className="report-panel-header">
            <div>
              <h3>Order Value Trend</h3>

              <p>
                Monthly order value based on order dates
              </p>
            </div>

            <span className="report-badge">
              Sales
            </span>
          </div>

          <TrendChart
            items={monthlyOrderTrend}
            valueFormatter={formatCurrency}
          />
        </div>

        <div className="report-panel">
          <div className="report-panel-header">
            <div>
              <h3>Payment Collection Trend</h3>

              <p>
                Completed payment collection by month
              </p>
            </div>

            <span className="report-badge">
              Cash Flow
            </span>
          </div>

          <TrendChart
            items={monthlyPaymentTrend}
            valueFormatter={formatCurrency}
          />
        </div>
      </div>

      {/* ===================================================
          ORDER STATUS + QUOTATION STATUS
      =================================================== */}

      <div className="report-grid-two">
        <div className="report-panel">
          <div className="report-panel-header">
            <div>
              <h3>Order Status</h3>

              <p>
                Current distribution of order statuses
              </p>
            </div>
          </div>

          <StatusChart
            items={orderAnalytics.statusItems}
          />
        </div>

        <div className="report-panel">
          <div className="report-panel-header">
            <div>
              <h3>Quotation Status</h3>

              <p>
                Quotation pipeline distribution
              </p>
            </div>
          </div>

          <StatusChart
            items={quotationAnalytics.statusItems}
          />
        </div>
      </div>

      {/* ===================================================
          QUOTATION CONVERSION
      =================================================== */}

      <div className="report-panel conversion-panel">
        <div className="report-panel-header">
          <div>
            <h3>Quotation → Order Conversion</h3>

            <p>
              Approved quotations that have been linked
              to actual orders
            </p>
          </div>

          <span className="conversion-rate">
            {conversionAnalytics.conversionRate.toFixed(
              1
            )}
            %
          </span>
        </div>

        <div className="conversion-content">
          <div className="conversion-bar-area">
            <div className="conversion-labels">
              <span>
                Approved Quotations
              </span>

              <strong>
                {conversionAnalytics.approvedCount}
              </strong>
            </div>

            <div className="conversion-track">
              <div
                className="conversion-fill"
                style={{
                  width: `${Math.min(
                    conversionAnalytics.conversionRate,
                    100
                  )}%`,
                }}
              ></div>
            </div>

            <div className="conversion-labels">
              <span>
                Converted to Orders
              </span>

              <strong>
                {
                  conversionAnalytics.convertedApproved
                }
              </strong>
            </div>
          </div>

          <div className="conversion-summary">
            <div>
              <span>Total Quotation Value</span>

              <strong>
                {formatCurrency(
                  quotationAnalytics.totalValue
                )}
              </strong>
            </div>

            <div>
              <span>Approved Value</span>

              <strong>
                {formatCurrency(
                  quotationAnalytics.approvedValue
                )}
              </strong>
            </div>
          </div>
        </div>
      </div>

      {/* ===================================================
          PRODUCTION + DELIVERY
      =================================================== */}

      <div className="report-grid-two">
        <div className="report-panel">
          <div className="report-panel-header">
            <div>
              <h3>Production Overview</h3>

              <p>
                Production workload and completion
              </p>
            </div>

            <span className="report-badge">
              {productionAnalytics.completionRate.toFixed(
                0
              )}
              % Complete
            </span>
          </div>

          <div className="mini-stat-grid">
            <div className="mini-stat">
              <span>Total</span>
              <strong>
                {productionAnalytics.total}
              </strong>
            </div>

            <div className="mini-stat">
              <span>Pending</span>
              <strong>
                {productionAnalytics.pending}
              </strong>
            </div>

            <div className="mini-stat">
              <span>In Progress</span>
              <strong>
                {productionAnalytics.inProgress}
              </strong>
            </div>

            <div className="mini-stat">
              <span>Quality Check</span>
              <strong>
                {productionAnalytics.qualityCheck}
              </strong>
            </div>

            <div className="mini-stat">
              <span>Completed</span>
              <strong>
                {productionAnalytics.completed}
              </strong>
            </div>
          </div>

          <div className="subsection-title">
            Production by Department
          </div>

          <BarChart
            items={
              productionAnalytics.departmentItems
            }
            valueFormatter={formatNumber}
          />
        </div>

        <div className="report-panel">
          <div className="report-panel-header">
            <div>
              <h3>Delivery Overview</h3>

              <p>
                Delivery pipeline and completion
              </p>
            </div>

            <span className="report-badge">
              {deliveryAnalytics.deliveryRate.toFixed(
                0
              )}
              % Delivered
            </span>
          </div>

          <div className="mini-stat-grid">
            <div className="mini-stat">
              <span>Total</span>
              <strong>
                {deliveryAnalytics.total}
              </strong>
            </div>

            <div className="mini-stat">
              <span>Pending</span>
              <strong>
                {deliveryAnalytics.pending}
              </strong>
            </div>

            <div className="mini-stat">
              <span>Scheduled</span>
              <strong>
                {deliveryAnalytics.scheduled}
              </strong>
            </div>

            <div className="mini-stat">
              <span>Out for Delivery</span>
              <strong>
                {deliveryAnalytics.outForDelivery}
              </strong>
            </div>

            <div className="mini-stat">
              <span>Delivered</span>
              <strong>
                {deliveryAnalytics.delivered}
              </strong>
            </div>
          </div>

          <div className="subsection-title">
            Delivery Status
          </div>

          <BarChart
            items={
              deliveryAnalytics.statusItems
            }
            valueFormatter={formatNumber}
          />
        </div>
      </div>

      {/* ===================================================
          INVENTORY + PAYMENT METHODS
      =================================================== */}

      <div className="report-grid-two">
        <div className="report-panel">
          <div className="report-panel-header">
            <div>
              <h3>Inventory Overview</h3>

              <p>
                Current material availability
              </p>
            </div>

            <span className="report-badge">
              Current Stock
            </span>
          </div>

          <div className="inventory-summary">
            <div>
              <span>Available</span>

              <strong>
                {formatNumber(
                  inventoryAnalytics.available
                )}
              </strong>
            </div>

            <div>
              <span>Reserved</span>

              <strong>
                {formatNumber(
                  inventoryAnalytics.reserved
                )}
              </strong>
            </div>

            <div>
              <span>Physical</span>

              <strong>
                {formatNumber(
                  inventoryAnalytics.totalPhysical
                )}
              </strong>
            </div>
          </div>

          <div className="subsection-title">
            Available Stock by Material
          </div>

          <BarChart
            items={
              inventoryAnalytics.materialItems
            }
            valueFormatter={formatNumber}
          />

          <div className="inventory-note">
            Stock transaction history is currently
            empty, so movement trends are not fabricated.
          </div>
        </div>

        <div className="report-panel">
          <div className="report-panel-header">
            <div>
              <h3>Payment Methods</h3>

              <p>
                Payment amount by recorded method
              </p>
            </div>

            <span className="report-badge">
              Completed + Pending
            </span>
          </div>

          <BarChart
            items={
              paymentAnalytics.methodItems
            }
            valueFormatter={formatCurrency}
          />

          <div className="payment-summary">
            <div>
              <span>Collected</span>

              <strong>
                {formatCurrency(
                  paymentAnalytics.collectedAmount
                )}
              </strong>
            </div>

            <div>
              <span>Pending</span>

              <strong>
                {formatCurrency(
                  paymentAnalytics.pendingAmount
                )}
              </strong>
            </div>
          </div>
        </div>
      </div>

      {/* ===================================================
          TOP CUSTOMERS
      =================================================== */}

      <div className="report-panel">
        <div className="report-panel-header">
          <div>
            <h3>Top Customers by Order Value</h3>

            <p>
              Customers ranked by order value in the
              selected period
            </p>
          </div>

          <span className="report-badge">
            {customerAnalytics.activeCustomers} Active
          </span>
        </div>

        <div className="customer-report-list">
          {customerAnalytics.topCustomers.length ===
          0 ? (
            <div className="chart-empty">
              No customer order data available
            </div>
          ) : (
            customerAnalytics.topCustomers.map(
              (customer, index) => {
                const maxValue =
                  customerAnalytics.topCustomers[0]
                    ?.value || 1;

                const width =
                  (customer.value / maxValue) *
                  100;

                return (
                  <div
                    className="customer-report-row"
                    key={customer.label}
                  >
                    <div className="customer-rank">
                      #{index + 1}
                    </div>

                    <div className="customer-main">
                      <div className="customer-name">
                        {customer.label}
                      </div>

                      <div className="customer-progress">
                        <div
                          style={{
                            width: `${width}%`,
                          }}
                        ></div>
                      </div>
                    </div>

                    <div className="customer-orders">
                      {customer.count} order
                      {customer.count !== 1
                        ? "s"
                        : ""}
                    </div>

                    <strong className="customer-value">
                      {formatCurrency(
                        customer.value
                      )}
                    </strong>
                  </div>
                );
              }
            )
          )}
        </div>
      </div>

      {/* ===================================================
          RECENT ORDERS
      =================================================== */}

      <div className="report-panel">
        <div className="report-panel-header">
          <div>
            <h3>Recent Orders</h3>

            <p>
              Latest orders included in the selected
              report period
            </p>
          </div>

          <span className="report-badge">
            {filteredOrders.length} Total
          </span>
        </div>

        <div className="table-wrapper reports-table-wrapper">
          <table className="reports-table">
            <thead>
              <tr>
                <th>ORDER</th>
                <th>CUSTOMER</th>
                <th>DATE</th>
                <th>STATUS</th>
                <th>SUBTOTAL</th>
                <th>TAX</th>
                <th>TOTAL</th>
                <th>EXPECTED DELIVERY</th>
              </tr>
            </thead>

            <tbody>
              {recentOrders.length === 0 ? (
                <tr>
                  <td
                    colSpan="8"
                    className="table-message"
                  >
                    No orders found for the selected
                    period.
                  </td>
                </tr>
              ) : (
                recentOrders.map((order) => {
                  const status = String(
                    order.status || "UNKNOWN"
                  ).toUpperCase();

                  return (
                    <tr key={order.id}>
                      <td>
                        <strong>
                          {order.order_number ||
                            `ORD-${order.id}`}
                        </strong>
                      </td>

                      <td>
                        {order.customer ||
                          `Customer #${
                            order.customer_id ||
                            "—"
                          }`}
                      </td>

                      <td>
                        {formatDate(
                          order.order_date
                        )}
                      </td>

                      <td>
                        <span
                          className={`status ${status
                            .toLowerCase()
                            .replaceAll(
                              "_",
                              "-"
                            )}`}
                        >
                          {titleCase(status)}
                        </span>
                      </td>

                      <td>
                        {formatCurrency(
                          order.subtotal
                        )}
                      </td>

                      <td>
                        {formatCurrency(
                          order.tax_amount
                        )}
                      </td>

                      <td>
                        <strong>
                          {formatCurrency(
                            order.total_amount
                          )}
                        </strong>
                      </td>

                      <td>
                        {formatDate(
                          order.expected_delivery_date
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ===================================================
          REPORT FOOTER
      =================================================== */}

      <div className="reports-footer">
        <div>
          <span className="report-online-dot"></span>

          <strong>
            Reports connected to live API data
          </strong>
        </div>

        <span>
          {lastUpdated
            ? `Last updated ${lastUpdated.toLocaleTimeString(
                "en-IN",
                {
                  hour: "2-digit",
                  minute: "2-digit",
                }
              )}`
            : "Waiting for data"}
        </span>
      </div>
    </section>
  );
}

export default Reports;