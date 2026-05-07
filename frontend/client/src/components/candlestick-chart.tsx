import { useEffect, useRef, useCallback } from "react";
import {
  createChart,
  IChartApi,
  ColorType,
  CrosshairMode,
  CandlestickSeries,
  HistogramSeries,
  Time,
} from "lightweight-charts";
import type { PriceBarResponse } from "@shared/schema";

interface Props {
  bars: PriceBarResponse[];
  ticker: string;
  interval: string;
  height?: number;
}

// Convert ISO datetime string to Unix timestamp (seconds) for lightweight-charts
function toTime(dateStr: string): Time {
  return (new Date(dateStr).getTime() / 1000) as Time;
}

export default function CandlestickChart({ bars, ticker, interval, height = 420 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  const createAndFill = useCallback(() => {
    if (!containerRef.current) return;

    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "hsl(210, 18%, 60%)",
        fontSize: 11,
        fontFamily: "'JetBrains Mono', 'ui-monospace', monospace",
      },
      grid: {
        vertLines: { color: "rgba(255,255,255,0.04)" },
        horzLines: { color: "rgba(255,255,255,0.04)" },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          color: "rgba(55, 219, 186, 0.4)",
          width: 1,
          style: 1,
          labelBackgroundColor: "hsl(174,62%,20%)",
        },
        horzLine: {
          color: "rgba(55, 219, 186, 0.4)",
          width: 1,
          style: 1,
          labelBackgroundColor: "hsl(174,62%,20%)",
        },
      },
      rightPriceScale: {
        borderColor: "rgba(255,255,255,0.07)",
        scaleMargins: { top: 0.1, bottom: 0.28 },
      },
      timeScale: {
        borderColor: "rgba(255,255,255,0.07)",
        timeVisible: true,
        secondsVisible: false,
      },
      handleScroll: { mouseWheel: true, pressedMouseMove: true },
      handleScale: { axisPressedMouseMove: true, mouseWheel: true, pinch: true },
    });

    // v5 API: addSeries(CandlestickSeries, options)
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "hsl(142, 71%, 45%)",
      downColor: "hsl(0, 72%, 51%)",
      borderUpColor: "hsl(142, 71%, 45%)",
      borderDownColor: "hsl(0, 72%, 51%)",
      wickUpColor: "hsl(142, 71%, 45%)",
      wickDownColor: "hsl(0, 72%, 51%)",
    });

    // v5 API: addSeries(HistogramSeries, options)
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });

    chart.priceScale("volume").applyOptions({
      scaleMargins: { top: 0.78, bottom: 0 },
    });

    if (bars.length > 0) {
      const candles = bars
        .filter((b) => b.open != null && b.high != null && b.low != null)
        .map((b) => ({
          time: toTime(b.time),
          open: Number(b.open),
          high: Number(b.high),
          low: Number(b.low),
          close: Number(b.close),
        }))
        .sort((a, b) => (a.time as number) - (b.time as number));

      const volumes = bars
        .filter((b) => b.volume != null)
        .map((b) => ({
          time: toTime(b.time),
          value: b.volume!,
          color:
            Number(b.close) >= Number(b.open)
              ? "rgba(34, 197, 94, 0.3)"
              : "rgba(239, 68, 68, 0.3)",
        }))
        .sort((a, b) => (a.time as number) - (b.time as number));

      candleSeries.setData(candles);
      if (volumes.length > 0) volumeSeries.setData(volumes);
      chart.timeScale().fitContent();
    }

    chartRef.current = chart;

    const ro = new ResizeObserver((entries) => {
      const w = entries[0]?.contentRect.width;
      if (w && chartRef.current) chartRef.current.applyOptions({ width: w });
    });
    ro.observe(containerRef.current);

    return () => {
      ro.disconnect();
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [bars, height]);

  useEffect(() => {
    const cleanup = createAndFill();
    return cleanup;
  }, [createAndFill]);

  return (
    <div
      ref={containerRef}
      style={{ height }}
      className="w-full rounded-md overflow-hidden"
      data-testid="candlestick-chart"
    />
  );
}
