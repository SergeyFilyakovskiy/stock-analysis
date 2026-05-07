// Shared types matching the backend API schemas

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface ProfileResponse {
  id: string;
  email: string;
  role: string;
  first_name: string | null;
  last_name: string | null;
  bio: string | null;
  avatar_url: string | null;
  is_verified: boolean;
  full_name: string | null;
}

export interface SecurityResponse {
  ticker: string;
  name: string;
  exchange: string | null;
  sector: string | null;
  is_active: boolean;
}

export interface SecuritiesListResponse {
  items: SecurityResponse[];
  total: number;
}

export interface PriceBarResponse {
  time: string;
  ticker: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number;
  volume: number | null;
  source: string | null;
}

export interface OHLCVResponse {
  ticker: string;
  interval: string;
  bars: PriceBarResponse[];
}

export interface DividendResponse {
  ticker: string;
  ex_date: string;
  pay_date: string | null;
  amount: number;
  currency: string;
}

export interface MarketIndexResponse {
  index_code: string;
  name: string;
  description: string | null;
  is_active: boolean;
}

export interface CompanySchema {
  ticker: string;
  name: string;
  sector: string;
  industry: string;
  market_cap: number | null;
  country: string;
}

export interface FinancialMetricsSchema {
  ticker: string;
  calculated_at: string;
  pe: number | null;
  pb: number | null;
  ps: number | null;
  ev_ebitda: number | null;
  roe: number | null;
  roa: number | null;
  roic: number | null;
  gross_margin: number | null;
  net_margin: number | null;
  ebitda_margin: number | null;
  debt_equity: number | null;
  dividend_yield: number | null;
}

export interface ValuationSchema {
  model_name: string;
  estimated_value: number;
  current_price: number;
  confidence_score: number;
  is_undervalued: boolean;
  upside_pct: number;
}

export interface FinancialReportSchema {
  period: string;
  period_type: string;
  fiscal_year: number;
  fiscal_quarter: number | null;
  revenue: number | null;
  net_income: number | null;
  ebitda: number | null;
  free_cash_flow: number | null;
  eps_diluted: number | null;
  source: string;
}

export interface AnalystRatingSchema {
  analyst_firm: string;
  rating: string;
  target_price: number | null;
  rating_date: string;
}

export interface CompanyReportSchema {
  ticker: string;
  company: CompanySchema | null;
  current_price: number;
  metrics: FinancialMetricsSchema | null;
  reports: FinancialReportSchema[];
  valuations: ValuationSchema[];
  analyst_ratings: AnalystRatingSchema[];
}

export interface ScreenerResultSchema {
  items: FinancialMetricsSchema[];
  total: number;
  limit: number;
  offset: number;
}
