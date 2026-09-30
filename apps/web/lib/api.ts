const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  status: number;
  validationErrors?: Record<string, string>;
}

export interface RequestOptions extends RequestInit {
  timeoutMs?: number;
  retries?: number;
  skipAuth?: boolean;
}

/**
 * Normalizes any backend error response (string, FastAPI 422 list, nested object, HTML)
 * into a safe, human-readable string suitable for display in UI without React crash.
 */
export function normalizeApiError(data: any, status: number): { error: string; validationErrors?: Record<string, string> } {
  // Offline or network connection failure
  if (status === 0) {
    if (typeof navigator !== "undefined" && !navigator.onLine) {
      return { error: "You appear to be offline. Please check your internet connection." };
    }
    return { error: "Unable to connect to the MoTA Scholarship portal. Please ensure the server is running." };
  }

  // HTTP Status Specific Fallbacks
  if (status === 401) {
    return { error: "Your session has expired. Please log in again to continue." };
  }
  if (status === 403) {
    return { error: "Access denied. You do not have the required institutional permissions for this action." };
  }
  if (status === 404) {
    return { error: "The requested scholarship application, document, or scheme was not found." };
  }
  if (status === 429) {
    return { error: "Too many requests. For security, please wait a moment before trying again." };
  }
  if (status >= 500) {
    return { error: "Government portal services are currently undergoing maintenance. Please try again shortly." };
  }

  // Parse structured validation error (FastAPI 422 standard)
  if (data && typeof data === "object") {
    // If detail is an array of errors: [{ loc: ['body', 'field_name'], msg: 'error description' }]
    if (Array.isArray(data.detail)) {
      const valErrors: Record<string, string> = {};
      const messages: string[] = [];

      data.detail.forEach((err: any) => {
        if (typeof err === "object" && err !== null) {
          const field = Array.isArray(err.loc) ? err.loc[err.loc.length - 1] : "field";
          const msg = err.msg || "Invalid input";
          valErrors[field] = msg;
          messages.push(`${field}: ${msg}`);
        } else if (typeof err === "string") {
          messages.push(err);
        }
      });

      return {
        error: messages.length > 0 ? messages.join("; ") : "Input validation failed. Please check your form entries.",
        validationErrors: valErrors,
      };
    }

    // If detail is a plain string
    if (typeof data.detail === "string" && data.detail.trim().length > 0) {
      return { error: data.detail };
    }

    // If message is a plain string
    if (typeof data.message === "string" && data.message.trim().length > 0) {
      return { error: data.message };
    }

    // If error is a plain string
    if (typeof data.error === "string" && data.error.trim().length > 0) {
      return { error: data.error };
    }
  }

  return { error: `An unexpected request error occurred (Status code: ${status}).` };
}

/**
 * Robust fetch wrapper hardened against:
 * 1. Infinite hanging via configurable timeout (default 15s)
 * 2. Unhandled FastAPI 422 object validation crashes
 * 3. Expired authentication (auto-cleans on 401)
 * 4. Network offline states
 * 5. Transient gateway failures with automatic retries for idempotent GET requests
 */
export async function fetchApi<T = any>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<ApiResponse<T>> {
  const {
    timeoutMs = 15000,
    retries = options.method === "POST" || options.method === "PUT" ? 0 : 1,
    skipAuth = false,
    ...fetchOptions
  } = options;

  const url = `${API_BASE}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(fetchOptions.headers as Record<string, string>),
  };

  if (!skipAuth && typeof window !== "undefined") {
    const token = localStorage.getItem("mota_access_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  // Pre-flight check for network connectivity
  if (typeof navigator !== "undefined" && !navigator.onLine) {
    return {
      error: "You are currently offline. Please check your network connection.",
      status: 0,
    };
  }

  let attempt = 0;
  while (attempt <= retries) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const res = await fetch(url, {
        ...fetchOptions,
        headers,
        signal: controller.signal,
        credentials: "include",
      });

      clearTimeout(timeoutId);
      const status = res.status;

      let data: any = null;
      const contentType = res.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        try {
          data = await res.json();
        } catch {
          data = null;
        }
      } else {
        try {
          const text = await res.text();
          data = text ? { detail: text } : null;
        } catch {
          data = null;
        }
      }

      if (!res.ok) {
        // If 401 Unauthorized, safely clean storage on client
        if (status === 401 && typeof window !== "undefined") {
          localStorage.removeItem("mota_access_token");
          localStorage.removeItem("mota_user");
        }

        // Retry 502/503/504 for GET requests
        if ([502, 503, 504].includes(status) && attempt < retries) {
          attempt++;
          await new Promise((r) => setTimeout(r, 600 * attempt));
          continue;
        }

        const normalized = normalizeApiError(data, status);
        return {
          error: normalized.error,
          validationErrors: normalized.validationErrors,
          status,
        };
      }

      return { data, status };
    } catch (err: any) {
      clearTimeout(timeoutId);

      // Handle abort / timeout
      if (err.name === "AbortError") {
        return {
          error: `Request timed out after ${Math.round(timeoutMs / 1000)} seconds. Please verify connection speed.`,
          status: 408,
        };
      }

      // Retry transient network failures for idempotent GET requests
      if (attempt < retries) {
        attempt++;
        await new Promise((r) => setTimeout(r, 600 * attempt));
        continue;
      }

      const normalized = normalizeApiError(null, 0);
      return {
        error: normalized.error,
        status: 0,
      };
    }
  }

  return {
    error: "Connection failed after multiple attempts.",
    status: 0,
  };
}
