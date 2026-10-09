import { useEffect, useRef } from "react";
import * as echarts from "echarts";

interface ChartProps {
  option: Record<string, unknown> | null;
}

export default function Chart({ option }: ChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    chartRef.current = echarts.init(containerRef.current, "dark");

    const onResize = () => chartRef.current?.resize();
    window.addEventListener("resize", onResize);

    return () => {
      window.removeEventListener("resize", onResize);
      chartRef.current?.dispose();
    };
  }, []);

  useEffect(() => {
    if (!chartRef.current || !option) return;
    chartRef.current.setOption(option, true);
  }, [option]);

  return (
    <div className="h-full rounded-lg bg-[#1e1e2e] p-2">
      {option ? (
        <div ref={containerRef} className="w-full h-full" />
      ) : (
        <div className="flex items-center justify-center h-full text-slate-500 text-sm">
          No chart data
        </div>
      )}
    </div>
  );
}
