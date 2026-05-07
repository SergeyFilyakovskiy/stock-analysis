import { QueryClient } from "@tanstack/react-query";

// API base — replaced by deploy_website with proxy path
const API_BASE = (window as any).__PORT_5000__ ?? "";

export { API_BASE };

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

// ---------- auth token helpers ----------
const TOKEN_KEY = "__sa_access_token__";
const REFRESH_KEY = "__sa_refresh_token__";

// We use module-level variables (not localStorage — blocked in sandboxed iframes)
let _accessToken: string | null = null;
let _refreshToken: string | null = null;

export function setTokens(access: string, refresh: string) {
  _accessToken = access;
  _refreshToken = refresh;
}

export function getAccessToken(): string | null {
  return _accessToken;
}

export function getRefreshToken(): string | null {
  return _refreshToken;
}

export function clearTokens() {
  _accessToken = null;
  _refreshToken = null;
}

// ---------- fetch wrapper ----------
export async function apiRequest<T = unknown>(
  method: string,
  path: string,
  body?: unknown,
  options?: RequestInit,
): Promise<T> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    ...options,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `HTTP ${res.status}`);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// Default query function for tanstack-query (used only when no queryFn is provided inline)
queryClient.setDefaultOptions({
  queries: {
    queryFn: async ({ queryKey }) => {
      const [path] = queryKey as string[];
      return apiRequest("GET", path as string);
    },
  },
});
