import { useEffect, useState } from "react";
import { fetchDatasets, type Dataset } from "../api/client";

interface DatasetSelectorProps {
  onSelect: (path: string) => void;
}

export default function DatasetSelector({ onSelect }: DatasetSelectorProps) {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [open, setOpen] = useState(false);
  const [localPath, setLocalPath] = useState("");

  useEffect(() => {
    fetchDatasets().then(setDatasets).catch(() => setDatasets([]));
  }, []);

  function handleLocalSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = localPath.trim();
    if (trimmed) {
      onSelect(trimmed);
      setLocalPath("");
      setOpen(false);
    }
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="px-3 py-1.5 text-sm bg-slate-700 hover:bg-slate-600 rounded transition-colors"
      >
        Datasets {datasets.length > 0 && `(${datasets.length})`}
      </button>
      {open && (
        <div className="absolute top-full right-0 mt-1 w-80 bg-slate-800 border border-slate-600 rounded-lg shadow-xl z-50">
          {/* Local file path input */}
          <form onSubmit={handleLocalSubmit} className="p-3 border-b border-slate-700">
            <label className="block text-xs text-slate-400 mb-1">Load local file</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={localPath}
                onChange={(e) => setLocalPath(e.target.value)}
                placeholder="/path/to/dataset.tif"
                className="flex-1 px-2 py-1 text-sm bg-slate-900 border border-slate-600 rounded text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
              />
              <button
                type="submit"
                className="px-2 py-1 text-sm bg-emerald-600 hover:bg-emerald-500 rounded transition-colors"
              >
                Add
              </button>
            </div>
          </form>

          {/* Server datasets list */}
          <div className="max-h-48 overflow-auto">
            {datasets.length === 0 ? (
              <div className="p-3 text-sm text-slate-400">
                No datasets in <code>data/</code> directory.
              </div>
            ) : (
              datasets.map((ds) => (
                <button
                  key={ds.path}
                  onClick={() => {
                    onSelect(ds.path);
                    setOpen(false);
                  }}
                  className="w-full text-left px-3 py-2 hover:bg-slate-700 transition-colors text-sm border-b border-slate-700 last:border-0"
                >
                  <div className="font-medium text-slate-200">{ds.name}</div>
                  <div className="text-xs text-slate-400">{ds.size_mb} MB</div>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
