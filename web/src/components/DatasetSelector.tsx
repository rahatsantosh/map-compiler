import { useEffect, useRef, useState } from "react";
import { fetchDatasets, uploadDataset, type Dataset } from "../api/client";

interface DatasetSelectorProps {
  onSelect: (path: string) => void;
}

export default function DatasetSelector({ onSelect }: DatasetSelectorProps) {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [open, setOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function refreshDatasets() {
    fetchDatasets().then(setDatasets).catch(() => setDatasets([]));
  }

  useEffect(() => {
    refreshDatasets();
  }, []);

  async function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const result = await uploadDataset(file);
      onSelect(result.path);
      refreshDatasets();
      setOpen(false);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
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
          {/* File picker */}
          <div className="p-3 border-b border-slate-700">
            <input
              ref={fileInputRef}
              type="file"
              accept=".tif,.tiff"
              onChange={handleFileSelect}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="w-full px-3 py-2 text-sm bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-600 rounded transition-colors font-medium"
            >
              {uploading ? "Uploading..." : "Browse files..."}
            </button>
            <p className="mt-1 text-xs text-slate-500">
              Select a .tif file — it will be copied to the data/ directory
            </p>
          </div>

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
