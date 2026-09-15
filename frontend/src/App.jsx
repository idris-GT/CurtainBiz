import { useEffect, useState } from "react";
import "./App.css";
import api from "./api/client";

import Customers from "./Customers";
import Products from "./Products";
import Employees from "./Employees";
import Inventory from "./Inventory";
import StockTransactions from "./StockTransactions";
import Quotations from "./Quotations";
import Orders from "./Orders";
import Production from "./Production";
import ProductionTasks from "./ProductionTasks";
import Deliveries from "./Deliveries";
import Payments from "./Payments";
import Queries from "./Queries";
import Reports from "./Reports";
import AdminIntelligence from "./AdminIntelligence";
import SalesIntelligence from "./SalesIntelligence";
import SettingsPage from "./Settings";

const menuItems = [
  { name: "Dashboard", icon: "âŒ‚" },
  { name: "Customers", icon: "â™™" },
  { name: "Products", icon: "â–£" },
  { name: "Employees", icon: "â™Ÿ" },
  { name: "Inventory", icon: "â–¤" },
  { name: "Stock Transactions", icon: "â‡„" },
  { name: "Quotations", icon: "â–§" },
  { name: "Orders", icon: "â—«" },
  { name: "Production", icon: "âš™" },
  { name: "Deliveries", icon: "âžœ" },
  { name: "Payments", icon: "â‚¹" },
  { name: "Queries", icon: "?" },
  { name: "Reports", icon: "â–¥" },
  { name: "Business Intelligence", icon: "â—ˆ" },
  { name: "Sales Intelligence", icon: "â—‰" },
];

function getArray(response) {
  if (Array.isArray(response.data)) return response.data;
  if (Array.isArray(response.data?.data)) return response.data.data;
  if (Array.isArray(response.data?.items)) return response.data.items;
  return [];
}

const PAGE_PERMISSIONS = {
  Customers: "customers.view",
  Products: "products.view",
  Employees: "employees.view",
  Inventory: "inventory.view",
  "Stock Transactions": "inventory.view",
  Quotations: "quotations.view",
  Orders: "orders.view",
  Production: "production.view",
  Deliveries: "deliveries.view",
  Payments: "payments.view",
  Queries: "queries.view",
  Reports: "reports.view",
  "Business Intelligence": "reports.view",
  "Sales Intelligence": "reports.view",
};

const ACTION_PERMISSIONS = {
  Customers: "customers.manage",
  Products: "products.manage",
  Employees: "employees.manage",
  Inventory: "inventory.manage",
  "Stock Transactions": "inventory.manage",
  Quotations: "quotations.manage",
  Orders: "orders.manage",
  Production: "production.manage",
  Deliveries: "deliveries.manage",
  Payments: "payments.manage",
  Queries: "queries.manage",
};

function pagePermission(page) {
  return PAGE_PERMISSIONS[page] || null;
}

function hasPermission(permissionSet, permissionName) {
  return Boolean(permissionName && permissionSet.has(permissionName));
}

function getInitials(name) {
  const value = String(name || "User").trim();

  if (!value) return "U";

  return value
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

function formatRoleName(role) {
  if (!role) return "User";

  return String(role)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatActivityAction(action) {
  return String(action || "â€”")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatActivityDate(value) {
  if (!value) return "â€”";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function App() {
  const [activePage, setActivePage] = useState("Dashboard");

  const [accessLoading, setAccessLoading] = useState(true);
  const [accessError, setAccessError] = useState("");
  const [currentUser, setCurrentUser] = useState({
    user_id: "",
    email: "",
    role_id: null,
    role: "",
    role_description: "",
  });
  const [permissions, setPermissions] = useState([]);
  const [profileOpen, setProfileOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [settingsSection, setSettingsSection] = useState("profile");
  const [displayName, setDisplayName] = useState(() => localStorage.getItem("curtainbiz_display_name") || "");
  const [profileSaved, setProfileSaved] = useState(false);


  const resolvedDisplayName = displayName || currentUser.email?.split("@")[0]?.replace(/[._-]+/g, " ") || "User";

  const notificationItems = [
    dashboardData.payments > 0 ? { title: "Pending payments", message: `${formatCurrency(dashboardData.payments)} is currently pending.`, icon: "₹" } : null,
    dashboardData.orders > 0 ? { title: "Active orders", message: `${dashboardData.orders} order${dashboardData.orders === 1 ? "" : "s"} require attention.`, icon: "◫" } : null,
    dashboardData.production > 0 ? { title: "Production workload", message: `${dashboardData.production} production item${dashboardData.production === 1 ? "" : "s"} are active.`, icon: "⚙" } : null,
  ].filter(Boolean);

  const saveProfile = () => {
    localStorage.setItem("curtainbiz_display_name", displayName.trim());
    setDisplayName(displayName.trim());
    setProfileSaved(true);
    window.setTimeout(() => setProfileSaved(false), 2200);
  };

  const signOut = () => {
    localStorage.removeItem("access_token");
    window.location.href = "/login";
  };

  const [dashboardData, setDashboardData] = useState({
    customers: 0,
    orders: 0,
    production: 0,
    payments: 0,
    recentOrders: [],
    recentActivities: [],
  });

  const permissionSet = new Set(permissions);

  const [loadingDashboard, setLoadingDashboard] = useState(true);
  const [dashboardError, setDashboardError] = useState("");
  const [activityError, setActivityError] = useState("");

  const loadAccess = async () => {
    try {
      setAccessLoading(true);
      setAccessError("");

      const accessResponse = await api.get(
        "/role-permissions/me"
      );

      const accessData = accessResponse.data || {};

      if (!accessData.role_id) {
        throw new Error("No active role is assigned to this user.");
      }

      setCurrentUser({
        user_id: accessData.user_id || "",
        email: accessData.email || "",
        role_id: accessData.role_id,
        role: accessData.role || "",
        role_description: accessData.role_description || "",
      });

      setPermissions(
        Array.isArray(accessData.permissions)
          ? accessData.permissions
              .map((item) => item.name)
              .filter(Boolean)
          : []
      );
    } catch (error) {
      console.error("RBAC access error:", error);

      setAccessError(
        "Unable to load your role and permissions."
      );

      setCurrentUser({
        user_id: "",
        email: "",
        role_id: null,
        role: "",
        role_description: "",
      });

      setPermissions([]);
    } finally {
      setAccessLoading(false);
    }
  };

  useEffect(() => {
    loadAccess();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoadingDashboard(true);
      setDashboardError("");
      setActivityError("");

      const canViewCustomers = hasPermission(
        permissionSet,
        "customers.view"
      );
      const canViewOrders = hasPermission(
        permissionSet,
        "orders.view"
      );
      const canViewProduction = hasPermission(
        permissionSet,
        "production.view"
      );
      const canViewPayments = hasPermission(
        permissionSet,
        "payments.view"
      );

      const [
        customersResponse,
        ordersResponse,
        productionResponse,
        paymentsResponse,
      ] = await Promise.all([
        canViewCustomers
          ? api.get("/customers/")
          : Promise.resolve({ data: [] }),
        canViewOrders
          ? api.get("/orders/")
          : Promise.resolve({ data: [] }),
        canViewProduction
          ? api.get("/production/")
          : Promise.resolve({ data: [] }),
        canViewPayments
          ? api.get("/payments/")
          : Promise.resolve({ data: [] }),
      ]);

      const customers = getArray(customersResponse);
      const orders = getArray(ordersResponse);
      const production = getArray(productionResponse);
      const payments = getArray(paymentsResponse);

      const activeOrders = orders.filter((order) => {
        const status = String(order.status || "").toUpperCase();

        return !["DELIVERED", "CANCELLED"].includes(status);
      });

      const activeProduction = production.filter((item) => {
        const status = String(item.status || "").toUpperCase();

        return !["COMPLETED", "CANCELLED"].includes(status);
      });

      const pendingPayments = payments
        .filter((payment) => {
          const status = String(
            payment.status || ""
          ).toUpperCase();

          return !["PAID", "COMPLETED"].includes(status);
        })
        .reduce((total, payment) => {
          return (
            total +
            Number(
              payment.amount ||
                payment.payment_amount ||
                payment.pending_amount ||
                0
            )
          );
        }, 0);

      const recentOrders = [...orders]
        .sort((a, b) => {
          const dateA = new Date(
            a.created_at ||
              a.order_date ||
              a.created_date ||
              0
          );

          const dateB = new Date(
            b.created_at ||
              b.order_date ||
            b.created_date ||
              0
          );

          return dateB - dateA;
        })
        .slice(0, 5);

      setDashboardData((previous) => ({
        ...previous,
        customers: customers.length,
        orders: activeOrders.length,
        production: activeProduction.length,
        payments: pendingPayments,
        recentOrders,
      }));
    } catch (error) {
      console.error("Dashboard API error:", error);

      setDashboardError(
        "Unable to load dashboard data. Please check that the backend is running."
      );
    } finally {
      setLoadingDashboard(false);
    }

    /*
      Activity logs are loaded separately.

      This is intentional:
      if the activity-log endpoint ever fails,
      the entire dashboard should NOT break.
    */
    try {
      const activityResponse = await api.get(
        "/activity-logs/"
      );

      const activities = getArray(activityResponse);

      const recentActivities = [...activities]
        .sort((a, b) => {
          const dateA = new Date(
            a.created_at || 0
          );

          const dateB = new Date(
            b.created_at || 0
          );

          return dateB - dateA;
        })
        .slice(0, 5);

      setDashboardData((previous) => ({
        ...previous,
        recentActivities,
      }));

      setActivityError("");
    } catch (error) {
      console.error(
        "Activity Logs API error:",
        error
      );

      setActivityError(
        "Activity logs are unavailable."
      );

      setDashboardData((previous) => ({
        ...previous,
        recentActivities: [],
      }));
    }
  };

  useEffect(() => {
    if (activePage === "Dashboard" && !accessLoading) {
      loadDashboard();
    }
  }, [activePage, accessLoading]);

  const navigateTo = (page) => {
    if (
      page !== "Dashboard" &&
      pagePermission(page) &&
      !hasPermission(permissionSet, pagePermission(page))
    ) {
      return;
    }

    setActivePage(page);
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(Number(value || 0));
  };

  const getOrderId = (order) => {
    return (
      order.order_code ||
      order.order_number ||
      order.order_id ||
      "â€”"
    );
  };

  const getCustomerName = (order) => {
    return (
      order.customer_name ||
      order.customer ||
      `Customer #${order.customer_id || "â€”"}`
    );
  };

  const getOrderAmount = (order) => {
    return Number(
      order.total_amount ||
        order.grand_total ||
        order.total ||
        order.amount ||
        0
    );
  };

  const getOrderStatus = (order) => {
    const status = String(
      order.status || "NEW"
    ).toUpperCase();

    return status
      .replaceAll("_", " ")
      .toLowerCase()
      .replace(/\b\w/g, (letter) =>
        letter.toUpperCase()
      );
  };

  const renderPage = () => {
    if (
      activePage !== "Dashboard" &&
      pagePermission(activePage) &&
      !hasPermission(
        permissionSet,
        pagePermission(activePage)
      )
    ) {
      return (
        <section className="empty-page">
          <div className="empty-icon">ðŸ”’</div>

          <p className="empty-eyebrow">
            ACCESS RESTRICTED
          </p>

          <h3>Permission Required</h3>

          <p>
            Your current role does not have permission
            to view this module.
          </p>

          <button
            className="primary-button"
            onClick={() => setActivePage("Dashboard")}
          >
            Back to Dashboard
          </button>
        </section>
      );
    }

    if (activePage === "Settings") {
      return <SettingsPage currentUser={currentUser} displayName={displayName} resolvedDisplayName={resolvedDisplayName} setDisplayName={setDisplayName} profileSaved={profileSaved} onSaveProfile={saveProfile} section={settingsSection} setSection={setSettingsSection} onSignOut={signOut} />;
    }

    if (activePage === "Dashboard") {
      return (
        <Dashboard
          data={dashboardData}
          loading={loadingDashboard}
          error={dashboardError}
          activityError={activityError}
          formatCurrency={formatCurrency}
          getOrderId={getOrderId}
          getCustomerName={getCustomerName}
          getOrderAmount={getOrderAmount}
          getOrderStatus={getOrderStatus}
          onNavigate={navigateTo}
          onRefresh={loadDashboard}
          userEmail={currentUser.email}
          hasPermission={(permissionName) =>
            hasPermission(
              permissionSet,
              permissionName
            )
          }
        />
      );
    }

    if (activePage === "Customers") {
      return <Customers />;
    }

    if (activePage === "Products") {
      return <Products />;
    }

    if (activePage === "Employees") {
      return <Employees />;
    }

    if (activePage === "Inventory") {
      return <Inventory />;
    }

    if (activePage === "Stock Transactions") {
      return <StockTransactions />;
    }

    if (activePage === "Quotations") {
      return <Quotations />;
    }

    if (activePage === "Orders") {
      return <Orders />;
    }

    if (activePage === "Production") {
      return <Production />;
    }

    if (activePage === "Production Tasks") {
      return <ProductionTasks />;
    }

    if (activePage === "Deliveries") {
      return <Deliveries />;
    }

    if (activePage === "Payments") {
      return <Payments />;
    }

    if (activePage === "Queries") {
      return <Queries />;
    }

    if (activePage === "Reports") {
      return <Reports />;
    }

    if (activePage === "Business Intelligence") {
      return <AdminIntelligence />;
    }

    if (activePage === "Sales Intelligence") {
      return <SalesIntelligence />;
    }

    return (
      <section className="empty-page">
        <div className="empty-icon">
          {menuItems.find(
            (item) => item.name === activePage
          )?.icon || "â–£"}
        </div>

        <p className="empty-eyebrow">
          MODULE
        </p>

        <h3>{activePage}</h3>

        <p>
          This module is next in the frontend build.
          The backend API is already available.
        </p>
      </section>
    );
  };

  if (accessLoading) {
    return (
      <div className="app">
        <main className="main">
          <section className="empty-page">
            <div className="empty-icon">â—Œ</div>

            <p className="empty-eyebrow">
              SECURITY
            </p>

            <h3>Loading your access...</h3>

            <p>
              Checking your role and permissions.
            </p>
          </section>
        </main>
      </div>
    );
  }

  if (accessError) {
    return (
      <div className="app">
        <main className="main">
          <section className="empty-page">
            <div className="empty-icon">ðŸ”’</div>

            <p className="empty-eyebrow">
              ACCESS ERROR
            </p>

            <h3>Unable to load access</h3>

            <p>{accessError}</p>

            <button
              className="primary-button"
              onClick={loadAccess}
            >
              Retry
            </button>
          </section>
        </main>
      </div>
    );
  }

  return (
    <div className="app">
      {/* SIDEBAR */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-logo">CB</div>

          <div>
            <h1>CurtainBiz</h1>
            <span>Operations Platform</span>
          </div>
        </div>

        <div className="menu-label">
          MAIN MENU
        </div>

        <nav className="navigation">
          {menuItems
            .filter(
              (item) =>
                item.name === "Dashboard" ||
                !pagePermission(item.name) ||
                hasPermission(
                  permissionSet,
                  pagePermission(item.name)
                )
            )
            .map((item) => (
              <button
                key={item.name}
                className={`nav-item ${
                  activePage === item.name
                    ? "active"
                    : ""
                }`}
                onClick={() => navigateTo(item.name)}
              >
                <span className="nav-icon">
                  {item.icon}
                </span>

                <span>{item.name}</span>
              </button>
            ))}
        </nav>

        <div className="sidebar-bottom">
          <button
            className={`nav-item ${
              activePage === "Settings"
                ? "active"
                : ""
            }`}
            onClick={() =>
              setActivePage("Settings")
            }
          >
            <span className="nav-icon">
              âš™
            </span>

            <span>Settings</span>
          </button>

          <button className="user-card" onClick={() => setProfileOpen((open) => !open)} aria-expanded={profileOpen} aria-label="Open account menu">
            <div className="avatar">{getInitials(resolvedDisplayName)}</div>
            <div className="user-info">
              <strong>{resolvedDisplayName}</strong>
              <span>{formatRoleName(currentUser.role)}</span>
            </div>
<<<<<<< ours
            <span className="user-menu">{profileOpen ? "⌃" : "⋮"}</span>
          </button>
=======

            <span className="user-menu">
              â‹®
            </span>
          </div>
>>>>>>> theirs
        </div>
      </aside>

      {/* MAIN */}
      <main className="main">
        {/* TOPBAR */}
        <header className="topbar">
          <div>
            <div className="breadcrumb">
              Workspace / {activePage}
            </div>

            <h2>{activePage}</h2>
          </div>

          <div className="topbar-actions">
            {hasPermission(
              permissionSet,
              "customers.view"
            ) && (
              <button
                className="icon-button"
                onClick={() =>
                  navigateTo("Customers")
                }
                title="Search customers"
              >
              âŒ•
              </button>
            )}

<<<<<<< ours
            <div className="notification-wrap">
              <button className="icon-button notification" title="Notifications" onClick={() => setNotificationsOpen((open) => !open)} aria-expanded={notificationsOpen}>
                ♢
                {notificationItems.length > 0 && <span></span>}
              </button>
              {notificationsOpen && (
                <div className="notification-panel">
                  <div className="notification-panel-header"><div><strong>Notifications</strong><small>Live operational signals</small></div><button onClick={() => setNotificationsOpen(false)}>×</button></div>
                  {notificationItems.length === 0 ? (
                    <div className="notification-empty"><div>✓</div><strong>You're all caught up</strong><span>No active operational alerts right now.</span></div>
                  ) : (
                    <div className="notification-list">{notificationItems.map((item) => <div className="notification-item" key={item.title}><div className="notification-icon">{item.icon}</div><div><strong>{item.title}</strong><span>{item.message}</span></div></div>)}</div>
                  )}
                </div>
              )}
            </div>
=======
            <button
              className="icon-button notification"
              title="Notifications"
              onClick={() =>
                setActivePage("Notifications")
              }
            >
              â™¢
              <span></span>
            </button>

            <div className="top-user">
              <div className="avatar">
                {getInitials(
                  currentUser.email ||
                    currentUser.role ||
                    "User"
                )}
              </div>
>>>>>>> theirs

            <button className="top-user top-user-trigger" onClick={() => setProfileOpen((open) => !open)} aria-expanded={profileOpen} aria-label="Open account menu">
              <div className="avatar">{getInitials(resolvedDisplayName)}</div>
              <div><strong>{resolvedDisplayName}</strong><small>{formatRoleName(currentUser.role)}</small></div>
              <span className="top-user-chevron">⌄</span>
            </button>
            {profileOpen && (
              <div className="profile-menu">
                <div className="profile-menu-header"><div className="avatar avatar-large">{getInitials(resolvedDisplayName)}</div><div><strong>{resolvedDisplayName}</strong><span>{currentUser.email || "No email"}</span><small>{formatRoleName(currentUser.role)}</small></div></div>
                <div className="profile-menu-divider" />
                <button onClick={() => { setSettingsSection("profile"); setActivePage("Settings"); setProfileOpen(false); }}><span>◉</span> My Profile</button>
                <button onClick={() => { setSettingsSection("preferences"); setActivePage("Settings"); setProfileOpen(false); }}><span>⚙</span> Account Settings</button>
                <button onClick={() => { setSettingsSection("security"); setActivePage("Settings"); setProfileOpen(false); }}><span>⌁</span> Security</button>
                <div className="profile-menu-divider" />
                <button className="profile-signout" onClick={signOut}><span>↪</span> Sign out</button>
              </div>
            )}
          </div>
        </header>

        {renderPage()}
      </main>
    </div>
  );
}

/* =========================================================
   DASHBOARD
========================================================= */

function Dashboard({
  data,
  loading,
  error,
  activityError,
  formatCurrency,
  getOrderId,
  getCustomerName,
  getOrderAmount,
  getOrderStatus,
  onNavigate,
  onRefresh,
  userEmail,
  hasPermission,
}) {
  const stats = [
    {
      title: "Total Customers",
      value: data.customers,
      icon: "â™™",
    },
    {
      title: "Active Orders",
      value: data.orders,
      icon: "â—«",
    },
    {
      title: "Production",
      value: data.production,
      icon: "âš™",
    },
    {
      title: "Pending Payments",
      value: formatCurrency(data.payments),
      icon: "â‚¹",
    },
  ];

  return (
    <section className="content">
      {/* WELCOME */}
      <div className="welcome">
        <div>
          <p className="eyebrow">
            OVERVIEW
          </p>

          <h3>
            Good day, {userEmail || "User"} ðŸ‘‹
          </h3>

          <p>
            Here's what's happening with your
            business today.
          </p>
        </div>

        {hasPermission("orders.manage") && (
          <button
            className="primary-button"
            onClick={() =>
              onNavigate("Orders")
            }
          >
            + New Order
          </button>
        )}
      </div>

      {/* CONNECTION ERROR */}
      {error && (
        <div className="dashboard-error">
          <div>
            <strong>
              Dashboard connection problem
            </strong>

            <span>{error}</span>
          </div>

          <button onClick={onRefresh}>
            Retry
          </button>
        </div>
      )}

      {/* STATS */}
      <div className="stats-grid">
        {stats.map((stat) => (
          <div
            className="stat-card"
            key={stat.title}
          >
            <div className="stat-top">
              <div className="stat-icon">
                {stat.icon}
              </div>

              <span className="live-badge">
                Live
              </span>
            </div>

            <p>{stat.title}</p>

            <h4>
              {loading ? "..." : stat.value}
            </h4>
          </div>
        ))}
      </div>

      {/* LOWER GRID */}
      <div className="dashboard-grid">
        {/* RECENT ORDERS */}
        <div className="panel orders-panel">
          <div className="panel-header">
            <div>
              <h3>Recent Orders</h3>

              <p>
                Latest customer orders from the
                database
              </p>
            </div>

            <button
              className="text-button"
              onClick={() =>
                onNavigate("Orders")
              }
            >
              View all â†’
            </button>
          </div>

          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>ORDER</th>
                  <th>CUSTOMER</th>
                  <th>PRODUCT</th>
                  <th>AMOUNT</th>
                  <th>STATUS</th>
                </tr>
              </thead>

              <tbody>
                {loading ? (
                  <tr>
                    <td
                      colSpan="5"
                      className="table-message"
                    >
                      Loading orders...
                    </td>
                  </tr>
                ) : data.recentOrders.length ===
                  0 ? (
                  <tr>
                    <td
                      colSpan="5"
                      className="table-message"
                    >
                      No orders found.
                    </td>
                  </tr>
                ) : (
                  data.recentOrders.map(
                    (order, index) => {
                      const status =
                        getOrderStatus(order);

                      return (
                        <tr
                          key={
                            order.order_id ||
                            order.id ||
                            index
                          }
                        >
                          <td>
                            <strong>
                              {getOrderId(
                                order
                              )}
                            </strong>
                          </td>

                          <td>
                            {getCustomerName(
                              order
                            )}
                          </td>

                          <td>
                            {order.product_name ||
                              order.product ||
                              "Order items"}
                          </td>

                          <td>
                            <strong>
                              {formatCurrency(
                                getOrderAmount(
                                  order
                                )
                              )}
                            </strong>
                          </td>

                          <td>
                            <span
                              className={`status ${status
                                .toLowerCase()
                                .replaceAll(
                                  " ",
                                  "-"
                                )}`}
                            >
                              {status}
                            </span>
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

        {/* QUICK ACTIONS */}
        <div className="panel quick-panel">
          <div className="panel-header">
            <div>
              <h3>Quick Actions</h3>

              <p>
                Common operations
              </p>
            </div>
          </div>

          <div className="quick-actions">
            {hasPermission("quotations.manage") && (
              <button
                onClick={() =>
                  onNavigate("Quotations")
                }
              >
              <span>ï¼‹</span>

              <div>
                <strong>
                  Create Quotation
                </strong>

                <small>
                  Prepare a new quotation
                </small>
              </div>
              </button>
            )}

            {hasPermission("customers.manage") && (
              <button
                onClick={() =>
                  onNavigate("Customers")
                }
              >
              <span>â™™</span>

              <div>
                <strong>
                  Add Customer
                </strong>

                <small>
                  Register a new customer
                </small>
              </div>
              </button>
            )}

            {hasPermission("inventory.view") && (
              <button
                onClick={() =>
                  onNavigate("Inventory")
                }
              >
              <span>â–¤</span>

              <div>
                <strong>
                  Check Inventory
                </strong>

                <small>
                  View current stock
                </small>
              </div>
              </button>
            )}

            {hasPermission("production.manage") && (
              <button
                onClick={() =>
                  onNavigate("Production")
                }
              >
              <span>âš™</span>

              <div>
                <strong>
                  Production Tasks
                </strong>

                <small>
                  Manage production workflow
                </small>
              </div>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* =====================================================
          RECENT ACTIVITY
          
          This replaces the need for an Activity Logs
          sidebar module.

          The data comes directly from:
          GET /activity-logs/
      ===================================================== */}

      <div
        className="panel"
        style={{
          marginTop: "24px",
          overflow: "hidden",
        }}
      >
        <div
          className="panel-header"
          style={{
            alignItems: "center",
          }}
        >
          <div>
            <h3>Recent Activity</h3>

            <p>
              Recent system actions and audit events
            </p>
          </div>

          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "6px 10px",
              borderRadius: "6px",
              background: "#f1f5f9",
              color: "#52657d",
              fontSize: "12px",
              fontWeight: "700",
            }}
          >
            ðŸ” Audit Log
          </span>
        </div>

        {activityError ? (
          <div
            style={{
              padding: "20px",
              color: "#7b8794",
              fontSize: "14px",
            }}
          >
            Activity logs are currently unavailable.
          </div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>ACTION</th>
                  <th>ENTITY</th>
                  <th>ENTITY ID</th>
                  <th>DESCRIPTION</th>
                  <th>TIME</th>
                </tr>
              </thead>

              <tbody>
                {loading ? (
                  <tr>
                    <td
                      colSpan="5"
                      className="table-message"
                    >
                      Loading activity...
                    </td>
                  </tr>
                ) : data.recentActivities.length ===
                  0 ? (
                  <tr>
                    <td
                      colSpan="5"
                      className="table-message"
                    >
                      No activity logs found.
                    </td>
                  </tr>
                ) : (
                  data.recentActivities.map(
                    (activity, index) => (
                      <tr
                        key={
                          activity.id ||
                          index
                        }
                      >
                        <td>
                          <span
                            className="status"
                            style={{
                              display:
                                "inline-block",
                              whiteSpace:
                                "nowrap",
                            }}
                          >
                            {formatActivityAction(
                              activity.action
                            )}
                          </span>
                        </td>

                        <td>
                          <strong>
                            {activity.entity_type ||
                              "â€”"}
                          </strong>
                        </td>

                        <td>
                          {activity.entity_id ??
                            "â€”"}
                        </td>

                        <td>
                          {activity.description ||
                            "â€”"}
                        </td>

                        <td>
                          {formatActivityDate(
                            activity.created_at
                          )}
                        </td>
                      </tr>
                    )
                  )
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* SYSTEM STATUS */}
      <div className="system-status">
        <div>
          <span className="online-dot"></span>

          <strong>
            {error
              ? "System connection issue"
              : "System operational"}
          </strong>
        </div>

        <span>
          Backend API{" "}
          {error
            ? "connection issue"
            : "connected"}
        </span>

        <span>
          Database{" "}
          {error ? "unavailable" : "healthy"}
        </span>

        <span>
          Last sync:{" "}
          {loading
            ? "Syncing..."
            : "Just now"}
        </span>
      </div>
    </section>
  );
}

export default App;
