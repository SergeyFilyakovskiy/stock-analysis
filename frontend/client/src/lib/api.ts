// Typed API helpers for all backend services
import { apiRequest, setTokens, clearTokens, getRefreshToken } from "./queryClient";
import type {
  TokenResponse,
  ProfileResponse,
  SecuritiesListResponse,
  SecurityResponse,
  OHLCVResponse,
  DividendResponse,
  MarketIndexResponse,
  CompanyReportSchema,
  ScreenerResultSchema,
} from "@shared/schema";

// ── Auth ──────────────────────────────────────────────────

const AUTH = "/api/v1/auth";

export const authApi = {
  register: (data: { email: string; password: string; first_name?: string; last_name?: string }) =>
    apiRequest<TokenResponse>("POST", `${AUTH}/register`, data),

  login: (email: string, password: string) =>
    apiRequest<TokenResponse>("POST", `${AUTH}/login`, { email, password }),

  logout: () => apiRequest<void>("POST", `${AUTH}/logout`),

  me: () => apiRequest<ProfileResponse>("GET", `${AUTH}/me`),

  refresh: async () => {
    const rt = getRefreshToken();
    if (!rt) throw new Error("No refresh token");
    const tokens = await apiRequest<TokenResponse>("POST", `${AUTH}/refresh`, { refresh_token: rt });
    setTokens(tokens.access_token, tokens.refresh_token);
    return tokens;
  },
};

// ── OAuth ─────────────────────────────────────────────────
const OAUTH = "/api/v1/oauth";

export const oauthApi = {
  redirectUrl: (provider: "google" | "github") => `${OAUTH}/${provider}`,
  // Callback is handled server-side; after redirect, the URL contains tokens as query params
};

// ── Market ────────────────────────────────────────────────

const MARKET = "/api/v1/market";

export const marketApi = {
  searchSecurities: (q: string) =>
    apiRequest<SecuritiesListResponse>("GET", `${MARKET}/securities?q=${encodeURIComponent(q)}`),

  getSecurity: (ticker: string) =>
    apiRequest<SecurityResponse>("GET", `${MARKET}/securities/${ticker}`),

  getLastPrice: (ticker: string) =>
    apiRequest<{ ticker: string; price: string }>("GET", `${MARKET}/securities/${ticker}/price`),

  getOHLCV: (ticker: string, from: string, to: string, interval = "1d") =>
    apiRequest<OHLCVResponse>(
      "GET",
      `${MARKET}/securities/${ticker}/ohlcv?from=${from}&to=${to}&interval=${interval}`,
    ),

  getHistory: (ticker: string, from: string, to: string) =>
    apiRequest<unknown[]>("GET", `${MARKET}/securities/${ticker}/history?from=${from}&to=${to}`),

  getDividends: (ticker: string) =>
    apiRequest<DividendResponse[]>("GET", `${MARKET}/securities/${ticker}/dividends`),

  getIndices: () => apiRequest<MarketIndexResponse[]>("GET", `${MARKET}/indices`),
};

// ── Fundamental ───────────────────────────────────────────

const FUND = "/api/v1/fundamental";

export const fundamentalApi = {
  getCompany: (ticker: string) =>
    apiRequest<CompanyReportSchema>("GET", `${FUND}/companies/${ticker}/report`),

  getMetrics: (ticker: string) =>
    apiRequest<unknown>("GET", `${FUND}/companies/${ticker}/metrics`),

  getReports: (ticker: string, limit = 8) =>
    apiRequest<unknown[]>("GET", `${FUND}/companies/${ticker}/reports?limit=${limit}`),

  screener: (params: Record<string, string | number | undefined>) => {
    const qs = Object.entries(params)
      .filter(([, v]) => v !== undefined)
      .map(([k, v]) => `${k}=${v}`)
      .join("&");
    return apiRequest<ScreenerResultSchema>("GET", `${FUND}/screener${qs ? `?${qs}` : ""}`);
  },

  compare: (tickers: string[], includeValuation = true) =>
    apiRequest<CompanyReportSchema[]>("POST", `${FUND}/compare`, {
      tickers,
      include_valuation: includeValuation,
    }),
};
