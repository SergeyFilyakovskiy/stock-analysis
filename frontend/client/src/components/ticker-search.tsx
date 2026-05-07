import { useState, useCallback, useRef } from "react";
import { Search, X } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { marketApi } from "../lib/api";
import type { SecurityResponse } from "@shared/schema";
import { cn } from "@/lib/utils";

interface Props {
  onSelect: (ticker: string, name: string) => void;
  placeholder?: string;
  className?: string;
}

export default function TickerSearch({ onSelect, placeholder = "Search ticker…", className }: Props) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["ticker-search", query],
    queryFn: () => marketApi.searchSecurities(query),
    enabled: query.length >= 1,
    staleTime: 10_000,
  });

  const items = data?.items ?? [];

  const handleSelect = useCallback((item: SecurityResponse) => {
    setQuery("");
    setOpen(false);
    onSelect(item.ticker, item.name);
  }, [onSelect]);

  return (
    <div className={cn("relative", className)}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => { setQuery(e.target.value); setOpen(true); }}
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
          placeholder={placeholder}
          data-testid="input-ticker-search"
          className="w-full pl-9 pr-8 py-2 text-sm bg-muted border border-border rounded-md text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary transition-colors"
        />
        {query && (
          <button
            onClick={() => { setQuery(""); inputRef.current?.focus(); }}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            data-testid="btn-clear-search"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {open && query.length >= 1 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-popover border border-border rounded-md shadow-lg z-50 overflow-hidden">
          {isLoading && (
            <div className="px-4 py-3 text-xs text-muted-foreground">Searching…</div>
          )}
          {!isLoading && items.length === 0 && (
            <div className="px-4 py-3 text-xs text-muted-foreground">No results for "{query}"</div>
          )}
          {items.slice(0, 8).map((item) => (
            <button
              key={item.ticker}
              onMouseDown={() => handleSelect(item)}
              data-testid={`search-result-${item.ticker}`}
              className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-muted text-left transition-colors"
            >
              <span className="font-mono text-sm font-medium text-foreground w-16 shrink-0">{item.ticker}</span>
              <span className="text-xs text-muted-foreground truncate">{item.name}</span>
              {item.exchange && (
                <span className="ml-auto text-xs text-muted-foreground/60 shrink-0">{item.exchange}</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
