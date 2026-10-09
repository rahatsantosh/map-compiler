import { useEffect, useState } from "react";
import { fetchDatasets, type Dataset } from "../api/client";

interface DatasetSelectorProps {
  onSelect: (path: string) => void;
}

export default function DatasetSelector({ onSelect }: DatasetSelectorProps) {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    fetchDatasets().then(setDatasets).catch(() => setDatasets([]));
  }, []);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="px-3 py-1.5 text-sm bg-slate-700 hover:bg-slate-600 rounded transition-colors"
      >
        Datasets {datasets.length > 0 && `(${datasets.length})`}
      </button>
      {open && (
        <div className="absolute top-full left-0 mt-1 w-72 bg-slate-800 border border-slate-600 rounded-lg shadow-xl z-50 max-h-64 overflow-auto">
          {datasets.length === 0 ? (
            <div className="p-3 text-sm text-slate-400">
              No datasets found. Place .tif files in the <code>data/</code> directory.
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
      )}
    </div>
  );
}
