import { useEffect, useRef } from 'react';
import * as maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import type { SimulationState } from './simulationEngine';

interface SimulationMapProps {
  state: SimulationState;
  onCellSelect: (id: string) => void;
  activeLayers: string[];
  radarMode: 'REFLECTIVITY' | 'VELOCITY' | 'SPECTRUM_WIDTH';
  satelliteVisible: boolean;
  nwpVisible: boolean;
  selectedCellId: string | null;
}

export default function SimulationMap({ state, onCellSelect, activeLayers, radarMode, satelliteVisible, nwpVisible, selectedCellId }: SimulationMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);

  useEffect(() => {
    if (map.current) return;
    
    map.current = new maplibregl.Map({
      container: mapContainer.current!,
      style: {
        version: 8,
        sources: {},
        layers: [
          {
            id: 'background',
            type: 'background',
            paint: { 'background-color': '#020617' } // VERY dark slate ocean
          }
        ]
      },
      center: [72.82, 18.96], // Mumbai
      zoom: 8.5,
      interactive: true,
      attributionControl: false, // NO carto watermark
    });

    map.current.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');

    map.current.on('load', () => {
      // Add Sources
      
      map.current!.addSource('india-outline', {
         type: 'geojson',
         data: '/india.geojson'
      });

      // Grid lines
      const gridFeatures: any[] = [];
      for(let i = 60; i <= 90; i+=1) { gridFeatures.push({ type: 'Feature', geometry: { type: 'LineString', coordinates: [[i, 0], [i, 40]] }}); }
      for(let i = 0; i <= 40; i+=1) { gridFeatures.push({ type: 'Feature', geometry: { type: 'LineString', coordinates: [[60, i], [90, i]] }}); }
      
      map.current!.addSource('map-grid', {
         type: 'geojson',
         data: { type: 'FeatureCollection', features: gridFeatures }
      });

      map.current!.addSource('storm-cells', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      });
      map.current!.addSource('threat-zones', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      });
      map.current!.addSource('storm-tracks', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      });
      map.current!.addSource('storm-track-points', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      });
      map.current!.addSource('lightning-strikes', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      });
      map.current!.addSource('satellite-cloud', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      });
      map.current!.addSource('nwp-environment', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      });

      // Add Layers
      map.current!.addLayer({
         id: 'india-fill',
         type: 'fill',
         source: 'india-outline',
         paint: {
            'fill-color': '#0f172a', // slate-900 (land)
         }
      });
      map.current!.addLayer({
         id: 'india-border',
         type: 'line',
         source: 'india-outline',
         paint: {
            'line-color': '#334155', // slate-700
            'line-width': 1.5
         }
      });

      map.current!.addLayer({
         id: 'map-grid-layer',
         type: 'line',
         source: 'map-grid',
         paint: {
            'line-color': '#334155', // slate-700
            'line-width': 1,
            'line-opacity': 0.5
         }
      });

      map.current!.addLayer({
        id: 'nwp-layer',
        type: 'fill',
        source: 'nwp-environment',
        paint: {
          'fill-color': '#8b5cf6',
          'fill-opacity': 0.05
        }
      });

      map.current!.addLayer({
        id: 'satellite-layer',
        type: 'circle',
        source: 'satellite-cloud',
        paint: {
          'circle-radius': ['get', 'radius'],
          'circle-color': '#e2e8f0',
          'circle-opacity': 0.3,
          'circle-blur': 1
        }
      });
      map.current!.addLayer({
        id: 'threat-zones-layer',
        type: 'fill',
        source: 'threat-zones',
        paint: {
          'fill-color': '#ef4444',
          'fill-opacity': 0.15,
          'fill-outline-color': '#ef4444'
        }
      });
      map.current!.addLayer({
        id: 'threat-zones-outline',
        type: 'line',
        source: 'threat-zones',
        paint: {
          'line-color': '#ef4444',
          'line-width': 2,
          'line-dasharray': [2, 2]
        }
      });

      map.current!.addLayer({
        id: 'storm-tracks-layer',
        type: 'line',
        source: 'storm-tracks',
        paint: {
          'line-color': '#fcd34d',
          'line-width': 3,
          'line-dasharray': [2, 2]
        }
      });

      map.current!.addLayer({
        id: 'storm-track-points-layer',
        type: 'circle',
        source: 'storm-track-points',
        paint: {
          'circle-radius': 4,
          'circle-color': '#fcd34d',
          'circle-stroke-width': 1,
          'circle-stroke-color': '#000000'
        }
      });
      
      map.current!.addLayer({
        id: 'storm-track-labels-layer',
        type: 'symbol',
        source: 'storm-track-points',
        layout: {
          'text-field': '+{leadTime} MIN',
          'text-size': 10,
          'text-offset': [0, 1.5],
          'text-font': ['Open Sans Bold', 'Arial Unicode MS Bold']
        },
        paint: {
          'text-color': '#fcd34d',
          'text-halo-color': '#000000',
          'text-halo-width': 2
        }
      });

      map.current!.addLayer({
        id: 'storm-cells-layer',
        type: 'circle',
        source: 'storm-cells',
        paint: {
          'circle-radius': ['get', 'radius'],
          'circle-color': [
             'match',
             ['get', 'intensityCategory'],
             'SEVERE', '#ef4444',
             'HIGH', '#f59e0b',
             'MODERATE', '#3b82f6',
             '#94a3b8'
          ],
          'circle-opacity': 0.7,
          'circle-stroke-width': 2,
          'circle-stroke-color': '#ffffff'
        }
      });

      map.current!.addLayer({
        id: 'lightning-strikes-layer',
        type: 'circle',
        source: 'lightning-strikes',
        paint: {
          'circle-radius': 3,
          'circle-color': '#fbbf24',
          'circle-opacity': 0.8
        }
      });

      // Interactivity
      map.current!.on('click', 'storm-cells-layer', (e) => {
        if (e.features && e.features.length > 0) {
          onCellSelect(e.features[0].properties!.id);
        }
      });
      map.current!.on('mouseenter', 'storm-cells-layer', () => {
        map.current!.getCanvas().style.cursor = 'pointer';
      });
      map.current!.on('mouseleave', 'storm-cells-layer', () => {
        map.current!.getCanvas().style.cursor = '';
      });
    });
  }, [onCellSelect]);

  // Update styles based on toggles
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;

    // Update Radar Mode Colors
    if (radarMode === 'REFLECTIVITY') {
       map.current.setPaintProperty('storm-cells-layer', 'circle-color', [
         'match', ['get', 'intensityCategory'],
         'SEVERE', '#ef4444',
         'HIGH', '#f59e0b',
         'MODERATE', '#3b82f6',
         '#94a3b8'
       ]);
    } else if (radarMode === 'VELOCITY') {
       map.current.setPaintProperty('storm-cells-layer', 'circle-color', [
         'match', ['get', 'intensityCategory'],
         'SEVERE', '#10b981', // Green for toward
         'HIGH', '#ef4444',   // Red for away
         'MODERATE', '#34d399',
         '#94a3b8'
       ]);
    } else if (radarMode === 'SPECTRUM_WIDTH') {
       map.current.setPaintProperty('storm-cells-layer', 'circle-color', [
         'match', ['get', 'intensityCategory'],
         'SEVERE', '#d946ef', // Magenta high turbulence
         'HIGH', '#c084fc',
         'MODERATE', '#a78bfa',
         '#94a3b8'
       ]);
    }

    // Toggle layer visibility
    map.current.setLayoutProperty('storm-cells-layer', 'visibility', activeLayers.includes('CELLS') ? 'visible' : 'none');
    map.current.setLayoutProperty('threat-zones-layer', 'visibility', activeLayers.includes('THREAT_ZONE') ? 'visible' : 'none');
    map.current.setLayoutProperty('threat-zones-outline', 'visibility', activeLayers.includes('THREAT_ZONE') ? 'visible' : 'none');
    map.current.setLayoutProperty('storm-tracks-layer', 'visibility', activeLayers.includes('TRACKS') ? 'visible' : 'none');
    map.current.setLayoutProperty('lightning-strikes-layer', 'visibility', activeLayers.includes('LIGHTNING') ? 'visible' : 'none');
    
    if (map.current.getLayer('satellite-layer')) {
        map.current.setLayoutProperty('satellite-layer', 'visibility', satelliteVisible ? 'visible' : 'none');
    }
    if (map.current.getLayer('nwp-layer')) {
        map.current.setLayoutProperty('nwp-layer', 'visibility', nwpVisible ? 'visible' : 'none');
    }

  }, [activeLayers, radarMode, satelliteVisible, nwpVisible]);

  // Center on selected cell smoothly
  useEffect(() => {
    if (!map.current || !selectedCellId) return;
    const cell = state.cells.find(c => c.id === selectedCellId);
    if (cell) {
      map.current.easeTo({ center: [cell.lon, cell.lat], zoom: 8.5, duration: 2000, essential: true });
    }
  }, [selectedCellId, state.cells]);

  // Update data
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;

    // 1. Cells
    const cellFeatures = state.cells.map(cell => ({
      type: 'Feature' as const,
      properties: {
        id: cell.id,
        intensityCategory: cell.intensity > 85 ? 'SEVERE' : cell.intensity > 60 ? 'HIGH' : 'MODERATE',
        // approximate pixels from km for simplicity
        radius: cell.radiusKm * 1.5 
      },
      geometry: {
        type: 'Point' as const,
        coordinates: [cell.lon, cell.lat]
      }
    }));

    (map.current.getSource('storm-cells') as maplibregl.GeoJSONSource).setData({
      type: 'FeatureCollection',
      features: activeLayers.includes('CELLS') ? cellFeatures : []
    });

    // 2. Threat Zones
    const threatFeatures = state.cells.map(cell => ({
      type: 'Feature' as const,
      properties: { id: cell.id },
      geometry: {
        type: 'Polygon' as const,
        coordinates: [cell.threatZonePolygon]
      }
    }));

    (map.current.getSource('threat-zones') as maplibregl.GeoJSONSource).setData({
      type: 'FeatureCollection',
      features: activeLayers.includes('THREAT_ZONE') ? threatFeatures : []
    });

    // 3. Projected Tracks
    const trackFeatures = state.cells.map(cell => {
      return {
        type: 'Feature' as const,
        properties: { id: cell.id },
        geometry: {
          type: 'LineString' as const,
          coordinates: [[cell.lon, cell.lat], ...cell.projectedTrack.map(pt => [pt.lon, pt.lat])]
        }
      }
    });

    (map.current.getSource('storm-tracks') as maplibregl.GeoJSONSource).setData({
      type: 'FeatureCollection',
      features: activeLayers.includes('TRACKS') ? trackFeatures : []
    });

    // 3b. Projected Track Points & Labels
    const trackPointFeatures: any[] = [];
    if (activeLayers.includes('TRACKS')) {
       state.cells.forEach(cell => {
          cell.projectedTrack.forEach(pt => {
             trackPointFeatures.push({
                type: 'Feature',
                properties: { id: cell.id, leadTime: pt.leadTimeMin },
                geometry: { type: 'Point', coordinates: [pt.lon, pt.lat] }
             });
          });
       });
    }
    
    (map.current.getSource('storm-track-points') as maplibregl.GeoJSONSource).setData({
      type: 'FeatureCollection',
      features: trackPointFeatures
    });

    // 4. Simulated Lightning Scatter
    const lightningFeatures: any[] = [];
    if (activeLayers.includes('LIGHTNING')) {
      state.cells.forEach(cell => {
        for (let i = 0; i < cell.lightningFlashRate; i++) {
           // random scatter around cell center based on radius
           const offsetLon = (Math.random() - 0.5) * (cell.radiusKm / 105);
           const offsetLat = (Math.random() - 0.5) * (cell.radiusKm / 111);
           lightningFeatures.push({
             type: 'Feature',
             properties: {},
             geometry: { type: 'Point', coordinates: [cell.lon + offsetLon, cell.lat + offsetLat] }
           });
        }
      });
    }

    (map.current.getSource('lightning-strikes') as maplibregl.GeoJSONSource).setData({
      type: 'FeatureCollection',
      features: lightningFeatures
    });

    // 5. Satellite Clouds
    const satFeatures: any[] = state.cells.map(cell => ({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [cell.lon, cell.lat] },
      properties: { radius: cell.radiusKm * 3 } // visually larger
    }));
    (map.current.getSource('satellite-cloud') as maplibregl.GeoJSONSource).setData({
      type: 'FeatureCollection',
      features: satFeatures
    });

    // 6. NWP Environment (simulated region covering everything)
    const nwpFeatures: any[] = [{
       type: 'Feature',
       geometry: {
          type: 'Polygon',
          coordinates: [[[70, 16], [76, 16], [76, 22], [70, 22], [70, 16]]]
       },
       properties: {}
    }];
    (map.current.getSource('nwp-environment') as maplibregl.GeoJSONSource).setData({
      type: 'FeatureCollection',
      features: nwpFeatures
    });

  }, [state, activeLayers]);

  return (
    <div className="absolute inset-0 z-0">
      <div ref={mapContainer} className="w-full h-full" />
    </div>
  );
}
