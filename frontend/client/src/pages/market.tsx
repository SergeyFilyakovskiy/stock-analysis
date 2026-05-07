import { useLocation } from "wouter";
import { useQuery } from "@tanstack/react-query";
import { TrendingUp, TrendingDown, Activity, ChevronRight } from "lucide-react";
import { marketApi } from "../lib/api";
import TickerSearch from "../components/ticker-search";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const WATCHLIST = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "AMZN"];

function PriceTile({ ticker }: { ticker: string }) {
  const [, navigate] = useLocation();
  const { data, isLoading } = useQuery({
    queryKey: [`/api/v1/market/securities/${ticker}/price`],
    queryFn: () => marketApi.getLastPrice(ticker),
    refetchInterval: 15_000,
  });

  const price = data?.price ? parseFloat(data.price) : null;

  return (
    <button
      onClick={() => navigate(`/chart/${ticker}`)}
      data-testid={`tile-${ticker}`}
      className="group flex items-center justify-between bg-card border border-border rounded-lg px-4 py-3 hover:border-primary/50 hover:bg-muted/50 transition-all text-left"
    >
      <div>
        <p className="text-sm font-semibold text-foreground font-mono">{ticker}</p>
      </div>
      <div className="flex items-center gap-1">
        {isLoading ? (
          <Skeleton className="h-4 w-16" />
        ) : price ? (
          <span className="text-sm font-mono tabular text-foreground">
            ${price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        ) : (
          <span className="text-xs text-muted-foreground">—</span>
        )}
        <ChevronRight className="w-3.5 h-3.5 text-muted-foreground group-hover:text-primary transition-colors ml-1" />
      </div>
    </button>
  );
}

function IndexCard({ code }: { code: string }) {
  return (
    <div className="bg-card border border-border rounded-lg px-4 py-3 space-y-1">
      <p className="text-xs text-muted-foreground">{code}</p>
      <div className="flex items-end gap-2">
        <span className="text-sm font-semibold font-mono text-foreground tabular">—</span>
        <span className="text-xs text-muted-foreground pb-px">live data when connected</span>
      </div>
    </div>
  );
}

export default function MarketPage() {
  const [, navigate] = useLocation();

  const { data: indices, isLoading: loadingIndices } = useQuery({
    queryKey: ["/api/v1/market/indices"],
    queryFn: marketApi.getIndices,
    staleTime: 60_000,
  });

  return (
    <div className="p-5 space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold text-foreground">Market Overview</h1>
          <p className="text-xs text-muted-foreground mt-0.5">Real-time prices and analytics</p>
        </div>
        <TickerSearch
          className="w-full sm:w-64"
          placeholder="Search ticker or company…"
          onSelect={(ticker) => navigate(`/chart/${ticker}`)}
        />
      </div>

      {/* Indices */}
      <section>
        <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">Market Indices</h2>
        {loadingIndices ? (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[0,1,2,3].map(i => <Skeleton key={i} className="h-16 rounded-lg" />)}
          </div>
        ) : indices && indices.length > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {indices.map((idx) => (
              <IndexCard key={idx.index_code} code={idx.index_code} />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {["S&P 500", "NASDAQ", "DOW", "VIX"].map((label) => (
              <IndexCard key={label} code={label} />
            ))}
          </div>
        )}
      </section>

      {/* Watchlist */}
      <section>
        <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">Watchlist</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
          {WATCHLIST.map((t) => <PriceTile key={t} ticker={t} />)}
        </div>
      </section>

      {/* Shortcuts */}
      <section>
        <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">Tools</h2>
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => navigate("/screener")}
            data-testid="shortcut-screener"
            className="bg-card border border-border rounded-lg px-4 py-3 text-left hover:border-primary/40 hover:bg-muted/50 transition-all"
          >
            <p className="text-sm font-medium text-foreground">Screener</p>
            <p className="text-xs text-muted-foreground mt-0.5">Filter by P/E, ROE, margins</p>
          </button>
          <button
            onClick={() => navigate("/compare")}
            data-testid="shortcut-compare"
            className="bg-card border border-border rounded-lg px-4 py-3 text-left hover:border-primary/40 hover:bg-muted/50 transition-all"
          >
            <p className="text-sm font-medium text-foreground">Compare</p>
            <p className="text-xs text-muted-foreground mt-0.5">Side-by-side company analysis</p>
          </button>
        </div>
      </section>
    </div>
  );
}
