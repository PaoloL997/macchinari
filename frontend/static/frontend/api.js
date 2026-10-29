// Thin client for the same-origin REST API.

/** Error raised when the API answers with a non-2xx status or is unreachable. */
export class ApiError extends Error {
  /**
   * @param {string} message Human readable message (the server `detail` when available).
   * @param {number} status HTTP status code, 0 when the request never reached the server.
   */
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/** Read a cookie by name. */
function getCookie(name) {
  const prefix = `${name}=`;
  for (const part of document.cookie.split(";")) {
    const cookie = part.trim();
    if (cookie.startsWith(prefix)) {
      return decodeURIComponent(cookie.slice(prefix.length));
    }
  }
  return "";
}

/** Headers required by Django for unsafe methods (POST, DELETE). */
function csrfHeaders() {
  return { "X-CSRFToken": getCookie("csrftoken") };
}

/** Extract a readable message from a DRF error payload. */
function errorMessage(data, status) {
  if (data && typeof data === "object") {
    if (typeof data.detail === "string") return data.detail;
    const first = Object.values(data).flat().find((value) => typeof value === "string");
    if (first) return first;
  }
  return `Errore ${status}`;
}

/**
 * Perform a request and parse the JSON body.
 *
 * @param {string} url
 * @param {RequestInit} [options]
 * @returns {Promise<any>} Parsed JSON, or `null` for empty responses.
 * @throws {ApiError}
 */
async function request(url, options = {}) {
  let response;
  try {
    response = await fetch(url, {
      credentials: "same-origin",
      ...options,
      headers: { Accept: "application/json", ...(options.headers || {}) },
    });
  } catch {
    throw new ApiError("Connessione non riuscita", 0);
  }

  let data = null;
  if (response.status !== 204) {
    try {
      data = await response.json();
    } catch {
      data = null;
    }
  }
  if (response.status === 401) {
    // The session expired or was logged out elsewhere: back to the login page.
    const next = encodeURIComponent(window.location.pathname + window.location.search);
    window.location.assign(`/login/?next=${next}`);
    throw new ApiError("Sessione scaduta", 401);
  }
  if (!response.ok) {
    throw new ApiError(errorMessage(data, response.status), response.status);
  }
  return data;
}

export const api = {
  /** List the active machines. */
  listMachines: () => request("/api/machines/"),

  /** Read the live status of a machine. */
  getStatus: (machineId) => request(`/api/machines/${machineId}/status/`),

  /** List the files currently on the machine. */
  listFiles: (machineId) => request(`/api/machines/${machineId}/files/`),

  /** Upload a file to the machine. */
  uploadFile(machineId, file) {
    const body = new FormData();
    body.append("file", file, file.name);
    return request(`/api/machines/${machineId}/files/`, {
      method: "POST",
      headers: csrfHeaders(),
      body,
    });
  },

  /** Delete a file from the machine. */
  deleteFile: (machineId, name) =>
    request(`/api/machines/${machineId}/files/${encodeURIComponent(name)}/`, {
      method: "DELETE",
      headers: csrfHeaders(),
    }),
};
