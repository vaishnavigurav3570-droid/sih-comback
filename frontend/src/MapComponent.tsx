import { useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
import * as maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

interface MapComponentProps {
  nowcastData?: any;
  radarData?: any;
  activeLayer?: string;
  mode?: 'nowcast' | 'radar';
}

export interface MapRef {
  flyToIndia: () => void;
  flyToMumbai: () => void;
}

const MapComponent = forwardRef<MapRef, MapComponentProps>(({ nowcastData, radarData, activeLayer, mode }, ref) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);

  useImperativeHandle(ref, () => ({
    flyToIndia: () => {
      map.current?.flyTo({ center: [82.0, 22.0], zoom: 4.5, duration: 2000, pitch: 0 });
    },
    flyToMumbai: () => {
      map.current?.flyTo({ center: [72.8, 18.9], zoom: 6, duration: 2000, pitch: 30 });
    }
  }));

  useEffect(() => {
    if (map.current || !mapContainer.current) return;

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      center: [82.0, 22.0],
      zoom: 4.5,
      pitch: 0,
      interactive: true
    });

    map.current.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');

    map.current.on('load', () => {
      // Sources
      map.current?.addSource('nowcast-grid', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
      map.current?.addSource('radar-points', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });

      // Layers
      map.current?.addLayer({
        id: 'nowcast-layer',
        type: 'fill',
        source: 'nowcast-grid',
        paint: {
          'fill-color': ['get', 'color'],
          'fill-opacity': 0.7,
          'fill-outline-color': 'transparent'
        }
      });

      map.current?.addLayer({
        id: 'radar-layer',
        type: 'circle',
        source: 'radar-points',
        paint: {
          'circle-color': ['get', 'color'],
          'circle-radius': 3,
          'circle-opacity': 0.8
        }
      });
    });
  }, []);

  // Update Nowcast
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded() || mode !== 'nowcast') return;
    const source = map.current.getSource('nowcast-grid') as maplibregl.GeoJSONSource;
    if (!source) return;

    if (!nowcastData || !activeLayer || !nowcastData.variables || !nowcastData.variables[activeLayer]) {
      source.setData({ type: 'FeatureCollection', features: [] });
      return;
    }

    const grid = nowcastData.variables[activeLayer];
    const bounds = nowcastData.bounds; // [[minLat, minLon], [maxLat, maxLon]]
    const features: any[] = [];

    const rows = grid.length;
    const cols = grid[0].length;
    const latStep = (bounds[1][0] - bounds[0][0]) / rows;
    const lonStep = (bounds[1][1] - bounds[0][1]) / cols;

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const val = grid[r][c];
        if (val !== null) {
          const lat = bounds[0][0] + r * latStep;
          const lon = bounds[0][1] + c * lonStep;
          
          let color = 'rgba(0,0,0,0)';
          if (activeLayer === 'storm_development_indicator' || activeLayer === 'extrapolated_indicator') {
            color = val > 0.7 ? '#ef4444' : val > 0.4 ? '#f59e0b' : '#3b82f6';
          } else if (activeLayer === 'ctp_component') {
            color = val > 0.7 ? '#c084fc' : val > 0.4 ? '#60a5fa' : '#94a3b8';
          } else {
             color = val > 0.5 ? '#10b981' : '#f43f5e';
          }

          features.push({
            type: 'Feature',
            properties: { value: val, color },
            geometry: {
              type: 'Polygon',
              coordinates: [[
                [lon, lat], [lon + lonStep, lat], [lon + lonStep, lat + latStep], [lon, lat + latStep], [lon, lat]
              ]]
            }
          });
        }
      }
    }
    source.setData({ type: 'FeatureCollection', features });
    
    // hide radar
    const rs = map.current.getSource('radar-points') as maplibregl.GeoJSONSource;
    if (rs) rs.setData({ type: 'FeatureCollection', features: [] });
  }, [nowcastData, activeLayer, mode]);

  // Update Radar
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded() || mode !== 'radar') return;
    const source = map.current.getSource('radar-points') as maplibregl.GeoJSONSource;
    if (!source) return;

    if (!radarData || !radarData.variables || !radarData.variables[activeLayer] || activeLayer === 'storm_development_indicator') {
      source.setData({ type: 'FeatureCollection', features: [] });
      return;
    }

    const latArr = radarData.latitude;
    const lonArr = radarData.longitude;
    const refArr = radarData.variables[activeLayer];
    const targetArr = radarData.variables['TARGET'];
    
    const features: any[] = [];
    const rows = latArr.length;
    const cols = latArr[0].length;

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const lat = latArr[r][c];
        const lon = lonArr[r][c];
        const val = refArr[r][c];
        const isTarget = targetArr ? targetArr[r][c] : 0;
        
        if (lat !== null && lon !== null && val !== null) {
          let color = val > 35 ? '#ef4444' : val > 20 ? '#f59e0b' : '#3b82f6';
          if (activeLayer === 'VEL') color = val > 5 ? '#ef4444' : val < -5 ? '#3b82f6' : '#94a3b8';
          if (activeLayer === 'WIDTH') color = val > 4 ? '#ef4444' : val > 2 ? '#f59e0b' : '#3b82f6';
          if (isTarget === 1) color = '#ef4444'; // Overwrite with target color
          
          features.push({
            type: 'Feature',
            properties: { value: val, color },
            geometry: { type: 'Point', coordinates: [lon, lat] }
          });
        }
      }
    }
    source.setData({ type: 'FeatureCollection', features });

    // hide nowcast
    const ns = map.current.getSource('nowcast-grid') as maplibregl.GeoJSONSource;
    if (ns) ns.setData({ type: 'FeatureCollection', features: [] });
  }, [radarData, mode]);

  return (
    <div className="absolute inset-0 z-0 bg-slate-950">
      <div ref={mapContainer} className="w-full h-full" />
    </div>
  );
});

export default MapComponent;
