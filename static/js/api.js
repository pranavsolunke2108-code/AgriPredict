/**
 * AgriPredict Frontend API Client and Multilingual Utilities
 */

const API = {
  getToken() {
    return localStorage.getItem("agri_token");
  },

  setToken(token) {
    localStorage.setItem("agri_token", token);
  },

  getFarmer() {
    try {
      const data = localStorage.getItem("agri_farmer");
      return data ? JSON.parse(data) : null;
    } catch (e) {
      return null;
    }
  },

  setFarmer(farmer) {
    localStorage.setItem("agri_farmer", JSON.stringify(farmer));
  },

  clearSession() {
    localStorage.removeItem("agri_token");
    localStorage.removeItem("agri_farmer");
    document.cookie = "agri_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT;";
  },

  getLang() {
    return localStorage.getItem("agri_lang") || "en";
  },

  setLang(lang) {
    localStorage.setItem("agri_lang", lang);
  },

  async request(endpoint, options = {}) {
    const url = endpoint;
    const headers = options.headers || {};

    if (!headers["Content-Type"] && !(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }

    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    options.headers = headers;

    try {
      const response = await fetch(url, options);

      // Handle 401 Unauthorized
      if (response.status === 401) {
        this.clearSession();
        const isAuthPage = window.location.pathname.includes("/ui/login") || window.location.pathname.includes("/ui/register");
        if (!isAuthPage) {
          const currentPath = window.location.pathname + window.location.search;
          window.location.href = `/ui/login?next=${encodeURIComponent(currentPath)}`;
        }
        throw new Error("Session expired. Please log in again.");
      }

      // Parse JSON or text
      const contentType = response.headers.get("content-type") || "";
      let data = null;
      if (contentType.includes("application/json")) {
        data = await response.json();
      } else {
        data = await response.text();
      }

      if (!response.ok) {
        const errorDetail = (data && data.detail) ? data.detail : (typeof data === "string" ? data : `Request failed with status ${response.status}`);
        const err = new Error(errorDetail);
        err.status = response.status;
        err.data = data;
        throw err;
      }

      return data;
    } catch (err) {
      throw err;
    }
  },

  // Auth Endpoints
  async login(identifier, password) {
    const res = await this.request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ identifier, password }),
    });
    if (res && res.access_token) {
      this.setToken(res.access_token);
      document.cookie = `agri_token=${res.access_token}; path=/; SameSite=Lax`;
    }
    if (res && res.farmer) {
      this.setFarmer(res.farmer);
    }
    return res;
  },

  register(payload) {
    return this.request("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getMe() {
    return this.request("/me");
  },

  async updateFarmerAddress(payload) {
    const res = await this.request("/me/address", {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    if (res) {
      this.setFarmer(res);
    }
    return res;
  },

  getCropsLocalized(lang = null) {
    const l = lang || this.getLang();
    return this.request(`/crops/localized?lang=${encodeURIComponent(l)}`);
  },

  // Dashboard Endpoints
  getDashboardSummary() {
    return this.request("/dashboard/summary");
  },

  getCurrentStatus() {
    return this.request("/dashboard/current");
  },

  getHistory(params = {}) {
    const q = new URLSearchParams();
    if (params.farm_id) q.set("farm_id", params.farm_id);
    if (params.crop) q.set("crop", params.crop);
    if (params.limit) q.set("limit", params.limit);
    if (params.offset) q.set("offset", params.offset);
    return this.request(`/dashboard/history?${q.toString()}`);
  },

  // Farms & Weather & Soil
  getFarms() {
    return this.request("/farms");
  },

  getFarm(farmId) {
    return this.request(`/farms/${farmId}`);
  },

  createFarm(payload) {
    return this.request("/farms", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  updateFarm(farmId, payload) {
    return this.request(`/farms/${farmId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  geoSearch(query) {
    return this.request(`/geo/search?q=${encodeURIComponent(query)}`);
  },

  geoReverse(lat, lon) {
    return this.request(`/geo/reverse?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`);
  },

  refreshWeather(farmId, force = false) {
    return this.request(`/farms/${farmId}/weather/refresh?force=${force}`, {
      method: "POST",
    });
  },

  createSoilTest(farmId, payload) {
    return this.request(`/farms/${farmId}/soil-tests`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getSoilTests(farmId) {
    return this.request(`/farms/${farmId}/soil-tests`);
  },

  recommendCrops(farmId, payload = {}) {
    return this.request(`/farms/${farmId}/recommend`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  // Crop Cycles
  startCycle(farmId, payload) {
    return this.request(`/farms/${farmId}/cycles`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getCycle(cycleId) {
    return this.request(`/cycles/${cycleId}`);
  },

  closeCycle(cycleId, payload) {
    return this.request(`/cycles/${cycleId}/close`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getCycleLog(cycleId) {
    return this.request(`/cycles/${cycleId}/log`);
  },

  // Expenses
  getExpenses(cycleId) {
    return this.request(`/cycles/${cycleId}/expenses`);
  },

  addExpense(cycleId, payload) {
    return this.request(`/cycles/${cycleId}/expenses`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  deleteExpense(expenseId) {
    return this.request(`/expenses/${expenseId}`, {
      method: "DELETE",
    });
  },

  // Agronomic Advisory
  getFertilizerAdvice(farmId, payload) {
    return this.request(`/farms/${farmId}/fertilizer-advice`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getRotationAdvice(farmId) {
    return this.request(`/farms/${farmId}/rotation-advice`);
  },

  // Crop Calendar
  getCycleCalendar(cycleId) {
    return this.request(`/cycles/${cycleId}/calendar`);
  },

  // Alerts & Notifications
  getAlerts(params = {}) {
    const q = new URLSearchParams();
    if (params.unread) q.set("unread", "true");
    if (params.limit) q.set("limit", params.limit);
    if (params.offset) q.set("offset", params.offset);
    return this.request(`/alerts?${q.toString()}`);
  },

  getUnreadAlertsCount() {
    return this.request("/alerts/unread-count");
  },

  markAlertRead(alertId) {
    return this.request(`/alerts/${alertId}/read`, {
      method: "PATCH",
    });
  },

  markAllAlertsRead() {
    return this.request("/alerts/read-all", {
      method: "POST",
    });
  },

  runTaskAlertsAdmin(daysAhead = 2) {
    return this.request(`/admin/run-task-alerts?days_ahead=${daysAhead}`, {
      method: "POST",
    });
  },

  // Phase 5: Profit Estimates & Agronomic Economics
  getFarmProfitEstimates(farmId) {
    return this.request(`/farms/${farmId}/profit-estimates`);
  },

  getCropProfitEstimate(farmId, cropId) {
    return this.request(`/farms/${farmId}/crops/${cropId}/profit`);
  },

  // Phase 5: Market Prices
  getLatestPrices(params = {}) {
    const q = new URLSearchParams();
    if (params.crop_id) q.set("crop_id", params.crop_id);
    if (params.district) q.set("district", params.district);
    return this.request(`/prices?${q.toString()}`);
  },

  getPriceHistory(params = {}) {
    const q = new URLSearchParams();
    if (params.crop_id) q.set("crop_id", params.crop_id);
    if (params.district) q.set("district", params.district);
    if (params.days) q.set("days", params.days);
    return this.request(`/prices/history?${q.toString()}`);
  },

  // Phase 5: Expense Analytics
  getCycleExpenseSummary(cycleId) {
    return this.request(`/cycles/${cycleId}/expense-summary`);
  },

  getFarmerExpensesByCategory() {
    return this.request("/dashboard/expenses-by-category");
  },

  // Phase 5: Admin Management
  getAdminCrops() {
    return this.request("/admin/crops");
  },

  getAdminCrop(cropId) {
    return this.request(`/admin/crops/${cropId}`);
  },

  createAdminCrop(payload) {
    return this.request("/admin/crops", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  updateAdminCrop(cropId, payload) {
    return this.request(`/admin/crops/${cropId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  deleteAdminCrop(cropId) {
    return this.request(`/admin/crops/${cropId}`, {
      method: "DELETE",
    });
  },

  getAdminCropStages(cropId = null) {
    const url = cropId ? `/admin/crop-stages?crop_id=${cropId}` : "/admin/crop-stages";
    return this.request(url);
  },

  createAdminCropStage(payload) {
    return this.request("/admin/crop-stages", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  updateAdminCropStage(stageId, payload) {
    return this.request(`/admin/crop-stages/${stageId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  deleteAdminCropStage(stageId) {
    return this.request(`/admin/crop-stages/${stageId}`, {
      method: "DELETE",
    });
  },

  getAdminFertilizers() {
    return this.request("/admin/fertilizers");
  },

  createAdminFertilizer(payload) {
    return this.request("/admin/fertilizers", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  updateAdminFertilizer(fertId, payload) {
    return this.request(`/admin/fertilizers/${fertId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  deleteAdminFertilizer(fertId) {
    return this.request(`/admin/fertilizers/${fertId}`, {
      method: "DELETE",
    });
  },

  getAdminRotationRules() {
    return this.request("/admin/rotation-rules");
  },

  createAdminRotationRule(payload) {
    return this.request("/admin/rotation-rules", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  updateAdminRotationRule(ruleId, payload) {
    return this.request(`/admin/rotation-rules/${ruleId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  deleteAdminRotationRule(ruleId) {
    return this.request(`/admin/rotation-rules/${ruleId}`, {
      method: "DELETE",
    });
  },

  getAdminMarketPrices(params = {}) {
    const q = new URLSearchParams();
    if (params.crop_id) q.set("crop_id", params.crop_id);
    if (params.district) q.set("district", params.district);
    if (params.limit) q.set("limit", params.limit);
    if (params.offset) q.set("offset", params.offset);
    return this.request(`/admin/market-prices?${q.toString()}`);
  },

  upsertAdminMarketPrice(payload) {
    return this.request("/admin/market-prices", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  deleteAdminMarketPrice(priceId) {
    return this.request(`/admin/market-prices/${priceId}`, {
      method: "DELETE",
    });
  },

  uploadMarketPricesCsv(formData) {
    return this.request("/admin/market-prices/upload-csv", {
      method: "POST",
      body: formData,
    });
  },

  getAdminTranslations(params = {}) {
    const q = new URLSearchParams();
    if (params.lang) q.set("lang", params.lang);
    if (params.key) q.set("key", params.key);
    return this.request(`/admin/translations?${q.toString()}`);
  },

  upsertAdminTranslation(payload) {
    return this.request("/admin/translations", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  deleteAdminTranslation(textKey, lang) {
    return this.request(`/admin/translations/${encodeURIComponent(textKey)}/${lang}`, {
      method: "DELETE",
    });
  },

  getAdminUsers() {
    return this.request("/admin/users");
  },

  toggleUserActive(userId, isActive) {
    return this.request(`/admin/users/${userId}/active`, {
      method: "PATCH",
      body: JSON.stringify({ is_active: isActive }),
    });
  },

  getAdminAuditLog(params = {}) {
    const q = new URLSearchParams();
    if (params.table) q.set("table", params.table);
    if (params.record_id) q.set("record_id", params.record_id);
    if (params.limit) q.set("limit", params.limit);
    return this.request(`/admin/audit-log?${q.toString()}`);
  },

  // Translations
  getTranslations(lang) {
    return this.request(`/i18n/${lang}`);
  },

  updateLanguage(lang) {
    return this.request("/me/language", {
      method: "PATCH",
      body: JSON.stringify({ language: lang }),
    });
  },
};

// UI Notification and Helper System
const UI = {
  showAlert(containerId, message, type = "danger") {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = `
      <div class="alert alert-${type}">
        <span>${type === 'danger' ? '⚠️' : '✓'}</span>
        <span>${message}</span>
      </div>
    `;
    container.scrollIntoView({ behavior: "smooth", block: "nearest" });
  },

  clearAlert(containerId) {
    const container = document.getElementById(containerId);
    if (container) container.innerHTML = "";
  },

  openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add("active");
  },

  closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove("active");
  },

  formatCurrency(val) {
    const num = Number(val) || 0;
    return "₹" + num.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  },

  formatDate(dateStr) {
    if (!dateStr) return "—";
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
    } catch (e) {
      return dateStr;
    }
  },

  getAlertMeta(type) {
    const d = this._dict || {};
    switch (type) {
      case "Rain":
        return { icon: "🌧️", label: d["alert_rain"] || "Heavy Rain", badgeClass: "badge-rain" };
      case "Heat":
        return { icon: "☀️", label: d["alert_heat"] || "Extreme Heat", badgeClass: "badge-heat" };
      case "Frost":
        return { icon: "❄️", label: d["alert_frost"] || "Frost Warning", badgeClass: "badge-frost" };
      case "Drought":
        return { icon: "🏜️", label: d["alert_drought"] || "Drought Risk", badgeClass: "badge-drought" };
      case "Task":
        return { icon: "📋", label: d["alert_task"] || "Stage Task", badgeClass: "badge-task" };
      case "Price":
        return { icon: "💰", label: d["alert_price"] || "Market Price", badgeClass: "badge-price" };
      default:
        return { icon: "⚠️", label: this.translateAlertType(type), badgeClass: "badge-task" };
    }
  },

  async updateAlertBadge() {
    try {
      const badges = [
        document.getElementById("nav-unread-badge"),
        document.getElementById("mobile-nav-unread-badge"),
      ].filter(Boolean);
      if (!badges.length) return;
      const data = await API.getUnreadAlertsCount();
      const count = data.unread_count || 0;
      badges.forEach((b) => {
        if (count > 0) {
          b.textContent = count > 99 ? "99+" : count;
          b.style.display = "inline-block";
        } else {
          b.style.display = "none";
        }
      });
    } catch (e) {
      // Ignore if unauthenticated or offline
    }
  },

  // Design System Theme Support (Light / Dark)
  initTheme() {
    try {
      const saved = localStorage.getItem("agripredict_theme");
      const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
      const theme = saved || (prefersDark ? "dark" : "light");
      this.setTheme(theme, false);
    } catch (e) {
      document.documentElement.setAttribute("data-theme", "light");
    }
  },

  setTheme(theme, persist = true) {
    if (persist) {
      try {
        localStorage.setItem("agripredict_theme", theme);
      } catch (e) {}
    }
    document.documentElement.setAttribute("data-theme", theme);
    if (theme === "dark") {
      document.body.classList.add("theme-dark");
    } else {
      document.body.classList.remove("theme-dark");
    }
    const themeBtns = document.querySelectorAll("#theme-toggle-btn, .theme-toggle-btn");
    themeBtns.forEach(btn => {
      btn.innerHTML = theme === "dark" ? "☀️" : "🌙";
      btn.title = theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode";
      btn.setAttribute("aria-label", btn.title);
    });
    const mobileThemeLabels = document.querySelectorAll(".mobile-theme-label");
    mobileThemeLabels.forEach(lbl => {
      lbl.textContent = theme === "dark" ? "Light Mode" : "Dark Mode";
    });
    const mobileThemeIcons = document.querySelectorAll(".mobile-theme-icon");
    mobileThemeIcons.forEach(ico => {
      ico.textContent = theme === "dark" ? "☀️" : "🌙";
    });
    window.dispatchEvent(new CustomEvent("agri_theme_changed", { detail: { theme } }));
  },

  toggleTheme() {
    const current = document.documentElement.getAttribute("data-theme") || "light";
    const next = current === "dark" ? "light" : "dark";
    this.setTheme(next, true);
  },

  getCurrentSeason() {
    const month = new Date().getMonth(); // 0=Jan, 9=Oct
    if (month >= 5 && month <= 8) {
      return { key: "season_kharif", label: "Kharif Season", css: "var(--season-kharif)" };
    } else if (month >= 9 || month <= 1) {
      return { key: "season_rabi", label: "Rabi Season", css: "var(--season-rabi)" };
    } else {
      return { key: "season_zaid", label: "Zaid Season", css: "var(--season-zaid)" };
    }
  },

  // Circular SVG Progress Ring
  renderCircularProgress(percent, size = 64, stroke = 6, label = "") {
    const p = Math.max(0, Math.min(100, Number(percent) || 0));
    const radius = (size - stroke) / 2;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (p / 100) * circumference;
    const strokeColor = p >= 70 ? "var(--primary)" : p >= 40 ? "var(--accent-gold)" : "var(--warning-terracotta)";
    return `
      <div class="progress-ring-wrap" style="width:${size}px; height:${size}px;" title="${p}%">
        <svg class="progress-ring-svg" width="${size}" height="${size}">
          <circle class="progress-ring-bg" stroke-width="${stroke}" r="${radius}" cx="${size/2}" cy="${size/2}" />
          <circle class="progress-ring-bar" stroke="${strokeColor}" stroke-width="${stroke}" stroke-dasharray="${circumference}" stroke-dashoffset="${offset}" r="${radius}" cx="${size/2}" cy="${size/2}" />
        </svg>
        <span class="progress-ring-val">${label || Math.round(p) + '%'}</span>
      </div>
    `;
  },

  // Count-up animation for KPI cards
  animateCountUp(elementId, target, duration = 800, prefix = "", suffix = "") {
    const el = typeof elementId === "string" ? document.getElementById(elementId) : elementId;
    if (!el) return;
    const finalVal = Number(target) || 0;
    const isCurrency = prefix === "₹";
    const startVal = 0;
    const startTime = performance.now();

    function update(now) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 3);
      const current = startVal + (finalVal - startVal) * ease;
      if (isCurrency) {
        el.textContent = "₹" + current.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      } else if (String(target).includes(".")) {
        el.textContent = `${prefix}${current.toFixed(1)}${suffix}`;
      } else {
        el.textContent = `${prefix}${Math.round(current).toLocaleString("en-IN")}${suffix}`;
      }
      if (progress < 1) {
        requestAnimationFrame(update);
      }
    }
    requestAnimationFrame(update);
  },

  // Skeletons & Empty States
  getCardSkeleton(count = 3) {
    let html = "";
    for (let i = 0; i < count; i++) {
      html += `
        <div class="card skeleton-card" style="padding:1.5rem; display:flex; flex-direction:column; gap:0.75rem;">
          <div class="skeleton" style="height:24px; width:55%;"></div>
          <div class="skeleton" style="height:16px; width:80%;"></div>
          <div class="skeleton" style="height:16px; width:40%;"></div>
          <div style="display:flex; gap:0.5rem; margin-top:0.5rem;">
            <div class="skeleton" style="height:32px; width:80px; border-radius:999px;"></div>
            <div class="skeleton" style="height:32px; width:80px; border-radius:999px;"></div>
          </div>
        </div>
      `;
    }
    return html;
  },

  getTableSkeleton(rows = 5, cols = 4) {
    let rowsHtml = "";
    for (let r = 0; r < rows; r++) {
      rowsHtml += `<tr>` + Array.from({ length: cols }).map(() => `
        <td><div class="skeleton" style="height:16px; width:${60 + (r * 7) % 35}%;"></div></td>
      `).join("") + `</tr>`;
    }
    return `
      <div class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>${Array.from({ length: cols }).map(() => `<th><div class="skeleton" style="height:16px; width:70px;"></div></th>`).join("")}</tr>
          </thead>
          <tbody>${rowsHtml}</tbody>
        </table>
      </div>
    `;
  },

  getEmptyState(icon = "🌱", title = "No records found", text = "", actionHtml = "") {
    return `
      <div class="empty-state">
        <div style="font-size:2.5rem; margin-bottom:0.25rem;">${icon}</div>
        <h3 class="empty-state-title">${title}</h3>
        ${text ? `<p class="empty-state-text">${text}</p>` : ""}
        ${actionHtml ? `<div style="margin-top:0.75rem;">${actionHtml}</div>` : ""}
      </div>
    `;
  },

  confirm(title, message, confirmText = "Confirm", cancelText = "Cancel") {
    return new Promise((resolve) => {
      let modal = document.getElementById("global-confirm-modal");
      if (!modal) {
        modal = document.createElement("div");
        modal.id = "global-confirm-modal";
        modal.className = "modal-backdrop";
        modal.style.display = "none";
        modal.innerHTML = `
          <div class="modal-box" style="max-width:440px;">
            <div class="modal-header">
              <h3 class="card-title" id="confirm-modal-title">Confirm Action</h3>
              <button type="button" class="btn btn-ghost btn-icon" id="confirm-modal-close" aria-label="Close">&times;</button>
            </div>
            <div class="modal-body">
              <p id="confirm-modal-message" style="color:var(--ink-secondary); font-size:var(--text-base);"></p>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" id="confirm-modal-cancel">Cancel</button>
              <button type="button" class="btn btn-danger" id="confirm-modal-ok">Confirm</button>
            </div>
          </div>
        `;
        document.body.appendChild(modal);
      }

      const titleEl = document.getElementById("confirm-modal-title");
      const msgEl = document.getElementById("confirm-modal-message");
      const okBtn = document.getElementById("confirm-modal-ok");
      const cancelBtn = document.getElementById("confirm-modal-cancel");
      const closeBtn = document.getElementById("confirm-modal-close");

      titleEl.textContent = title;
      msgEl.textContent = message;
      okBtn.textContent = confirmText;
      cancelBtn.textContent = cancelText;

      const cleanup = () => {
        modal.style.display = "none";
        okBtn.onclick = null;
        cancelBtn.onclick = null;
        closeBtn.onclick = null;
      };

      okBtn.onclick = () => { cleanup(); resolve(true); };
      cancelBtn.onclick = () => { cleanup(); resolve(false); };
      closeBtn.onclick = () => { cleanup(); resolve(false); };
      modal.style.display = "flex";
    });
  },

  _dict: {},

  t(key, fallback = "") {
    return (this._dict && this._dict[key]) || fallback || key;
  },

  translateCrop(cropName) {
    if (!cropName) return "—";
    const key = "crop_" + cropName.toLowerCase().replace(/ /g, "_");
    return (this._dict && this._dict[key]) || cropName;
  },

  translateCategory(category) {
    if (!category) return "—";
    const key = "cat_" + category.toLowerCase();
    return (this._dict && this._dict[key]) || category;
  },

  translateSeason(season) {
    if (!season) return "—";
    const key = "season_" + season.toLowerCase();
    return (this._dict && this._dict[key]) || season;
  },

  translateAlertType(alertType) {
    if (!alertType) return "—";
    const key = "alert_" + alertType.toLowerCase();
    return (this._dict && this._dict[key]) || alertType;
  },

  translateStatus(status) {
    if (!status) return "—";
    const key = status.toLowerCase();
    return (this._dict && this._dict[key]) || status;
  },

  // Multilingual Translator
  async applyTranslations(lang = null) {
    const activeLang = lang || API.getLang();
    API.setLang(activeLang);

    // Update active state of language buttons
    document.querySelectorAll(".lang-btn").forEach((btn) => {
      if (btn.dataset.lang === activeLang) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });

    try {
      const dict = await API.getTranslations(activeLang);
      this._dict = dict || {};

      document.querySelectorAll("[data-i18n]").forEach((el) => {
        const key = el.getAttribute("data-i18n");
        if (dict[key]) {
          if (el.tagName === "INPUT" && (el.type === "button" || el.type === "submit")) {
            el.value = dict[key];
          } else {
            el.textContent = dict[key];
          }
        }
      });

      document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
        const key = el.getAttribute("data-i18n-placeholder");
        if (dict[key]) {
          el.placeholder = dict[key];
        }
      });

      document.querySelectorAll("[data-i18n-title]").forEach((el) => {
        const key = el.getAttribute("data-i18n-title");
        if (dict[key]) {
          el.title = dict[key];
        }
      });

      if (typeof Chart !== "undefined" && Chart.defaults && Chart.defaults.font) {
        Chart.defaults.font.family = "'Noto Sans Devanagari', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif";
      }

      window.dispatchEvent(new CustomEvent("agri_lang_changed", { detail: { lang: activeLang, dict } }));
    } catch (err) {
      console.warn("Could not load translations:", err);
    }
  },

  renderNavbar(activePage = "dashboard") {
    const farmer = API.getFarmer();
    const navPlaceholder = document.getElementById("navbar-placeholder");
    if (!navPlaceholder) return;

    if (typeof document !== "undefined" && document.body) {
      document.body.classList.add("has-app-sidebar");
    }

    const season = this.getCurrentSeason();
    const curTheme = (typeof document !== "undefined" && document.documentElement.getAttribute("data-theme")) || "light";

    navPlaceholder.innerHTML = `
      <!-- Desktop Sidebar -->
      <aside class="app-sidebar" aria-label="Main Navigation">
        <div class="sidebar-brand">
          <span style="font-size:1.5rem;">🌱</span>
          <span>AgriPredict</span>
        </div>
        <nav class="sidebar-nav">
          <a href="/ui/dashboard" class="sidebar-link ${activePage === 'dashboard' ? 'active' : ''}">
            <span style="font-size:1.2rem;">📊</span>
            <span data-i18n="dashboard">${this.t('dashboard', 'Dashboard')}</span>
          </a>
          <a href="/ui/farms" class="sidebar-link ${activePage === 'farms' ? 'active' : ''}">
            <span style="font-size:1.2rem;">🚜</span>
            <span data-i18n="my_farms">${this.t('my_farms', 'My Farms')}</span>
          </a>
          <a href="/ui/prices" class="sidebar-link ${activePage === 'prices' ? 'active' : ''}">
            <span style="font-size:1.2rem;">📈</span>
            <span data-i18n="market_prices">${this.t('market_prices', 'Market Prices')}</span>
          </a>
          <a href="/ui/alerts" class="sidebar-link ${activePage === 'alerts' ? 'active' : ''}">
            <span style="font-size:1.2rem;">🔔</span>
            <span data-i18n="alerts">${this.t('alerts', 'Alerts')}</span>
          </a>
          ${farmer && farmer.role === 'admin' ? `
            <a href="/ui/admin" class="sidebar-link ${activePage === 'admin' ? 'active' : ''}" style="color:var(--info-water); font-weight:700;">
              <span style="font-size:1.2rem;">⚙️</span>
              <span data-i18n="admin_panel">Admin</span>
            </a>
          ` : ''}
        </nav>
      </aside>

      <!-- Sticky Top Header -->
      <header class="app-header">
        <div class="header-left">
          <a href="/ui/dashboard" class="nav-brand" style="display:inline-flex; align-items:center; gap:0.5rem; text-decoration:none; font-weight:700; color:var(--primary); font-size:1.15rem;">
            <span>🌱</span> <span class="hide-on-desktop">AgriPredict</span>
          </a>
          <span class="chip chip-season" id="current-season-chip" style="margin-left:0.5rem;">
            🌱 <span data-i18n="${season.key}">${this.t(season.key, season.label)}</span>
          </span>
        </div>
        <div class="header-right">
          <div class="lang-switch">
            <button type="button" class="lang-btn ${API.getLang() === 'en' ? 'active' : ''}" data-lang="en" onclick="UI.switchLanguage('en')">EN</button>
            <button type="button" class="lang-btn ${API.getLang() === 'mr' ? 'active' : ''}" data-lang="mr" onclick="UI.switchLanguage('mr')">MR</button>
            <button type="button" class="lang-btn ${API.getLang() === 'hi' ? 'active' : ''}" data-lang="hi" onclick="UI.switchLanguage('hi')">HI</button>
          </div>
          <button type="button" id="theme-toggle-btn" class="btn btn-ghost btn-icon" onclick="UI.toggleTheme()" title="${curTheme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}" aria-label="Toggle Theme">
            ${curTheme === 'dark' ? '☀️' : '🌙'}
          </button>
          <a href="/ui/alerts" class="btn btn-ghost btn-icon nav-bell-link" title="Notifications & Weather Alerts" style="position:relative;">
            🔔<span id="nav-unread-badge" class="badge-unread" style="display:none; position:absolute; top:-2px; right:-2px;">0</span>
          </a>
          ${farmer ? `<span class="farmer-name-tag hide-on-phone" style="font-size:0.875rem; font-weight:600; color:var(--ink);">${farmer.name}</span>` : ''}
          <button class="btn btn-secondary btn-sm" onclick="UI.logout()" data-i18n="logout">${this.t('logout', 'Logout')}</button>
        </div>
      </header>

      <!-- Mobile Bottom Navigation Bar (< 1024px) -->
      <nav class="app-bottom-nav" aria-label="Mobile Navigation">
        <a href="/ui/dashboard" class="bottom-nav-item ${activePage === 'dashboard' ? 'active' : ''}">
          <span style="font-size:1.25rem;">📊</span>
          <span data-i18n="dashboard">${this.t('dashboard', 'Dashboard')}</span>
        </a>
        <a href="/ui/farms" class="bottom-nav-item ${activePage === 'farms' ? 'active' : ''}">
          <span style="font-size:1.25rem;">🚜</span>
          <span data-i18n="my_farms">${this.t('my_farms', 'My Farms')}</span>
        </a>
        <a href="/ui/prices" class="bottom-nav-item ${activePage === 'prices' ? 'active' : ''}">
          <span style="font-size:1.25rem;">📈</span>
          <span data-i18n="market_prices">${this.t('market_prices', 'Prices')}</span>
        </a>
        <a href="/ui/alerts" class="bottom-nav-item ${activePage === 'alerts' ? 'active' : ''}">
          <span style="font-size:1.25rem; position:relative;">
            🔔<span id="mobile-nav-unread-badge" class="badge-unread" style="display:none; position:absolute; top:-4px; right:-8px;">0</span>
          </span>
          <span data-i18n="alerts">${this.t('alerts', 'Alerts')}</span>
        </a>
      </nav>
    `;
    this.applyTranslations();
    this.updateAlertBadge();
  },

  async switchLanguage(lang) {
    API.setLang(lang);
    if (API.getToken()) {
      try {
        await API.updateLanguage(lang);
        const farmer = API.getFarmer();
        if (farmer) {
          farmer.language = lang;
          API.setFarmer(farmer);
        }
      } catch (e) {
        console.warn("Could not persist language to backend:", e);
      }
    }
    await this.applyTranslations(lang);
  },

  logout() {
    API.clearSession();
    window.location.href = "/ui/login";
  },

  isSafeUrl(url) {
    if (!url || typeof url !== "string") return false;
    // Must start with single slash, not protocol-relative //, no protocol scheme, no backslashes
    if (!url.startsWith("/") || url.startsWith("//")) return false;
    if (url.includes("://") || url.includes("\\")) return false;
    return true;
  },

  getSafeRedirectUrl(defaultUrl = "/ui/dashboard") {
    const params = new URLSearchParams(window.location.search);
    const next = params.get("next");
    if (next && this.isSafeUrl(next)) {
      return next;
    }
    return defaultUrl;
  },

  showToast(message, type = "info", duration = 4000) {
    let container = document.getElementById("toast-container");
    if (!container) {
      container = document.createElement("div");
      container.id = "toast-container";
      container.setAttribute("role", "status");
      container.setAttribute("aria-live", "polite");
      document.body.appendChild(container);
    }
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.setAttribute("role", "status");
    toast.setAttribute("aria-live", "polite");
    const icons = {
      success: "✓",
      danger: "⚠️",
      warning: "⚠️",
      info: "ℹ️",
    };
    toast.innerHTML = `
      <span class="toast-icon">${icons[type] || "ℹ️"}</span>
      <span class="toast-message">${message}</span>
      <button type="button" class="toast-close" aria-label="Close">&times;</button>
    `;
    const removeToast = () => {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(30px)";
      setTimeout(() => toast.remove(), 200);
    };
    const closeBtn = toast.querySelector(".toast-close");
    if (closeBtn) closeBtn.onclick = removeToast;
    container.appendChild(toast);
    setTimeout(removeToast, duration);
  },

  showError(err, fallbackMessage = "An error occurred") {
    const msg = (err && (err.message || err.detail)) || fallbackMessage;
    console.error("AgriPredict API Error:", err);
    this.showToast(msg, "danger");
    return msg;
  },

  async requireAuth() {
    const token = API.getToken();
    const currentPath = window.location.pathname + window.location.search;

    if (!token) {
      document.body.classList.add("auth-protected");
      document.body.style.visibility = "hidden";
      window.location.replace(`/ui/login?next=${encodeURIComponent(currentPath)}`);
      return false;
    }

    try {
      const farmer = await API.getMe();
      API.setFarmer(farmer);
      if (farmer && farmer.language) {
        API.setLang(farmer.language);
      }
      document.cookie = `agri_token=${token}; path=/; SameSite=Lax`;
      document.body.classList.remove("auth-protected");
      document.body.classList.add("auth-ready");
      document.body.style.visibility = "visible";
      document.body.style.opacity = "1";
      return true;
    } catch (err) {
      API.clearSession();
      document.body.classList.add("auth-protected");
      document.body.style.visibility = "hidden";
      window.location.replace(`/ui/login?next=${encodeURIComponent(currentPath)}`);
      return false;
    }
  },

  // Modal: Start New Crop Cycle
  async openStartCycleModal(options = {}) {
    const {
      preselectedFarmId = null,
      preselectedCropId = null,
      predictionId = null,
      onSuccess = null,
    } = options;

    let modal = document.getElementById("global-start-cycle-modal");
    if (!modal) {
      modal = document.createElement("div");
      modal.id = "global-start-cycle-modal";
      modal.className = "modal-overlay";
      modal.innerHTML = `
        <div class="modal-content" style="max-width: 520px;">
          <div class="modal-header">
            <h3 class="modal-title">🌱 Start New Crop Cycle</h3>
            <button type="button" class="modal-close" onclick="UI.closeModal('global-start-cycle-modal')">&times;</button>
          </div>
          <form id="global-start-cycle-form">
            <input type="hidden" id="g-cycle-prediction-id" value="">
            <div class="modal-body">
              <div id="global-start-cycle-alert"></div>

              <div id="global-start-cycle-no-farms" style="display:none; text-align:center; padding:1.5rem;">
                <p style="color:var(--text-muted); margin-bottom:1rem; font-size:0.95rem;">
                  You do not have any registered farms yet. Add a farm to start crop cycles.
                </p>
                <a href="/ui/farms" class="btn btn-primary btn-sm">+ Add Farm</a>
              </div>

              <div id="global-start-cycle-fields">
                <div class="form-group">
                  <label class="form-label" for="g-cycle-farm-select">Farm *</label>
                  <select id="g-cycle-farm-select" class="form-control" required></select>
                </div>

                <div class="form-group">
                  <label class="form-label" for="g-cycle-crop-select">Crop *</label>
                  <select id="g-cycle-crop-select" class="form-control" required></select>
                </div>

                <div class="form-group">
                  <label class="form-label" for="g-cycle-sowing-date">Sowing Date *</label>
                  <input type="date" id="g-cycle-sowing-date" class="form-control" required>
                  <small style="color:var(--text-muted); font-size:0.75rem;">
                    Selecting today or earlier marks status as "Growing". Future dates set status as "Planned".
                  </small>
                </div>

                <div class="form-group" style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:var(--radius-sm); padding:0.85rem 1rem;">
                  <div style="font-size:0.82rem; color:var(--text-muted);">Computed Expected Harvest Date:</div>
                  <div id="g-cycle-expected-harvest" style="font-size:1.15rem; font-weight:700; color:var(--primary-dark); margin-top:0.25rem;">—</div>
                  <div id="g-cycle-duration-note" style="font-size:0.75rem; color:var(--text-muted); margin-top:0.2rem;"></div>
                </div>
              </div>
            </div>
            <div class="modal-footer" id="global-start-cycle-footer">
              <button type="button" class="btn btn-secondary" onclick="UI.closeModal('global-start-cycle-modal')">Cancel</button>
              <button type="submit" id="g-cycle-submit-btn" class="btn btn-primary">Start Crop Cycle</button>
            </div>
          </form>
        </div>
      `;
      document.body.appendChild(modal);

      // Form submission handler
      const form = document.getElementById("global-start-cycle-form");
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        UI.clearAlert("global-start-cycle-alert");
        const farmId = document.getElementById("g-cycle-farm-select").value;
        const cropId = parseInt(document.getElementById("g-cycle-crop-select").value);
        const sowDate = document.getElementById("g-cycle-sowing-date").value;
        const predId = document.getElementById("g-cycle-prediction-id").value;
        const submitBtn = document.getElementById("g-cycle-submit-btn");

        submitBtn.disabled = true;
        submitBtn.textContent = "Starting cycle...";

        try {
          const res = await API.startCycle(farmId, {
            crop_id: cropId,
            sowing_date: sowDate,
            prediction_id: predId ? parseInt(predId) : null,
          });
          UI.closeModal("global-start-cycle-modal");
          UI.showToast("Crop cycle started successfully!", "success");
          window.dispatchEvent(new CustomEvent("agri_cycle_started", { detail: res }));
          if (typeof UI._startCycleSuccessCallback === "function") {
            UI._startCycleSuccessCallback(res);
          }
        } catch (err) {
          // Display 400 error message plainly (e.g. farm already has an active cycle)
          UI.showAlert("global-start-cycle-alert", err.message || "Failed to start crop cycle", "danger");
        } finally {
          submitBtn.disabled = false;
          submitBtn.textContent = "Start Crop Cycle";
        }
      });
    }

    UI._startCycleSuccessCallback = onSuccess;
    UI.clearAlert("global-start-cycle-alert");
    document.getElementById("g-cycle-prediction-id").value = predictionId || "";

    const farmSelect = document.getElementById("g-cycle-farm-select");
    const cropSelect = document.getElementById("g-cycle-crop-select");
    const sowingInput = document.getElementById("g-cycle-sowing-date");
    const fieldsDiv = document.getElementById("global-start-cycle-fields");
    const noFarmsDiv = document.getElementById("global-start-cycle-no-farms");
    const footerDiv = document.getElementById("global-start-cycle-footer");

    // Sowing date default today
    const todayStr = new Date().toISOString().split("T")[0];
    sowingInput.value = todayStr;

    let localizedCrops = [];

    const recalculateHarvest = () => {
      const selectedCropId = parseInt(cropSelect.value);
      const matched = localizedCrops.find((c) => c.crop_id === selectedCropId);
      const duration = (matched && matched.duration_days) ? matched.duration_days : 120;
      const sowVal = sowingInput.value;

      if (sowVal) {
        const d = new Date(sowVal);
        d.setDate(d.getDate() + duration);
        document.getElementById("g-cycle-expected-harvest").textContent = UI.formatDate(d);
        document.getElementById("g-cycle-duration-note").textContent = `Calculated as sowing date + ${duration} days crop duration.`;
      } else {
        document.getElementById("g-cycle-expected-harvest").textContent = "—";
        document.getElementById("g-cycle-duration-note").textContent = "";
      }
    };

    cropSelect.onchange = recalculateHarvest;
    sowingInput.oninput = recalculateHarvest;
    sowingInput.onchange = recalculateHarvest;

    try {
      const [farms, crops] = await Promise.all([
        API.getFarms(),
        API.getCropsLocalized(),
      ]);

      localizedCrops = crops || [];

      if (!farms || farms.length === 0) {
        noFarmsDiv.style.display = "block";
        fieldsDiv.style.display = "none";
        footerDiv.style.display = "none";
      } else {
        noFarmsDiv.style.display = "none";
        fieldsDiv.style.display = "block";
        footerDiv.style.display = "flex";

        farmSelect.innerHTML = farms.map((f) => `
          <option value="${f.farm_id}" ${preselectedFarmId && f.farm_id == preselectedFarmId ? "selected" : ""}>
            ${f.farm_name} (${f.area_acres} acres)
          </option>
        `).join("");

        cropSelect.innerHTML = localizedCrops.map((c) => `
          <option value="${c.crop_id}" ${preselectedCropId && c.crop_id == preselectedCropId ? "selected" : ""}>
            ${c.localized_name || c.crop_name} (${c.duration_days} days)
          </option>
        `).join("");

        recalculateHarvest();
      }

      UI.openModal("global-start-cycle-modal");
    } catch (err) {
      UI.showError(err, "Could not initialize Start Cycle modal");
    }
  },

  // Modal: Fertilizer Plan & Nutrient Dosage
  async openFertilizerPlanModal(options = {}) {
    const {
      farmId,
      farmName = "",
      cropId = null,
      cropName = "",
    } = options;

    if (!farmId) {
      UI.showToast("No farm selected for fertilizer plan.", "warning");
      return;
    }

    let modal = document.getElementById("global-fertilizer-modal");
    if (!modal) {
      modal = document.createElement("div");
      modal.id = "global-fertilizer-modal";
      modal.className = "modal-overlay";
      modal.innerHTML = `
        <div class="modal-content" style="max-width: 650px;">
          <div class="modal-header">
            <div>
              <h3 class="modal-title">🧪 Fertilizer Plan & Nutrient Dosage</h3>
              <p id="g-fert-subtitle" style="font-size:0.82rem; color:var(--text-muted);"></p>
            </div>
            <button type="button" class="modal-close" onclick="UI.closeModal('global-fertilizer-modal')">&times;</button>
          </div>
          <div class="modal-body">
            <div id="g-fert-alert"></div>

            <div id="g-fert-crop-picker-wrapper" style="margin-bottom:1.25rem; display:none;">
              <label class="form-label" for="g-fert-crop-select">Choose Crop to Plan For:</label>
              <select id="g-fert-crop-select" class="form-control"></select>
            </div>

            <div id="g-fert-content">
              <div class="empty-state">
                <p>Calculating nutrient dosages...</p>
              </div>
            </div>

            <div class="disclaimer-box" style="margin-top:1.25rem; font-size:0.8rem; color:#64748b; background:#f8fafc; padding:0.65rem 0.9rem; border-radius:var(--radius-sm); border:1px solid #e2e8f0;">
              ℹ️ <strong>Note:</strong> Fertilizer dosage amounts are indicative calculations based on soil test nutrient deficits. Verify against recommendations from your local Agriculture Department or Krishi Vigyan Kendra (KVK).
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" onclick="UI.closeModal('global-fertilizer-modal')">Close</button>
          </div>
        </div>
      `;
      document.body.appendChild(modal);
    }

    UI.clearAlert("g-fert-alert");
    document.getElementById("g-fert-subtitle").textContent = farmName ? `Farm: ${farmName}` : "";

    const contentDiv = document.getElementById("g-fert-content");
    const pickerWrapper = document.getElementById("g-fert-crop-picker-wrapper");
    const cropSelect = document.getElementById("g-fert-crop-select");

    const fetchAndRenderAdvice = async (targetCropId, targetCropName = "") => {
      contentDiv.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">⏳</div>
          <p>Calculating nutrient dosages based on soil test...</p>
        </div>
      `;

      try {
        const res = await API.getFertilizerAdvice(farmId, { crop_id: parseInt(targetCropId) });

        if (res.fertilizers && res.fertilizers.length > 0) {
          contentDiv.innerHTML = `
            <div style="margin-bottom:0.75rem; font-size:0.88rem; font-weight:600; color:#065f46; background:#ecfdf5; padding:0.5rem 0.75rem; border-radius:var(--radius-sm); border-left:3px solid #10b981;">
              ✓ ${res.message || "Nutrient plan generated from soil test"}
            </div>
            <table class="data-table" style="margin-top:0.5rem;">
              <thead>
                <tr>
                  <th>Fertilizer</th>
                  <th>Dosage / Acre</th>
                  <th>Farm Requirement</th>
                  <th>Est. Cost</th>
                </tr>
              </thead>
              <tbody>
                ${res.fertilizers.map((f) => `
                  <tr>
                    <td><strong>${f.fertilizer}</strong></td>
                    <td>${f.kg_per_acre} kg</td>
                    <td style="font-weight:600; color:var(--primary-dark);">${f.kg_for_farm} kg</td>
                    <td style="font-weight:700; color:var(--accent);">${UI.formatCurrency(f.estimated_cost)}</td>
                  </tr>
                `).join("")}
              </tbody>
            </table>
            <div style="margin-top:0.75rem; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem;">
              <span style="font-weight:700; color:var(--ink); font-size:0.85rem;">Total Estimated Cost: ${UI.formatCurrency(res.fertilizers.reduce((sum, f) => sum + (f.estimated_cost || 0), 0))}</span>
              ${UI.renderEconBadge(options.econSource, options.econYear)}
            </div>
          `;
        } else {
          // Soil already meets needs
          contentDiv.innerHTML = `
            <div class="empty-state" style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:var(--radius-md); padding:1.5rem; text-align:center;">
              <div style="font-size:2rem; margin-bottom:0.5rem;">🌿</div>
              <h4 style="color:#166534; font-weight:700; margin-bottom:0.35rem;">Soil Already Meets This Crop's Needs</h4>
              <p style="color:#15803d; font-size:0.9rem; margin-bottom:0;">
                ${res.message || "Soil nutrient levels are sufficient. No additional chemical fertilizer is needed."}
              </p>
            </div>
          `;
        }
      } catch (err) {
        console.error("Fertilizer plan error:", err);
        UI.showToast(err.message || "Failed to load fertilizer advice", "danger");

        const msgLower = (err.message || "").toLowerCase();
        if (msgLower.includes("no soil test")) {
          contentDiv.innerHTML = `
            <div class="empty-state" style="background:#fffbeb; border:1px solid #fef3c7; border-radius:var(--radius-md); padding:1.5rem; text-align:center;">
              <div style="font-size:2rem; margin-bottom:0.5rem;">🧪</div>
              <h4 style="color:#92400e; font-weight:700; margin-bottom:0.35rem;">No Soil Test Yet</h4>
              <p style="color:#b45309; font-size:0.88rem; margin-bottom:1rem;">
                No soil test record found for this farm. Record a soil test first to generate a tailored fertilizer plan.
              </p>
              <a href="/ui/farms" class="btn btn-primary btn-sm">+ Record Soil Test on Farms Page</a>
            </div>
          `;
        } else {
          contentDiv.innerHTML = `
            <div class="empty-state" style="color:var(--danger); background:#fef2f2; border:1px solid #fecaca; border-radius:var(--radius-md); padding:1.5rem; text-align:center;">
              <p style="font-weight:600; margin-bottom:0.5rem;">Could not load fertilizer plan</p>
              <p style="font-size:0.85rem; margin-bottom:0;">${err.message || "An unexpected error occurred."}</p>
            </div>
          `;
        }
      }
    };

    if (cropId) {
      pickerWrapper.style.display = "none";
      fetchAndRenderAdvice(cropId, cropName);
    } else {
      pickerWrapper.style.display = "block";
      try {
        const crops = await API.getCropsLocalized();
        if (!crops || crops.length === 0) {
          contentDiv.innerHTML = `<div class="empty-state"><p>No crops available for planning.</p></div>`;
          return;
        }

        cropSelect.innerHTML = crops.map((c) => `
          <option value="${c.crop_id}">${c.localized_name || c.crop_name}</option>
        `).join("");

        cropSelect.onchange = () => {
          const selectedId = cropSelect.value;
          const opt = cropSelect.options[cropSelect.selectedIndex];
          fetchAndRenderAdvice(selectedId, opt ? opt.textContent : "");
        };

        const initialCropId = cropSelect.value;
        const initialOpt = cropSelect.options[cropSelect.selectedIndex];
        fetchAndRenderAdvice(initialCropId, initialOpt ? initialOpt.textContent : "");
      } catch (err) {
        UI.showError(err, "Failed to load crops list for fertilizer plan");
      }
    }

    UI.openModal("global-fertilizer-modal");
  },

  renderEconBadge(econSource, econYear) {
    if (econSource && String(econSource).trim()) {
      const template = UI.t('econ_source_label', 'Yield and cost estimate from: {source} ({year})');
      const label = template
        .replace('{source}', econSource)
        .replace('{year}', econYear || '');
      return `<span class="badge" style="background:var(--primary-subtle); color:var(--primary); font-weight:600; border:1px solid var(--primary); font-size:0.75rem;">${label}</span>`;
    }
    return `<span class="badge" style="background:var(--warning-subtle, #FEF3C7); color:var(--warning-terracotta, #B45309); font-weight:600; border:1px solid #FCD34D; font-size:0.75rem;">⚠️ ${UI.t('econ_placeholder_warning', 'Sample figures - not verified yet')}</span>`;
  },

  renderWhyPanel(data, options = {}) {
    const summaryText = (UI.t('why_summary_' + data.summary_level, 'Match score'))
      .replace('{good}', data.good_count);

    const strengths = (data.items || []).filter(it => it.status === 'ideal' || it.status === 'ok');
    const watch = (data.items || [])
      .filter(it => it.status !== 'ideal' && it.status !== 'ok')
      .sort((a, b) => (a.score || 0) - (b.score || 0));

    const getStatusChip = (status) => {
      let chipClass = 'why-status-ideal';
      if (status === 'ideal' || status === 'ok') {
        chipClass = 'why-status-ideal';
      } else if (status.startsWith('slightly_')) {
        chipClass = 'why-status-slightly_low';
      } else if (status === 'low' || status === 'high') {
        chipClass = 'why-status-low';
      } else {
        chipClass = 'why-status-very_low';
      }
      const statusLabel = UI.t('why_status_' + status, status);
      return `<span class="why-status-chip ${chipClass}">${statusLabel}</span>`;
    };

    const renderItemRow = (it) => {
      const isNutrient = ['nitrogen', 'phosphorus', 'potassium'].includes(it.param);
      const localizedParam = UI.t(it.param, it.param);
      const yourValLabel = UI.t('why_your_value', 'Yours');
      const idealLabel = UI.t('why_ideal_range', 'Ideal');

      const idealStr = isNutrient
        ? `${idealLabel}: about ${it.ideal_min}`
        : `${idealLabel}: ${it.ideal_min} - ${it.ideal_max}`;

      const valuesLine = `${yourValLabel}: ${it.value} / ${idealStr}`;

      return `
        <div class="why-item-row" style="margin-bottom:0.65rem;">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.35rem 0.6rem; font-size:0.85rem;">
            <div style="display:flex; align-items:center; gap:0.4rem; flex-wrap:wrap;">
              <strong style="color:var(--ink);">${localizedParam}</strong>
              ${getStatusChip(it.status)}
            </div>
            <div style="font-size:0.8rem; color:var(--muted); font-weight:500;">
              ${valuesLine}
            </div>
          </div>
          <div class="bar-track" style="margin-top:0.3rem; height:5px; background:var(--border); border-radius:var(--radius-full); overflow:hidden;">
            <div class="bar-fill" style="width:${Math.min(100, Math.max(0, it.score))}%; height:100%; border-radius:var(--radius-full);"></div>
          </div>
        </div>
      `;
    };

    let tipsHtml = '';
    if (data.tips && data.tips.length > 0) {
      tipsHtml = `
        <div class="why-tips-container" style="margin-top:0.75rem; display:flex; flex-direction:column; gap:0.5rem;">
          ${data.tips.map(tipKey => {
            const tipText = UI.t(tipKey, tipKey);
            let extraAction = '';
            if (tipKey === 'why_tip_fertilizer') {
              if (options.farmId) {
                const safeName = (data.crop_name || '').replace(/'/g, "\\'");
                extraAction = `<div style="margin-top:0.35rem;"><a href="javascript:void(0)" onclick="UI.openFertilizerPlanModal({ farmId: ${options.farmId}, cropId: ${data.crop_id}, cropName: '${safeName}' })" style="color:var(--primary); font-weight:700; text-decoration:underline; font-size:0.82rem;">🌿 ${UI.t('fertilizer_plan', 'Fertilizer Plan')} &rarr;</a></div>`;
              } else {
                extraAction = `<div style="margin-top:0.35rem;"><a href="/register" style="color:var(--primary); font-weight:700; text-decoration:underline; font-size:0.82rem;">🌿 ${UI.t('fertilizer_plan', 'Fertilizer Plan')} &rarr;</a></div>`;
              }
            }
            return `
              <div class="why-tip-box">
                <div>💡 ${tipText}</div>
                ${extraAction}
              </div>
            `;
          }).join('')}
        </div>
      `;
    }

    return `
      <div class="why-panel" style="font-size:0.85rem; line-height:1.5;">
        <!-- Summary Line -->
        <div style="font-weight:700; color:var(--ink); margin-bottom:0.75rem; padding-bottom:0.5rem; border-bottom:1px dashed var(--border);">
          ${summaryText}
        </div>

        <!-- Strengths Group -->
        ${strengths.length > 0 ? `
          <div style="margin-bottom:0.85rem;">
            <div style="font-size:0.75rem; font-weight:800; color:var(--success); text-transform:uppercase; letter-spacing:0.04em; margin-bottom:0.45rem; display:flex; align-items:center; gap:0.3rem;">
              <span>✓</span> <span>${UI.t('why_strengths', 'What matches well')}</span>
            </div>
            ${strengths.map(renderItemRow).join('')}
          </div>
        ` : ''}

        <!-- Watch Group -->
        ${watch.length > 0 ? `
          <div style="margin-bottom:0.85rem;">
            <div style="font-size:0.75rem; font-weight:800; color:var(--warning-terracotta, #C8553D); text-transform:uppercase; letter-spacing:0.04em; margin-bottom:0.45rem; display:flex; align-items:center; gap:0.3rem;">
              <span>⚠️</span> <span>${UI.t('why_watch', 'What to watch')}</span>
            </div>
            ${watch.map(renderItemRow).join('')}
          </div>
        ` : ''}

        <!-- Tips -->
        ${tipsHtml}
      </div>
    `;
  },
};

// Auto-initialize theme as early as possible
if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => UI.initTheme());
  } else {
    UI.initTheme();
  }
}

// Explicit global exports for browser environments
if (typeof window !== "undefined") {
  window.API = API;
  window.UI = UI;
}


