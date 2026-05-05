import { mockApiRequest } from "./mockServer";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "/api").replace(/\/$/, "");

type QueryValue = string | number | boolean | null | undefined;

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

interface RequestOptions extends RequestInit {
  query?: Record<string, QueryValue>;
}

const MOCK_API_ENABLED =
  import.meta.env.VITE_USE_MOCK_API === "true" ||
  (import.meta.env.DEV && !import.meta.env.VITE_API_BASE_URL);

const DEV_MOCK_FALLBACK_ENABLED =
  import.meta.env.DEV && import.meta.env.VITE_DISABLE_MOCK_FALLBACK !== "true";

function buildUrl(path: string, query?: Record<string, QueryValue>) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const url = new URL(`${API_BASE_URL}${normalizedPath}`, window.location.origin);

  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    });
  }

  return url.toString();
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type") || "";
  const isJson = contentType.includes("application/json");
  const body = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const message =
      typeof body === "object" && body && "message" in body
        ? String(body.message)
        : typeof body === "string" && body
        ? body
        : "请求失败，请稍后重试";
    throw new ApiError(message, response.status);
  }

  return body as T;
}

async function request<T>(path: string, options: RequestOptions = {}) {
  const { headers, query, ...init } = options;
  const requestConfig = {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
  };

  if (MOCK_API_ENABLED) {
    return mockApiRequest<T>({
      body: init.body,
      method: init.method ?? "GET",
      path,
      query,
    });
  }

  try {
    const response = await fetch(buildUrl(path, query), requestConfig);
    return parseResponse<T>(response);
  } catch (error) {
    if (DEV_MOCK_FALLBACK_ENABLED) {
      return mockApiRequest<T>({
        body: init.body,
        method: init.method ?? "GET",
        path,
        query,
      });
    }
    throw error;
  }
}

export const apiClient = {
  delete: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "DELETE" }),
  get: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "GET" }),
  patch: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, {
      ...options,
      body: body === undefined ? undefined : JSON.stringify(body),
      method: "PATCH",
    }),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, {
      ...options,
      body: body === undefined ? undefined : JSON.stringify(body),
      method: "POST",
    }),
};

export function getErrorMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message;
  }

  return "请求失败，请稍后重试";
}
