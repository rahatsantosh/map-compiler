import { useEffect, useRef } from "react";
import * as maplibregl from "maplibre-gl";

interface MapViewProps {
  wmsUrl: string | null;
}

export default function MapView({ wmsUrl }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: {
        version: 8,
        sources: {
          osm: {
            type: "raster",
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            attribution: "&copy; OpenStreetMap contributors",
          },
        },
        layers: [{ id: "osm", type: "raster", source: "osm" }],
      },
      center: [94.555, 27.573],
      zoom: 10,
    });

    map.addControl(new maplibregl.NavigationControl(), "top-right");
    mapRef.current = map;

    return () => map.remove();
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const sourceId = "wms-source";
    const layerId = "wms-layer";

    function addWms() {
      if (map!.getLayer(layerId)) map!.removeLayer(layerId);
      if (map!.getSource(sourceId)) map!.removeSource(sourceId);

      if (!wmsUrl) return;

      map!.addSource(sourceId, {
        type: "raster",
        tiles: [wmsUrl + "&bbox={bbox-epsg-3857}"],
        tileSize: 256,
      });
      map!.addLayer({ id: layerId, type: "raster", source: sourceId });
    }

    if (map.isStyleLoaded()) {
      addWms();
    } else {
      map.on("load", addWms);
    }
  }, [wmsUrl]);

  return <div ref={containerRef} className="w-full h-full" />;
}
