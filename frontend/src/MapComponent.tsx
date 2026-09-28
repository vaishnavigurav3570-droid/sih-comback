import { useEffect, useRef } from 'react';
import * as maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

interface MapComponentProps {
  gridForecasts: any[]; // We will type this properly later
}

export default function MapComponent({ gridForecasts }: MapComponentProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);

  useEffect(() => {
    if (map.current || !mapContainer.current) return; // initialize map only once

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json', // Premium dark basemap
      center: [78.9629, 20.5937], // Center of India
      zoom: 4,
      pitch: 0, // 3D tilt
    });

    map.current.addControl(new maplibregl.NavigationControl(), 'bottom-right');

    map.current.on('load', () => {
      // Setup sources and layers here in the future
    });
  }, []);

  // Update map when data changes
  useEffect(() => {
    if (!map.current || !gridForecasts.length) return;
    
    // In a future step, we will convert gridForecasts to GeoJSON and update the map source
    
  }, [gridForecasts]);

  return (
    <div className="absolute inset-0 z-0 bg-slate-900">
      <div ref={mapContainer} className="w-full h-full" />
    </div>
  );
}
