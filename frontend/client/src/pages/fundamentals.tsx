import { useState } from "react";
import { useParams, Link } from "wouter";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { fundamentalApi } from "../lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import type { FinancialReportSchema, ValuationSchema } from "@shared/schema";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell,
} from "recharts";

function MetricRow({ label, value, suffix = "" }: { label: string; value: number | null | undefined; suffix?: string }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-border last:border-0">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-xs font-mono font-medium text-foreground tabular">
        {value != null ? `${value.toFixed(2)}${suffix}` : "—"}
      </span>
    </div>
  );
}

function ValuationCard({ v }: { v: ValuationSchema }) {
  const up = v.is_undervalued;
  return (
    <div className="bg-card border border-border rounded-md p-4 space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-xs text-muted-foreground uppercase tracking-wide">{v.model_name}</p>
        <span className={cn("text-xs font-medium px-2 py-0.5 rounded", up ? "text-success bg-success/10" : "text-destructive bg-destructive/10")}>
          {up ? "Undervalued" : "Overvalued"}
        </span>
      </div>
      <div className="flex items-end gap-3">
        <div>
          <p className="text-[10px] text-muted-foreground">Est. Value</p>
          <p className="text-sm font-semibold font-mono tabular text-foreground">${Number(v.estimated_value).toFixed(2)}</p>
        </div>
        <div>
          <p className="text-[10px] text-muted-foreground">Current</p>
          <p className="text-sm font-semibold font-mono tabular text-foreground">${Number(v.current_price).toFixed(2)}</p>
        </div>
        <div className="ml-auto text-right">
          <p className="text-[10px] text-muted-foreground">Upside</p>
          <p className={cn("text-sm font-semibold tabular", Number(v.upside_pct) >= 0 ? "text-success" : "text-destructive")}>
            {Number(v.upside_pct) >= 0 ? "+" : ""}{Number(v.upside_pct).toFixed(1)}%
          </p>
        </div>
      </div>
      <div className="flex items-center gap-1">
        <div className="flex-1 h-1 bg-muted rounded-full overflow-hidden">
          <div className="h-full bg-primary rounded-full" style={{ width: `${v.confidence_score * 100}%` }} />
        </div>
        <span className="text-[10px] text-muted-foreground">{(v.confidence_score * 100).toFixed(0)}% confidence</span>
      </div>
    </div>
  );
}

const COLORS = ["hsl(174,72%,46%)", "hsl(174,62%,38%)", "hsl(142,71%,45%)", "hsl(38,92%,50%)"];

function RevenueChart({ reports }: { reports: FinancialReportSchema[] }) {
  const annual = reports.filter(r => r.period_type === "annual").slice(0, 8);
  const data = annual.map(r => ({
    period: r.period,
    revenue: r.revenue != null ? Math.round(Number(r.revenue) / 1e6) : null,
    net_income: r.net_income != null ? Math.round(Number(r.net_income) / 1e6) : null,
  })).reverse();

  if (data.length === 0) return <p className="text-xs text-muted-foreground">No annual reports</p>;

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 8 }}>
        <XAxis dataKey="period" tick={{ fill: "hsl(220,8%,52%)", fontSize: 10 }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: "hsl(220,8%,52%)", fontSize: 10 }} axisLine={false} tickLine={false} tickFormatter={v => `$${v}M`} />
        <Tooltip
          contentStyle={{ background: "hsl(220,13%,10%)", border: "1px solid hsl(220,10%,16%)", borderRadius: 6, fontSize: 11 }}
          labelStyle={{ color: "hsl(210,18%,80%)" }}
          formatter={(v: number) => [`$${v}M`, ""]}
        />
        <Bar dataKey="revenue" name="Revenue" fill="hsl(174,72%,46%)" opacity={0.85} radius={[2, 2, 0, 0]} />
        <Bar dataKey="net_income" name="Net Income" fill="hsl(142,71%,45%)" opacity={0.75} radius={[2, 2, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export default function FundamentalsPage() {
  const { ticker } = useParams<{ ticker: string }>();
  const [model, setModel] = useState<"dcf" | "pe" | "ev_ebitda">("dcf");

  const { data: report, isLoading } = useQuery({
    queryKey: [`/api/v1/fundamental/companies/${ticker}/report`, model],
    queryFn: () => fundamentalApi.getCompany(ticker!),
    enabled: !!ticker,
  });

  return (
    <div className="p-5 space-y-5 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link href={`/chart/${ticker}`} className="text-muted-foreground hover:text-foreground transition-colors" data-testid="btn-back">
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <h1 className="text-base font-semibold text-foreground font-mono">{ticker}</h1>
          {report?.company && <p className="text-xs text-muted-foreground">{report.company.name}</p>}
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {[0,1,2,3].map(i => <Skeleton key={i} className="h-16" />)}
          </div>
          <Skeleton className="h-48" />
        </div>
      ) : !report ? (
        <div className="text-center py-16 text-muted-foreground">
          <p className="text-sm">No data available for {ticker}</p>
        </div>
      ) : (
        <Tabs defaultValue="overview">
          <TabsList className="h-8">
            <TabsTrigger value="overview" className="text-xs" data-testid="tab-overview">Overview</TabsTrigger>
            <TabsTrigger value="financials" className="text-xs" data-testid="tab-financials">Financials</TabsTrigger>
            <TabsTrigger value="valuation" className="text-xs" data-testid="tab-valuation">Valuation</TabsTrigger>
            <TabsTrigger value="analysts" className="text-xs" data-testid="tab-analysts">Analysts</TabsTrigger>
          </TabsList>

          {/* Overview */}
          <TabsContent value="overview" className="space-y-4 mt-4">
            {/* Company info */}
            {report.company && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {[
                  { label: "Sector",     value: report.company.sector },
                  { label: "Industry",   value: report.company.industry },
                  { label: "Country",    value: report.company.country },
                  { label: "Market Cap", value: report.company.market_cap ? `$${(Number(report.company.market_cap) / 1e9).toFixed(2)}B` : "—" },
                ].map(({ label, value }) => (
                  <div key={label} className="bg-card border border-border rounded-md px-3 py-2.5">
                    <p className="text-xs text-muted-foreground">{label}</p>
                    <p className="text-sm font-medium text-foreground mt-0.5 truncate">{value}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Key metrics */}
            {report.metrics && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="bg-card border border-border rounded-md px-4 py-3">
                  <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Valuation Ratios</h3>
                  <MetricRow label="P/E"       value={report.metrics.pe} />
                  <MetricRow label="P/B"       value={report.metrics.pb} />
                  <MetricRow label="P/S"       value={report.metrics.ps} />
                  <MetricRow label="EV/EBITDA" value={report.metrics.ev_ebitda} />
                  <MetricRow label="Div. Yield" value={report.metrics.dividend_yield} suffix="%" />
                </div>
                <div className="bg-card border border-border rounded-md px-4 py-3">
                  <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Profitability</h3>
                  <MetricRow label="ROE"          value={report.metrics.roe != null ? report.metrics.roe * 100 : null} suffix="%" />
                  <MetricRow label="ROA"          value={report.metrics.roa != null ? report.metrics.roa * 100 : null} suffix="%" />
                  <MetricRow label="ROIC"         value={report.metrics.roic != null ? report.metrics.roic * 100 : null} suffix="%" />
                  <MetricRow label="Gross Margin" value={report.metrics.gross_margin != null ? report.metrics.gross_margin * 100 : null} suffix="%" />
                  <MetricRow label="Net Margin"   value={report.metrics.net_margin != null ? report.metrics.net_margin * 100 : null} suffix="%" />
                </div>
              </div>
            )}
          </TabsContent>

          {/* Financials */}
          <TabsContent value="financials" className="space-y-4 mt-4">
            {report.reports.length > 0 ? (
              <>
                <div className="bg-card border border-border rounded-md p-4">
                  <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">Revenue & Net Income (Annual, $M)</h3>
                  <RevenueChart reports={report.reports} />
                </div>
                <div className="bg-card border border-border rounded-md overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-border bg-muted/40">
                          {["Period", "Revenue", "Net Income", "EBITDA", "FCF", "EPS"].map(h => (
                            <th key={h} className="px-4 py-2.5 text-left text-muted-foreground font-medium">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {report.reports.slice(0, 12).map((r, i) => (
                          <tr key={i} className="border-b border-border last:border-0 hover:bg-muted/30 transition-colors">
                            <td className="px-4 py-2.5 font-medium text-foreground">{r.period}</td>
                            <td className="px-4 py-2.5 font-mono tabular text-foreground">{r.revenue != null ? `$${(Number(r.revenue)/1e6).toFixed(0)}M` : "—"}</td>
                            <td className="px-4 py-2.5 font-mono tabular">
                              <span className={r.net_income != null && Number(r.net_income) >= 0 ? "text-success" : "text-destructive"}>
                                {r.net_income != null ? `$${(Number(r.net_income)/1e6).toFixed(0)}M` : "—"}
                              </span>
                            </td>
                            <td className="px-4 py-2.5 font-mono tabular text-foreground">{r.ebitda != null ? `$${(Number(r.ebitda)/1e6).toFixed(0)}M` : "—"}</td>
                            <td className="px-4 py-2.5 font-mono tabular text-foreground">{r.free_cash_flow != null ? `$${(Number(r.free_cash_flow)/1e6).toFixed(0)}M` : "—"}</td>
                            <td className="px-4 py-2.5 font-mono tabular text-foreground">{r.eps_diluted != null ? `$${Number(r.eps_diluted).toFixed(2)}` : "—"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-12 text-muted-foreground"><p className="text-sm">No financial reports available</p></div>
            )}
          </TabsContent>

          {/* Valuation */}
          <TabsContent value="valuation" className="space-y-4 mt-4">
            {report.valuations.length > 0 ? (
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {report.valuations.map((v) => <ValuationCard key={v.model_name} v={v} />)}
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground"><p className="text-sm">No valuation data available</p></div>
            )}
          </TabsContent>

          {/* Analysts */}
          <TabsContent value="analysts" className="mt-4">
            {report.analyst_ratings.length > 0 ? (
              <div className="bg-card border border-border rounded-md overflow-hidden">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-border bg-muted/40">
                      {["Firm", "Rating", "Target Price", "Date"].map(h => (
                        <th key={h} className="px-4 py-2.5 text-left text-muted-foreground font-medium">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {report.analyst_ratings.map((r, i) => (
                      <tr key={i} className="border-b border-border last:border-0 hover:bg-muted/30 transition-colors">
                        <td className="px-4 py-2.5 font-medium text-foreground">{r.analyst_firm}</td>
                        <td className="px-4 py-2.5">
                          <span className={cn("px-1.5 py-0.5 rounded text-xs font-medium",
                            r.rating.toLowerCase().includes("buy") ? "bg-success/15 text-success" :
                            r.rating.toLowerCase().includes("sell") ? "bg-destructive/15 text-destructive" :
                            "bg-muted text-muted-foreground"
                          )}>
                            {r.rating}
                          </span>
                        </td>
                        <td className="px-4 py-2.5 font-mono tabular text-foreground">
                          {r.target_price ? `$${Number(r.target_price).toFixed(2)}` : "—"}
                        </td>
                        <td className="px-4 py-2.5 text-muted-foreground">{r.rating_date}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground"><p className="text-sm">No analyst ratings available</p></div>
            )}
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
