import { useEffect, useMemo, useState } from "react";

const STORAGE_KEYS = {
  displayName: "curtainbiz_display_name",
  phone: "curtainbiz_profile_phone",
  employeeId: "curtainbiz_employee_id",
  department: "curtainbiz_profile_department",
  jobTitle: "curtainbiz_profile_job_title",
  photo: "curtainbiz_profile_photo",
  theme: "curtainbiz_theme",
  compact: "curtainbiz_compact_mode",
  notifications: "curtainbiz_notifications_enabled",
};

const getStored = (key, fallback = "") => {
  try {
    return localStorage.getItem(key) ?? fallback;
  } catch {
    return fallback;
  }
};

const getStoredBoolean = (key, fallback = false) => {
  const value = getStored(key, "");
  if (value === "") return fallback;
  return value === "true";
};

const formatRole = (role) => {
  if (!role) return "User";

  return String(role)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
};

const initials = (name) => {
  const value = String(name || "User").trim();

  if (!value) return "U";

  return value
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part.charAt(0))
    .join("")
    .toUpperCase();
};

function SettingsPage({
  currentUser,
  displayName,
  resolvedDisplayName,
  setDisplayName,
  profileSaved,
  onSaveProfile,
  section,
  setSection,
  onSignOut,
}) {
  const [phone, setPhone] = useState(() =>
    getStored(STORAGE_KEYS.phone)
  );

  const [employeeId, setEmployeeId] = useState(() =>
    getStored(
      STORAGE_KEYS.employeeId,
      currentUser?.user_id || ""
    )
  );

  const [department, setDepartment] = useState(() =>
    getStored(STORAGE_KEYS.department)
  );

  const [jobTitle, setJobTitle] = useState(() =>
    getStored(STORAGE_KEYS.jobTitle)
  );

  const [photo, setPhoto] = useState(() =>
    getStored(STORAGE_KEYS.photo)
  );

  const [theme, setTheme] = useState(() =>
    getStored(STORAGE_KEYS.theme, "light")
  );

  const [compactMode, setCompactMode] = useState(() =>
    getStoredBoolean(STORAGE_KEYS.compact, false)
  );

  const [notificationsEnabled, setNotificationsEnabled] =
    useState(() =>
      getStoredBoolean(
        STORAGE_KEYS.notifications,
        true
      )
    );

  const [profileMessage, setProfileMessage] = useState("");
  const [photoMessage, setPhotoMessage] = useState("");

  const roleName = formatRole(currentUser?.role);

  const email = currentUser?.email || "Not available";

  const userId = currentUser?.user_id || "Not available";

  const profileInitials = useMemo(
    () => initials(resolvedDisplayName),
    [resolvedDisplayName]
  );

  useEffect(() => {
    document.documentElement.dataset.theme = theme;

    localStorage.setItem(
      STORAGE_KEYS.theme,
      theme
    );
  }, [theme]);

  useEffect(() => {
    document.documentElement.dataset.compact =
      compactMode ? "true" : "false";

    localStorage.setItem(
      STORAGE_KEYS.compact,
      String(compactMode)
    );
  }, [compactMode]);

  useEffect(() => {
    localStorage.setItem(
      STORAGE_KEYS.notifications,
      String(notificationsEnabled)
    );
  }, [notificationsEnabled]);

  const saveExtendedProfile = () => {
    localStorage.setItem(
      STORAGE_KEYS.phone,
      phone.trim()
    );

    localStorage.setItem(
      STORAGE_KEYS.employeeId,
      employeeId.trim()
    );

    localStorage.setItem(
      STORAGE_KEYS.department,
      department.trim()
    );

    localStorage.setItem(
      STORAGE_KEYS.jobTitle,
      jobTitle.trim()
    );

    setProfileMessage(
      "Profile information saved successfully."
    );

    window.setTimeout(
      () => setProfileMessage(""),
      2500
    );

    onSaveProfile();
  };

  const handlePhotoChange = (event) => {
    const file = event.target.files?.[0];

    if (!file) return;

    if (!file.type.startsWith("image/")) {
      setPhotoMessage(
        "Please select a valid image file."
      );
      return;
    }

    if (file.size > 2 * 1024 * 1024) {
      setPhotoMessage(
        "Profile photo must be smaller than 2 MB."
      );
      return;
    }

    const reader = new FileReader();

    reader.onload = () => {
      const result = String(
        reader.result || ""
      );

      setPhoto(result);

      localStorage.setItem(
        STORAGE_KEYS.photo,
        result
      );

      setPhotoMessage(
        "Profile photo updated."
      );

      window.setTimeout(
        () => setPhotoMessage(""),
        2200
      );
    };

    reader.readAsDataURL(file);
  };

  const removePhoto = () => {
    setPhoto("");

    localStorage.removeItem(
      STORAGE_KEYS.photo
    );

    setPhotoMessage(
      "Profile photo removed."
    );

    window.setTimeout(
      () => setPhotoMessage(""),
      2200
    );
  };

  const resetPreferences = () => {
    setTheme("light");
    setCompactMode(false);
    setNotificationsEnabled(true);

    localStorage.setItem(
      STORAGE_KEYS.theme,
      "light"
    );

    localStorage.setItem(
      STORAGE_KEYS.compact,
      "false"
    );

    localStorage.setItem(
      STORAGE_KEYS.notifications,
      "true"
    );
  };

  const settingsItems = [
    {
      id: "profile",
      icon: "👤",
      title: "Profile",
      description: "Personal and employee information",
    },
    {
      id: "appearance",
      icon: "◐",
      title: "Appearance",
      description: "Theme and layout preferences",
    },
    {
      id: "notifications",
      icon: "🔔",
      title: "Notifications",
      description: "Operational alert preferences",
    },
    {
      id: "security",
      icon: "🔐",
      title: "Security",
      description: "Account and session controls",
    },
    {
      id: "about",
      icon: "ⓘ",
      title: "About",
      description: "CurtainBiz system information",
    },
  ];

  return (
    <section className="cb-settings-page">
      <style>{`
        .cb-settings-page {
          min-height: calc(100vh - 84px);
          padding: 30px 34px 50px;
          background: var(--cb-bg, #f5f7fb);
          color: var(--cb-text, #172033);
        }

        .cb-settings-header {
          margin-bottom: 24px;
        }

        .cb-settings-eyebrow {
          margin: 0 0 7px;
          color: #8791a1;
          font-size: 10px;
          font-weight: 800;
          letter-spacing: 1.4px;
        }

        .cb-settings-header h1 {
          margin: 0;
          font-size: 26px;
          letter-spacing: -0.7px;
        }

        .cb-settings-header p {
          margin: 7px 0 0;
          color: #7d8797;
          font-size: 12px;
        }

        .cb-settings-layout {
          display: grid;
          grid-template-columns: 250px minmax(0, 1fr);
          gap: 20px;
          max-width: 1180px;
        }

        .cb-settings-nav,
        .cb-settings-card {
          background: var(--cb-card, #fff);
          border: 1px solid var(--cb-border, #e4e8ef);
          border-radius: 13px;
        }

        .cb-settings-nav {
          padding: 9px;
          height: fit-content;
        }

        .cb-settings-nav-item {
          width: 100%;
          border: 0;
          background: transparent;
          color: var(--cb-muted, #667185);
          display: flex;
          align-items: center;
          gap: 11px;
          padding: 12px;
          border-radius: 9px;
          text-align: left;
          cursor: pointer;
          transition: 0.18s ease;
        }

        .cb-settings-nav-item:hover {
          background: var(--cb-hover, #f4f6f9);
          color: var(--cb-text, #172033);
        }

        .cb-settings-nav-item.active {
          background: var(--cb-active, #edf1f6);
          color: var(--cb-text, #172033);
        }

        .cb-settings-nav-icon {
          width: 30px;
          height: 30px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 8px;
          background: var(--cb-icon-bg, #f0f3f7);
          font-size: 14px;
          flex-shrink: 0;
        }

        .cb-settings-nav-copy strong,
        .cb-settings-nav-copy small {
          display: block;
        }

        .cb-settings-nav-copy strong {
          font-size: 11px;
        }

        .cb-settings-nav-copy small {
          margin-top: 3px;
          color: #8b94a3;
          font-size: 9px;
        }

        .cb-settings-card {
          padding: 26px;
          min-height: 520px;
        }

        .cb-settings-card-header {
          padding-bottom: 20px;
          margin-bottom: 22px;
          border-bottom: 1px solid var(--cb-border, #e9edf2);
        }

        .cb-settings-card-header h2 {
          margin: 0;
          font-size: 18px;
        }

        .cb-settings-card-header p {
          margin: 6px 0 0;
          color: #7f8999;
          font-size: 11px;
        }

        .cb-profile-hero {
          display: flex;
          align-items: center;
          gap: 17px;
          padding: 17px;
          border: 1px solid var(--cb-border, #e4e8ef);
          background: var(--cb-soft, #fafbfd);
          border-radius: 12px;
          margin-bottom: 24px;
        }

        .cb-profile-avatar {
          width: 76px;
          height: 76px;
          border-radius: 50%;
          overflow: hidden;
          background: #172033;
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 800;
          font-size: 23px;
          flex-shrink: 0;
          border: 3px solid var(--cb-card, #fff);
          box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        }

        .cb-profile-avatar img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }

        .cb-profile-hero h3 {
          margin: 0;
          font-size: 17px;
        }

        .cb-profile-hero p {
          margin: 5px 0 0;
          color: #7e8999;
          font-size: 11px;
        }

        .cb-profile-actions {
          display: flex;
          gap: 8px;
          margin-top: 11px;
          flex-wrap: wrap;
        }

        .cb-small-button {
          border: 1px solid var(--cb-border, #dfe4eb);
          background: var(--cb-card, #fff);
          color: var(--cb-text, #263248);
          border-radius: 7px;
          padding: 7px 10px;
          font-size: 10px;
          cursor: pointer;
        }

        .cb-small-button:hover {
          background: var(--cb-hover, #f4f6f9);
        }

        .cb-small-button.danger {
          color: #a34d4d;
        }

        .cb-hidden-file {
          display: none;
        }

        .cb-profile-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 15px;
        }

        .cb-field {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .cb-field.full {
          grid-column: 1 / -1;
        }

        .cb-field label {
          color: #707b8d;
          font-size: 10px;
          font-weight: 700;
        }

        .cb-field input {
          width: 100%;
          border: 1px solid var(--cb-border, #dfe4eb);
          background: var(--cb-input, #fff);
          color: var(--cb-text, #202c40);
          border-radius: 8px;
          padding: 10px 11px;
          font-size: 11px;
          outline: none;
        }

        .cb-field input:focus {
          border-color: #8b96a7;
          box-shadow: 0 0 0 3px rgba(80, 95, 118, 0.08);
        }

        .cb-field input[readonly] {
          background: var(--cb-readonly, #f7f8fa);
          color: #7b8595;
        }

        .cb-profile-footer {
          margin-top: 20px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }

        .cb-save-button {
          border: 0;
          background: #172033;
          color: white;
          border-radius: 8px;
          padding: 10px 16px;
          font-size: 11px;
          font-weight: 700;
          cursor: pointer;
        }

        .cb-save-button:hover {
          background: #26344b;
        }

        .cb-success {
          color: #3f8661;
          font-size: 10px;
          font-weight: 600;
        }

        .cb-preference-list {
          display: flex;
          flex-direction: column;
          gap: 11px;
        }

        .cb-preference-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 20px;
          padding: 16px;
          border: 1px solid var(--cb-border, #e4e8ef);
          background: var(--cb-soft, #fafbfd);
          border-radius: 10px;
        }

        .cb-preference-row strong {
          display: block;
          font-size: 12px;
        }

        .cb-preference-row p {
          margin: 4px 0 0;
          color: #818b9b;
          font-size: 10px;
          line-height: 1.5;
        }

        .cb-select {
          border: 1px solid var(--cb-border, #dfe4eb);
          background: var(--cb-input, #fff);
          color: var(--cb-text, #202c40);
          border-radius: 8px;
          padding: 9px 30px 9px 10px;
          font-size: 10px;
          cursor: pointer;
        }

        .cb-switch {
          width: 42px;
          height: 24px;
          border: 0;
          border-radius: 20px;
          padding: 3px;
          background: #c7ced8;
          cursor: pointer;
          transition: 0.2s;
          flex-shrink: 0;
        }

        .cb-switch.on {
          background: #172033;
        }

        .cb-switch span {
          display: block;
          width: 18px;
          height: 18px;
          border-radius: 50%;
          background: white;
          transition: 0.2s;
        }

        .cb-switch.on span {
          transform: translateX(18px);
        }

        .cb-security-box {
          padding: 18px;
          border: 1px solid var(--cb-border, #e4e8ef);
          background: var(--cb-soft, #fafbfd);
          border-radius: 11px;
          margin-bottom: 15px;
        }

        .cb-security-box strong {
          font-size: 12px;
        }

        .cb-security-box p {
          color: #7e8999;
          font-size: 10px;
          line-height: 1.6;
          margin: 7px 0 0;
        }

        .cb-danger-button {
          border: 1px solid #e0b5b5;
          color: #a34d4d;
          background: #fff8f8;
          border-radius: 8px;
          padding: 10px 15px;
          font-size: 11px;
          font-weight: 700;
          cursor: pointer;
        }

        .cb-about {
          text-align: center;
          padding: 30px 20px;
        }

        .cb-about-logo {
          width: 70px;
          height: 70px;
          margin: 0 auto 15px;
          border-radius: 17px;
          background: #172033;
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 19px;
          font-weight: 900;
        }

        .cb-about h2 {
          margin: 0;
          font-size: 21px;
        }

        .cb-about > p {
          color: #7e8999;
          font-size: 11px;
          line-height: 1.7;
          max-width: 520px;
          margin: 9px auto 20px;
        }

        .cb-about-meta {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 10px;
          text-align: left;
        }

        .cb-about-meta div {
          padding: 13px;
          border: 1px solid var(--cb-border, #e4e8ef);
          border-radius: 9px;
          background: var(--cb-soft, #fafbfd);
        }

        .cb-about-meta span {
          display: block;
          color: #8a94a4;
          font-size: 9px;
        }

        .cb-about-meta strong {
          display: block;
          margin-top: 5px;
          font-size: 11px;
        }

        @media (max-width: 900px) {
          .cb-settings-layout {
            grid-template-columns: 1fr;
          }

          .cb-settings-nav {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
          }
        }

        @media (max-width: 650px) {
          .cb-settings-page {
            padding: 20px 15px 40px;
          }

          .cb-profile-grid,
          .cb-about-meta {
            grid-template-columns: 1fr;
          }

          .cb-field.full {
            grid-column: auto;
          }

          .cb-settings-nav {
            grid-template-columns: 1fr;
          }

          .cb-profile-hero {
            align-items: flex-start;
            flex-direction: column;
          }

          .cb-preference-row {
            align-items: flex-start;
            flex-direction: column;
          }
        }

        html[data-theme="dark"] {
          --cb-bg: #0d1320;
          --cb-card: #151e2d;
          --cb-soft: #111a28;
          --cb-hover: #1b2638;
          --cb-active: #253249;
          --cb-border: #2b374a;
          --cb-text: #edf2f8;
          --cb-muted: #aeb8c7;
          --cb-icon-bg: #202c3d;
          --cb-input: #111a28;
          --cb-readonly: #1a2433;
        }

        html[data-theme="dark"] .cb-settings-header h1,
        html[data-theme="dark"] .cb-settings-card-header h2,
        html[data-theme="dark"] .cb-profile-hero h3,
        html[data-theme="dark"] .cb-preference-row strong,
        html[data-theme="dark"] .cb-security-box strong,
        html[data-theme="dark"] .cb-about h2,
        html[data-theme="dark"] .cb-about-meta strong {
          color: #edf2f8;
        }

        html[data-theme="dark"] .cb-settings-header p,
        html[data-theme="dark"] .cb-settings-card-header p,
        html[data-theme="dark"] .cb-profile-hero p,
        html[data-theme="dark"] .cb-preference-row p,
        html[data-theme="dark"] .cb-security-box p,
        html[data-theme="dark"] .cb-about > p {
          color: #98a5b8;
        }

        html[data-theme="dark"] .cb-save-button,
        html[data-theme="dark"] .cb-about-logo {
          background: #e9eef5;
          color: #172033;
        }

        html[data-theme="dark"] .cb-small-button,
        html[data-theme="dark"] .cb-select,
        html[data-theme="dark"] .cb-field input {
          color: #edf2f8;
        }
      `}</style>

      <div className="cb-settings-header">
        <p className="cb-settings-eyebrow">
          WORKSPACE SETTINGS
        </p>

        <h1>Settings</h1>

        <p>
          Manage your CurtainBiz account, preferences
          and workspace experience.
        </p>
      </div>

      <div className="cb-settings-layout">
        <aside className="cb-settings-nav">
          {settingsItems.map((item) => (
            <button
              key={item.id}
              className={`cb-settings-nav-item ${
                section === item.id ? "active" : ""
              }`}
              onClick={() => setSection(item.id)}
            >
              <span className="cb-settings-nav-icon">
                {item.icon}
              </span>

              <span className="cb-settings-nav-copy">
                <strong>{item.title}</strong>
                <small>{item.description}</small>
              </span>
            </button>
          ))}
        </aside>

        <main className="cb-settings-card">
          {section === "profile" && (
            <>
              <div className="cb-settings-card-header">
                <h2>Profile</h2>
                <p>
                  Your personal identity and employee
                  information.
                </p>
              </div>

              <div className="cb-profile-hero">
                <div className="cb-profile-avatar">
                  {photo ? (
                    <img
                      src={photo}
                      alt="Profile"
                    />
                  ) : (
                    profileInitials
                  )}
                </div>

                <div>
                  <h3>{resolvedDisplayName}</h3>

                  <p>
                    {roleName} · {email}
                  </p>

                  <div className="cb-profile-actions">
                    <label className="cb-small-button">
                      Change photo
                      <input
                        className="cb-hidden-file"
                        type="file"
                        accept="image/*"
                        onChange={handlePhotoChange}
                      />
                    </label>

                    {photo && (
                      <button
                        className="cb-small-button danger"
                        onClick={removePhoto}
                      >
                        Remove photo
                      </button>
                    )}
                  </div>

                  {photoMessage && (
                    <div className="cb-success">
                      {photoMessage}
                    </div>
                  )}
                </div>
              </div>

              <div className="cb-profile-grid">
                <div className="cb-field">
                  <label>DISPLAY NAME</label>

                  <input
                    value={displayName}
                    onChange={(event) =>
                      setDisplayName(
                        event.target.value
                      )
                    }
                    placeholder="Enter your name"
                  />
                </div>

                <div className="cb-field">
                  <label>EMAIL</label>

                  <input
                    value={email}
                    readOnly
                  />
                </div>

                <div className="cb-field">
                  <label>EMPLOYEE ID</label>

                  <input
                    value={employeeId}
                    onChange={(event) =>
                      setEmployeeId(
                        event.target.value
                      )
                    }
                    placeholder="e.g. EMP001"
                  />
                </div>

                <div className="cb-field">
                  <label>DEPARTMENT</label>

                  <input
                    value={department}
                    onChange={(event) =>
                      setDepartment(
                        event.target.value
                      )
                    }
                    placeholder="e.g. Administration"
                  />
                </div>

                <div className="cb-field">
                  <label>JOB TITLE</label>

                  <input
                    value={jobTitle}
                    onChange={(event) =>
                      setJobTitle(
                        event.target.value
                      )
                    }
                    placeholder="e.g. Administrator"
                  />
                </div>

                <div className="cb-field">
                  <label>PHONE</label>

                  <input
                    value={phone}
                    onChange={(event) =>
                      setPhone(
                        event.target.value
                      )
                    }
                    placeholder="Phone number"
                  />
                </div>

                <div className="cb-field">
                  <label>ROLE</label>

                  <input
                    value={roleName}
                    readOnly
                  />
                </div>

                <div className="cb-field">
                  <label>ACCOUNT ID</label>

                  <input
                    value={userId}
                    readOnly
                  />
                </div>
              </div>

              <div className="cb-profile-footer">
                <div className="cb-success">
                  {profileSaved
                    ? "Profile saved successfully."
                    : profileMessage}
                </div>

                <button
                  className="cb-save-button"
                  onClick={saveExtendedProfile}
                >
                  Save Profile
                </button>
              </div>
            </>
          )}

          {section === "appearance" && (
            <>
              <div className="cb-settings-card-header">
                <h2>Appearance</h2>
                <p>
                  Customize how CurtainBiz looks on
                  your device.
                </p>
              </div>

              <div className="cb-preference-list">
                <div className="cb-preference-row">
                  <div>
                    <strong>Theme</strong>
                    <p>
                      Switch the application between
                      light and dark appearance.
                    </p>
                  </div>

                  <select
                    className="cb-select"
                    value={theme}
                    onChange={(event) =>
                      setTheme(event.target.value)
                    }
                  >
                    <option value="light">
                      Light
                    </option>

                    <option value="dark">
                      Dark
                    </option>
                  </select>
                </div>

                <div className="cb-preference-row">
                  <div>
                    <strong>Compact layout</strong>
                    <p>
                      Store a compact layout preference
                      for future dense workspace views.
                    </p>
                  </div>

                  <button
                    className={`cb-switch ${
                      compactMode ? "on" : ""
                    }`}
                    onClick={() =>
                      setCompactMode(
                        (previous) => !previous
                      )
                    }
                    aria-label="Toggle compact layout"
                  >
                    <span />
                  </button>
                </div>

                <div className="cb-preference-row">
                  <div>
                    <strong>Reset preferences</strong>
                    <p>
                      Restore your appearance and
                      notification preferences.
                    </p>
                  </div>

                  <button
                    className="cb-small-button"
                    onClick={resetPreferences}
                  >
                    Reset
                  </button>
                </div>
              </div>
            </>
          )}

          {section === "notifications" && (
            <>
              <div className="cb-settings-card-header">
                <h2>Notifications</h2>
                <p>
                  Control operational notifications shown
                  inside CurtainBiz.
                </p>
              </div>

              <div className="cb-preference-list">
                <div className="cb-preference-row">
                  <div>
                    <strong>
                      Operational notifications
                    </strong>

                    <p>
                      Allow the application notification
                      center to display operational alerts.
                    </p>
                  </div>

                  <button
                    className={`cb-switch ${
                      notificationsEnabled
                        ? "on"
                        : ""
                    }`}
                    onClick={() =>
                      setNotificationsEnabled(
                        (previous) => !previous
                      )
                    }
                    aria-label="Toggle notifications"
                  >
                    <span />
                  </button>
                </div>

                <div className="cb-preference-row">
                  <div>
                    <strong>
                      Current notification status
                    </strong>

                    <p>
                      {notificationsEnabled
                        ? "Notifications are enabled."
                        : "Notifications are disabled."}
                    </p>
                  </div>

                  <span
                    className="cb-success"
                  >
                    {notificationsEnabled
                      ? "ACTIVE"
                      : "OFF"}
                  </span>
                </div>
              </div>
            </>
          )}

          {section === "security" && (
            <>
              <div className="cb-settings-card-header">
                <h2>Security</h2>
                <p>
                  Review your current account and
                  session controls.
                </p>
              </div>

              <div className="cb-security-box">
                <strong>Authentication</strong>

                <p>
                  CurtainBiz uses authenticated access
                  tokens and role-based permissions for
                  protected application modules.
                </p>
              </div>

              <div className="cb-security-box">
                <strong>Current role</strong>

                <p>
                  {roleName}
                  {currentUser?.role_description
                    ? ` — ${currentUser.role_description}`
                    : ""}
                </p>
              </div>

              <div className="cb-security-box">
                <strong>Account email</strong>

                <p>{email}</p>
              </div>

              <button
                className="cb-danger-button"
                onClick={onSignOut}
              >
                Sign Out
              </button>
            </>
          )}

          {section === "about" && (
            <div className="cb-about">
              <div className="cb-about-logo">
                CB
              </div>

              <h2>CurtainBiz</h2>

              <p>
                Business Operations Platform for
                managing customers, products, inventory,
                orders, production, deliveries, payments,
                analytics and machine-learning-driven
                business intelligence.
              </p>

              <div className="cb-about-meta">
                <div>
                  <span>VERSION</span>
                  <strong>1.0.0</strong>
                </div>

                <div>
                  <span>FRONTEND</span>
                  <strong>React</strong>
                </div>

                <div>
                  <span>BACKEND</span>
                  <strong>FastAPI</strong>
                </div>

                <div>
                  <span>DATABASE</span>
                  <strong>PostgreSQL</strong>
                </div>

                <div>
                  <span>AUTH</span>
                  <strong>JWT + RBAC</strong>
                </div>

                <div>
                  <span>ML</span>
                  <strong>Business Intelligence</strong>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </section>
  );
}

export default SettingsPage;