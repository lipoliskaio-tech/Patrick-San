// Funções utilitárias para comunicação com a API do backend.

function getToken() {
  return localStorage.getItem("admin_token");
}

function requireAuth() {
  const token = getToken();
  if (!token) {
    window.location.href = "login.html";
    throw new Error("Não autenticado");
  }
  return token;
}

async function apiRequest(path, options = {}) {
  const token = getToken();
  const headers = Object.assign(
    { "Content-Type": "application/json" },
    options.headers || {}
  );
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    localStorage.removeItem("admin_token");
    window.location.href = "login.html";
    throw new Error("Sessão expirada. Faça login novamente.");
  }

  if (response.status === 204) {
    return null;
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const message = data.detail || data.message || "Erro na requisição.";
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }

  return data;
}

async function apiLogin(username, password) {
  const response = await fetch(`${API_BASE_URL}/admin/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Usuário ou senha inválidos.");
  }
  return data;
}

async function fetchDashboard() {
  return apiRequest("/admin/dashboard");
}

async function searchLicenses(params = {}) {
  const query = new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v))
  ).toString();
  return apiRequest(`/admin/licenses${query ? `?${query}` : ""}`);
}

async function createLicenses(payload) {
  return apiRequest("/admin/licenses", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

async function banLicense(id) {
  return apiRequest(`/admin/licenses/${id}/ban`, { method: "PATCH" });
}

async function suspendLicense(id) {
  return apiRequest(`/admin/licenses/${id}/suspend`, { method: "PATCH" });
}

async function reactivateLicense(id) {
  return apiRequest(`/admin/licenses/${id}/reactivate`, { method: "PATCH" });
}

async function resetHwid(id) {
  return apiRequest(`/admin/licenses/${id}/reset-hwid`, { method: "PATCH" });
}

async function updateExpiry(id, payload) {
  return apiRequest(`/admin/licenses/${id}/expiry`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

async function deleteLicense(id) {
  return apiRequest(`/admin/licenses/${id}`, { method: "DELETE" });
}

async function getLicenseHistory(id) {
  return apiRequest(`/admin/licenses/${id}/history`);
}

async function getMaintenance() {
  return apiRequest("/admin/maintenance");
}

async function setMaintenance(payload) {
  return apiRequest("/admin/maintenance", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

async function listVersions() {
  return apiRequest("/admin/versions");
}

async function createVersion(payload) {
  return apiRequest("/admin/versions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

function logout() {
  localStorage.removeItem("admin_token");
  window.location.href = "login.html";
}
