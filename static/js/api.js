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
        if (!window.location.pathname.includes("/ui/login") && !window.location.pathname.includes("/ui/register")) {
          window.location.href = "/ui/login";
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
  login(identifier, password) {
    return this.request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ identifier, password }),
    });
  },

  register(payload) {
    return this.request("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getMe() {
    return this.request("/auth/me");
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
      const badge = document.getElementById("nav-unread-badge");
      if (!badge) return;
      const data = await API.getUnreadAlertsCount();
      const count = data.unread_count || 0;
      if (count > 0) {
        badge.textContent = count > 99 ? "99+" : count;
        badge.style.display = "inline-block";
      } else {
        badge.style.display = "none";
      }
    } catch (e) {
      // Ignore if unauthenticated or offline
    }
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
          el.textContent = dict[key];
        }
      });

      document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
        const key = el.getAttribute("data-i18n-placeholder");
        if (dict[key]) {
          el.placeholder = dict[key];
        }
      });

      window.dispatchEvent(new CustomEvent("agri_lang_changed", { detail: { lang: activeLang, dict } }));
    } catch (err) {
      console.warn("Could not load translations:", err);
    }
  },

  renderNavbar(activePage = "dashboard") {
    const farmer = API.getFarmer();
    const navPlaceholder = document.getElementById("navbar-placeholder");
    if (!navPlaceholder) return;

    navPlaceholder.innerHTML = `
      <nav class="navbar">
        <a href="/ui/dashboard" class="nav-brand">
          <span class="logo-icon">🌱</span> AgriPredict
        </a>
        <div class="nav-links">
          <a href="/ui/dashboard" class="nav-link ${activePage === 'dashboard' ? 'active' : ''}" data-i18n="dashboard">Dashboard</a>
          <a href="/ui/farms" class="nav-link ${activePage === 'farms' ? 'active' : ''}" data-i18n="my_farms">My Farms</a>
          <a href="/ui/prices" class="nav-link ${activePage === 'prices' ? 'active' : ''}" data-i18n="market_prices">Market Prices</a>
          <a href="/ui/alerts" class="nav-link ${activePage === 'alerts' ? 'active' : ''}" data-i18n="alerts">Alerts</a>
          ${farmer && farmer.role === 'admin' ? `<a href="/ui/admin" class="nav-link ${activePage === 'admin' ? 'active' : ''}" style="color:#0284c7;font-weight:700;">⚙️ Admin</a>` : ''}
        </div>
        <div class="nav-user">
          <a href="/ui/alerts" class="nav-bell-link" title="Notifications & Weather Alerts">
            🔔<span id="nav-unread-badge" class="nav-bell-badge" style="display:none;">0</span>
          </a>
          <div class="lang-switch">
            <button type="button" class="lang-btn ${API.getLang() === 'en' ? 'active' : ''}" data-lang="en" onclick="UI.switchLanguage('en')">EN</button>
            <button type="button" class="lang-btn ${API.getLang() === 'mr' ? 'active' : ''}" data-lang="mr" onclick="UI.switchLanguage('mr')">MR</button>
            <button type="button" class="lang-btn ${API.getLang() === 'hi' ? 'active' : ''}" data-lang="hi" onclick="UI.switchLanguage('hi')">HI</button>
          </div>
          ${farmer ? `<span style="font-size:0.85rem;font-weight:600;color:#334155;">${farmer.name}</span>` : ''}
          <button class="btn btn-secondary btn-sm" onclick="UI.logout()" data-i18n="logout">Logout</button>
        </div>
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

  requireAuth() {
    const token = API.getToken();
    if (!token) {
      window.location.href = "/ui/login";
      return false;
    }
    return true;
  }
};
