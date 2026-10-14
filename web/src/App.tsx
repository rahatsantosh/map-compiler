import { useRef, useState } from "react";
import Editor from "./components/Editor";
import MapView from "./components/MapView";
import Console from "./components/Console";
import Chart from "./components/Chart";
import DatasetSelector from "./components/DatasetSelector";
import { runScript, buildWmsUrl } from "./api/client";

const DEFAULT_SCRIPT = `d = get_dataset(layer="path/to/dataset.tif")
nir = B(d, 4)
red = B(d, 3)
ndvi = (nir - red) / (nir + red)
response = setup(ndvi)`;

export default function App() {
  const [script, setScript] = useState(DEFAULT_SCRIPT);
  const [consoleOutput, setConsoleOutput] = useState("");
  const [isError, setIsError] = useState(false);
  const [chartOption, setChartOption] = useState<Record<string, unknown> | null>(null);
  const [wmsUrl, setWmsUrl] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const scriptRef = useRef(script);
  scriptRef.current = script;

  async function handleRun() {
    const src = scriptRef.current;
    const clickHash = String(Date.now());
    setRunning(true);

    const hasTiledOutput = src.includes("response") && src.includes("setup(");
    const hasConsoleOrGraph = src.includes("print") || src.includes("rasterPlot");

    if (hasTiledOutput) {
      setWmsUrl(buildWmsUrl(src, clickHash));
    }

    if (hasConsoleOrGraph) {
      try {
        const result = await runScript(src, clickHash);
        setConsoleOutput(result.console ?? "");
        setIsError(result.error);
        if (result.graph) {
          setChartOption(result.graph as Record<string, unknown>);
        }
      } catch (err) {
        setConsoleOutput(String(err));
        setIsError(true);
      }
    }

    setRunning(false);
  }

  function handleDatasetSelect(path: string) {
    const snippet = `d = get_dataset(layer="${path}")`;
    setScript((prev) => prev + "\n" + snippet);
  }

  return (
    <div className="h-screen flex flex-col bg-slate-900 text-slate-200">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700">
        <h1 className="text-lg font-semibold">Map Compiler</h1>
        <div className="flex items-center gap-3">
          <DatasetSelector onSelect={handleDatasetSelect} />
          <button
            onClick={handleRun}
            disabled={running}
            className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-600 rounded text-sm font-medium transition-colors"
          >
            {running ? "Running..." : "Run (Shift+Enter)"}
          </button>
        </div>
      </header>

      {/* Main layout */}
      <div className="flex-1 flex min-h-0">
        {/* Left panel: map */}
        <div className="flex-1 min-w-0">
          <MapView wmsUrl={wmsUrl} />
        </div>

        {/* Right panel: editor + console + chart */}
        <div className="w-[420px] flex flex-col border-l border-slate-700">
          {/* Editor */}
          <div className="flex-1 min-h-0 flex flex-col">
            <div className="px-3 py-1.5 bg-slate-800 text-xs text-slate-400 font-medium border-b border-slate-700 rounded-t-lg">
              Script
            </div>
            <div className="flex-1 min-h-0">
              <Editor value={script} onChange={setScript} onRun={handleRun} />
            </div>
          </div>

          {/* Console */}
          <div className="h-36 border-t border-slate-700 p-2">
            <Console output={consoleOutput} isError={isError} />
          </div>

          {/* Chart */}
          <div className="h-48 border-t border-slate-700 p-2">
            <Chart option={chartOption} />
          </div>
        </div>
      </div>
    </div>
  );
}
