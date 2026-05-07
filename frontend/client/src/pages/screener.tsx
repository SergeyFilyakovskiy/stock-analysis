import { useState } from "react";
import { useLocation } from "wouter";
import { useQuery } from "@tanstack/react-query";
import { SlidersHorizontal, ChevronRight, Search } from "lucide-react";
import { fundamentalApi } from "../lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { FinancialMetricsSchema } from "@shared/schema";
import { cn } from "@/lib/utils";

interface Filters {
  pe_min?: number;
  pe_max?: number;
  roe_min?: number;
  ev_ebitda_max?: number;
  debt_equity_max?: number;
  sector?: string;
}

function MetricCell({ value, suffix = "" }: { value: number | null | undefined; suffix?: string }) {
  return (
    <td className="px-3 py-2.5 font-mono tabular text-foreground text-xs">
      {value != null ? `${value.toFixed(2)}${suffix}` : "—"}
    </td>
  );
}

export default function ScreenerPage() {
  const [, navigate] = useLocation();
  const [filters, setFilters] = useState<Filters>({});
  const [activeFilters, setActiveFilters] = useState<Filters>({});
  const [page, setPage] = useState(0);

  const LIMIT = 50;

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["screener", activeFilters, page],
    queryFn: () => fundamentalApi.screener({ ...activeFilters, limit: LIMIT, offset: page * LIMIT }),
    staleTime: 60_000,
  });

  const apply = () => {
    setActiveFilters(filters);
    setPage(0);
  };

  const reset = () => {
    setFilters({});
    setActiveFilters({});
    setPage(0);
  };

  const f = (key: keyof Filters) => (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value === "" ? undefined : parseFloat(e.target.value);
    setFilters((prev) => ({ ...prev, [key]: isNaN(val as number) ? undefined : val }));
  };

  const fStr = (key: keyof Filters) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFilters((prev) => ({ ...prev, [key]: e.target.value || undefined }));
  };

  const items: FinancialMetricsSchema[] = data?.items ?? [];
  const total = data?.total ?? 0;
  const pageCount = Math.ceil(total / LIMIT);

  return (
    <div className="p-5 space-y-5 max-w-6xl mx-auto">
      <div>
        <h1 className="text-lg font-semibold text-foreground">Stock Screener</h1>
        <p className="text-xs text-muted-foreground mt-0.5">Filter companies by fundamental metrics</p>
      </div>

      {/* Filters panel */}
      <div className="bg-card border border-border rounded-lg p-4">
        <div className="flex items-center gap-2 mb-4">
          <SlidersHorizontal className="w-4 h-4 text-muted-foreground" />
          <h2 className="text-sm font-medium text-foreground">Filters</h2>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {[
            { label: "P/E Min",       key: "pe_min" as keyof Filters },
            { label: "P/E Max",       key: "pe_max" as keyof Filters },
            { label: "ROE Min (%)",   key: "roe_min" as keyof Filters },
            { label: "EV/EBITDA Max", key: "ev_ebitda_max" as keyof Filters },
            { label: "D/E Max",       key: "debt_equity_max" as keyof Filters },
          ].map(({ label, key }) => (
            <div key={key} className="space-y-1">
              <Label className="text-xs text-muted-foreground">{label}</Label>
              <Input
                type="number"
                step="0.01"
                value={(filters[key] as number | undefined) ?? ""}
                onChange={f(key)}
                placeholder="—"
                data-testid={`filter-${key}`}
                className="h-8 text-xs"
              />
            </div>
          ))}
          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground">Sector</Label>
            <Input
              type="text"
              value={(filters.sector as string | undefined) ?? ""}
              onChange={fStr("sector")}
              placeholder="Technology…"
              data-testid="filter-sector"
              className="h-8 text-xs"
            />
          </div>
        </div>
        <div className="flex gap-2 mt-4">
          <Button size="sm" onClick={apply} data-testid="btn-apply-filters" className="gap-1.5 text-xs h-8">
            <Search className="w-3.5 h-3.5" /> Apply
          </Button>
          <Button size="sm" variant="ghost" onClick={reset} data-testid="btn-reset-filters" className="text-xs h-8">
            Reset
          </Button>
        </div>
      </div>

      {/* Results */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <p className="text-xs text-muted-foreground">
            {isLoading ? "Loading…" : `${total.toLocaleString()} companies found`}
          </p>
        </div>
        <div className="bg-card border border-border rounded-lg overflow-hidden">
          {isLoading ? (
            <div className="p-4 space-y-2">
              {[0,1,2,3,4].map(i => <Skeleton key={i} className="h-8 w-full" />)}
            </div>
          ) : items.length === 0 ? (
            <div className="py-16 text-center text-muted-foreground">
              <p className="text-sm">No companies match the current filters</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border bg-muted/40">
                    {["Ticker", "P/E", "P/B", "P/S", "EV/EBITDA", "ROE", "ROA", "Net Margin", "D/E", "Div. Yield", ""].map(h => (
                      <th key={h} className="px-3 py-2.5 text-left text-muted-foreground font-medium whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr
                      key={item.ticker}
                      data-testid={`screener-row-${item.ticker}`}
                      className="border-b border-border last:border-0 hover:bg-muted/30 transition-colors cursor-pointer"
                      onClick={() => navigate(`/chart/${item.ticker}`)}
                    >
                      <td className="px-3 py-2.5 font-mono font-semibold text-foreground">{item.ticker}</td>
                      <MetricCell value={item.pe} />
                      <MetricCell value={item.pb} />
                      <MetricCell value={item.ps} />
                      <MetricCell value={item.ev_ebitda} />
                      <MetricCell value={item.roe != null ? item.roe * 100 : null} suffix="%" />
                      <MetricCell value={item.roa != null ? item.roa * 100 : null} suffix="%" />
                      <MetricCell value={item.net_margin != null ? item.net_margin * 100 : null} suffix="%" />
                      <MetricCell value={item.debt_equity} />
                      <MetricCell value={item.dividend_yield != null ? item.dividend_yield * 100 : null} suffix="%" />
                      <td className="px-3 py-2.5 text-right">
                        <ChevronRight className="w-3.5 h-3.5 text-muted-foreground inline" />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Pagination */}
        {pageCount > 1 && (
          <div className="flex items-center justify-between mt-3">
            <p className="text-xs text-muted-foreground">Page {page + 1} of {pageCount}</p>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" disabled={page === 0 || isFetching} onClick={() => setPage(p => p - 1)} className="h-7 text-xs">Prev</Button>
              <Button size="sm" variant="outline" disabled={page >= pageCount - 1 || isFetching} onClick={() => setPage(p => p + 1)} className="h-7 text-xs">Next</Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
