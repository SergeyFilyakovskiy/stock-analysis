import { useState, useMemo } from "react";
import { useParams, useLocation, Link } from "wouter";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, BarChart, FileText, RefreshCw } from "lucide-react";
import { marketApi } from "../lib/api";
import CandlestickChart from "../components/candlestick-chart";
import TickerSearch from "../components/ticker-search";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const INTERVALS = [
  { label: "1m",  value: "1m" },
  { label: "5m",  value: "5m" },
  { label: "15m", value: "15m" },
  { label: "1h",  value: "1h" },
  { label: "4h",  value: "4h" },
  { label: "1D",  value: "1d" },
  { label: "1W",  value: "1w" },
];

const RANGE_PRESETS = [
  { label: "1D",  days: 1 },
  { label: "5D",  days: 5 },
  { label: "1M",  days: 30 },
  { label: "3M",  days: 90 },
  { label: "6M",  days: 180 },
  { label: "1Y",  days: 365 },
];

function daysAgo(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString();
}

export default function ChartPage() {
  const { ticker } = useParams<{ ticker: string }>();
  const [, navigate] = useLocation();
  const [interval, setInterval] = useState("1d");
  const [range, setRange] = useState(90);

  // Memoize so date strings don't change on every render and cause re-fetches
  const { from, to } = useMemo(() => ({
    from: daysAgo(range),
    to: new Date().toISOString(),
  }), [range]);

  const { data: security, isLoading: secLoading } = useQuery({
    queryKey: [`/api/v1/market/securities/${ticker}`],
    queryFn: () => marketApi.getSecurity(ticker!),
    enabled: !!ticker,
  });

  const { data: ohlcv, isLoading: chartLoading, isError: chartError, error: chartErr, refetch } = useQuery({
    queryKey: [`/api/v1/market/securities/${ticker}/ohlcv`, from, to, interval],
    queryFn: () => marketApi.getOHLCV(ticker!, from, to, interval),
    enabled: !!ticker,
    staleTime: 30_000,
  });

  const { data: priceData } = useQuery({
    queryKey: [`/api/v1/market/securities/${ticker}/price`],
    queryFn: () => marketApi.getLastPrice(ticker!),
    enabled: !!ticker,
    refetchInterval: 15_000,
  });

  const price = priceData?.price ? parseFloat(priceData.price) : null;
  const bars  = ohlcv?.bars ?? [];

  // Compute simple change from first to last bar
  const priceChange = bars.length >= 2
    ? Number(bars[bars.length - 1].close) - Number(bars[0].close)
    : null;
  const pricePct = priceChange && bars.length >= 2
    ? (priceChange / Number(bars[0].close)) * 100
    : null;

  return (
    <div className="p-5 space-y-4 max-w-6xl mx-auto">
      {/* Top bar */}
      <div className="flex items-center gap-3 flex-wrap">
        <button
          onClick={() => navigate("/")}
          className="text-muted-foreground hover:text-foreground transition-colors"
          data-testid="btn-back"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>

        <div className="flex-1 min-w-0">
          {secLoading ? (
            <Skeleton className="h-5 w-32" />
          ) : (
            <div className="flex items-baseline gap-2">
              <h1 className="text-base font-semibold text-foreground font-mono">{ticker}</h1>
              {security?.name && (
                <span className="text-xs text-muted-foreground truncate">{security.name}</span>
              )}
            </div>
          )}
        </div>

        <TickerSearch
          className="w-44"
          placeholder="Switch ticker…"
          onSelect={(t) => navigate(`/chart/${t}`)}
        />
      </div>

      {/* Price header */}
      <div className="flex items-end gap-3 flex-wrap">
        {price ? (
          <>
            <span className="text-2xl font-semibold font-mono tabular text-foreground">
              ${price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
            {pricePct !== null && (
              <span className={cn("text-sm font-medium tabular", priceChange! >= 0 ? "text-success" : "text-destructive")}>
                {priceChange! >= 0 ? "+" : ""}{priceChange!.toFixed(2)} ({pricePct!.toFixed(2)}%)
              </span>
            )}
          </>
        ) : (
          <Skeleton className="h-8 w-40" />
        )}

        <div className="ml-auto flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => refetch()}
            data-testid="btn-refresh"
            className="h-8 w-8"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </Button>
          <Link href={`/fundamentals/${ticker}`}>
            <Button variant="outline" size="sm" className="gap-1.5 text-xs h-8" data-testid="btn-fundamentals">
              <FileText className="w-3.5 h-3.5" /> Fundamentals
            </Button>
          </Link>
        </div>
      </div>

      {/* Chart card */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        {/* Interval + Range selectors */}
        <div className="flex items-center justify-between px-4 py-2 border-b border-border gap-4 flex-wrap">
          <div className="flex gap-0.5">
            {INTERVALS.map(({ label, value }) => (
              <button
                key={value}
                onClick={() => setInterval(value)}
                data-testid={`interval-${value}`}
                className={cn(
                  "px-2.5 py-1 text-xs rounded transition-colors font-mono",
                  interval === value
                    ? "bg-primary/15 text-primary font-medium"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted",
                )}
              >
                {label}
              </button>
            ))}
          </div>

          <div className="flex gap-0.5">
            {RANGE_PRESETS.map(({ label, days }) => (
              <button
                key={label}
                onClick={() => setRange(days)}
                data-testid={`range-${label}`}
                className={cn(
                  "px-2.5 py-1 text-xs rounded transition-colors",
                  range === days
                    ? "bg-primary/15 text-primary font-medium"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted",
                )}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Chart */}
        <div className="p-2">
          {chartLoading ? (
            <div className="flex items-center justify-center" style={{ height: 420 }}>
              <div className="w-8 h-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
            </div>
          ) : chartError ? (
            <div className="flex flex-col items-center justify-center gap-2 text-destructive" style={{ height: 420 }}>
              <p className="text-sm">Error loading chart data</p>
              <p className="text-xs text-muted-foreground">{String((chartErr as Error)?.message || chartErr)}</p>
            </div>
          ) : bars.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-2 text-muted-foreground" style={{ height: 420 }}>
              <BarChart className="w-10 h-10 opacity-30" />
              <p className="text-sm">No data available for this range</p>
            </div>
          ) : (
            <CandlestickChart bars={bars} ticker={ticker!} interval={interval} height={420} />
          )}
        </div>
      </div>

      {/* Info row */}
      {security && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {[
            { label: "Exchange", value: security.exchange ?? "—" },
            { label: "Sector",   value: security.sector   ?? "—" },
            { label: "Status",   value: security.is_active ? "Active" : "Inactive" },
            { label: "Bars",     value: bars.length.toString() },
          ].map(({ label, value }) => (
            <div key={label} className="bg-card border border-border rounded-md px-3 py-2.5">
              <p className="text-xs text-muted-foreground">{label}</p>
              <p className="text-sm font-medium text-foreground mt-0.5 truncate">{value}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
