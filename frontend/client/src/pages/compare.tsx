import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Plus, X, BarChart2 } from "lucide-react";
import { fundamentalApi } from "../lib/api";
import TickerSearch from "../components/ticker-search";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { CompanyReportSchema } from "@shared/schema";
import { cn } from "@/lib/utils";

const METRICS: { label: string; key: keyof CompanyReportSchema["metrics"] & string }[] = [
  { label: "P/E",          key: "pe" },
  { label: "P/B",          key: "pb" },
  { label: "P/S",          key: "ps" },
  { label: "EV/EBITDA",    key: "ev_ebitda" },
  { label: "ROE",          key: "roe" },
  { label: "ROA",          key: "roa" },
  { label: "ROIC",         key: "roic" },
  { label: "Gross Margin", key: "gross_margin" },
  { label: "Net Margin",   key: "net_margin" },
  { label: "EBITDA Margin",key: "ebitda_margin" },
  { label: "Debt/Equity",  key: "debt_equity" },
  { label: "Div. Yield",   key: "dividend_yield" },
];

function fmt(v: number | null | undefined, key: string): string {
  if (v == null) return "—";
  const pct = ["roe","roa","roic","gross_margin","net_margin","ebitda_margin","dividend_yield"].includes(key);
  return pct ? `${(v * 100).toFixed(2)}%` : v.toFixed(2);
}

function highlight(values: (number | null | undefined)[], key: string, idx: number): string {
  const valid = values.filter((v): v is number => v != null);
  if (valid.length < 2) return "";
  const v = values[idx];
  if (v == null) return "";

  // For "lower is better" metrics
  const lowerBetter = ["pe","pb","ps","ev_ebitda","debt_equity"].includes(key);
  const best  = lowerBetter ? Math.min(...valid) : Math.max(...valid);
  const worst = lowerBetter ? Math.max(...valid) : Math.min(...valid);

  if (v === best)  return "text-success font-medium";
  if (v === worst) return "text-destructive";
  return "";
}

export default function ComparePage() {
  const [tickers, setTickers] = useState<string[]>([]);

  const { mutate, data: reports, isPending, error } = useMutation({
    mutationFn: (t: string[]) => fundamentalApi.compare(t),
  });

  const addTicker = (ticker: string) => {
    if (tickers.includes(ticker) || tickers.length >= 5) return;
    const updated = [...tickers, ticker];
    setTickers(updated);
    if (updated.length >= 2) mutate(updated);
  };

  const removeTicker = (ticker: string) => {
    const updated = tickers.filter(t => t !== ticker);
    setTickers(updated);
    if (updated.length >= 2) mutate(updated);
  };

  return (
    <div className="p-5 space-y-5 max-w-6xl mx-auto">
      <div>
        <h1 className="text-lg font-semibold text-foreground">Compare Companies</h1>
        <p className="text-xs text-muted-foreground mt-0.5">Side-by-side fundamental analysis (up to 5 companies)</p>
      </div>

      {/* Ticker picker */}
      <div className="flex items-center gap-3 flex-wrap">
        {tickers.map((t) => (
          <div key={t} className="flex items-center gap-1.5 bg-primary/10 text-primary text-xs font-mono font-medium px-3 py-1.5 rounded-full">
            {t}
            <button onClick={() => removeTicker(t)} data-testid={`remove-ticker-${t}`} className="hover:text-primary/70 transition-colors">
              <X className="w-3 h-3" />
            </button>
          </div>
        ))}

        {tickers.length < 5 && (
          <TickerSearch
            className="w-48"
            placeholder="Add ticker…"
            onSelect={addTicker}
          />
        )}

        {tickers.length > 0 && (
          <Button variant="ghost" size="sm" onClick={() => setTickers([])} className="text-xs h-7 text-muted-foreground">
            Clear all
          </Button>
        )}
      </div>

      {/* Results */}
      {tickers.length < 2 && (
        <div className="py-20 flex flex-col items-center gap-3 text-muted-foreground">
          <BarChart2 className="w-10 h-10 opacity-30" />
          <p className="text-sm">Add at least 2 tickers to compare</p>
        </div>
      )}

      {isPending && (
        <div className="space-y-2">
          <Skeleton className="h-10 w-full" />
          {[0,1,2,3,4].map(i => <Skeleton key={i} className="h-8 w-full" />)}
        </div>
      )}

      {error && (
        <div className="py-8 text-center text-destructive text-sm">
          Failed to load comparison data
        </div>
      )}

      {reports && reports.length >= 2 && (
        <div className="bg-card border border-border rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border bg-muted/40">
                  <th className="px-4 py-3 text-left text-muted-foreground font-medium w-36">Metric</th>
                  {reports.map((r) => (
                    <th key={r.ticker} className="px-4 py-3 text-left text-foreground font-semibold font-mono">{r.ticker}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {/* Company info rows */}
                {reports[0].company && (
                  <>
                    {[
                      { label: "Name",       getValue: (r: CompanyReportSchema) => r.company?.name ?? "—" },
                      { label: "Sector",     getValue: (r: CompanyReportSchema) => r.company?.sector ?? "—" },
                      { label: "Market Cap", getValue: (r: CompanyReportSchema) => r.company?.market_cap ? `$${(Number(r.company.market_cap)/1e9).toFixed(2)}B` : "—" },
                    ].map(({ label, getValue }) => (
                      <tr key={label} className="border-b border-border hover:bg-muted/20 transition-colors">
                        <td className="px-4 py-2.5 text-muted-foreground">{label}</td>
                        {reports.map((r) => (
                          <td key={r.ticker} className="px-4 py-2.5 text-foreground">{getValue(r)}</td>
                        ))}
                      </tr>
                    ))}
                    {/* Divider */}
                    <tr className="border-b border-border bg-muted/20">
                      <td colSpan={reports.length + 1} className="px-4 py-1 text-[10px] text-muted-foreground uppercase tracking-wider font-medium">
                        Fundamental Metrics
                      </td>
                    </tr>
                  </>
                )}

                {METRICS.map(({ label, key }) => {
                  const values = reports.map(r => r.metrics ? (r.metrics[key as keyof typeof r.metrics] as number | null | undefined) : null);
                  return (
                    <tr key={key} className="border-b border-border last:border-0 hover:bg-muted/20 transition-colors">
                      <td className="px-4 py-2.5 text-muted-foreground">{label}</td>
                      {reports.map((r, i) => (
                        <td
                          key={r.ticker}
                          data-testid={`compare-${r.ticker}-${key}`}
                          className={cn("px-4 py-2.5 font-mono tabular", highlight(values, key, i))}
                        >
                          {fmt(values[i], key)}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="px-4 py-2 border-t border-border bg-muted/20">
            <p className="text-[10px] text-muted-foreground">
              <span className="text-success font-medium">Green</span> = best value · <span className="text-destructive">Red</span> = worst value for each metric
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
