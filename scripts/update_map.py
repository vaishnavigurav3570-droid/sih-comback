import re

with open('frontend/src/MapComponent.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the circle layer for nowcast with a heatmap layer
layer_setup = """
      map.current?.addLayer({
        id: 'nowcast-layer',
        type: 'heatmap',
        source: 'nowcast-grid',
        paint: {
          'heatmap-weight': ['get', 'value'],
          'heatmap-intensity': 1.0,
          'heatmap-color': [
            'interpolate',
            ['linear'],
            ['heatmap-density'],
            0, 'rgba(0,0,0,0)',
            0.2, 'rgba(59, 130, 246, 0.7)',
            0.5, 'rgba(245, 158, 11, 0.8)',
            0.8, 'rgba(239, 68, 68, 0.9)'
          ],
          'heatmap-radius': [
            'interpolate',
            ['linear'],
            ['zoom'],
            0, 30,
            9, 80
          ],
          'heatmap-opacity': 0.8
        }
      });
"""

text = re.sub(r"map\.current\?\.addLayer\({\s*id:\s*'nowcast-layer'[\s\S]*?}\);", layer_setup.strip(), text)

# Modify the feature generation loop to not apply hard color thresholds, but just pass the value
loop_update = """
          // Filter out very low noise, but pass raw values to the heatmap
          if (val > 0.3) {
            features.push({
              type: 'Feature',
              properties: { value: val },
              geometry: {
                type: 'Point',
                coordinates: [lon + lonStep / 2, lat + latStep / 2]
              }
            });
          }
"""

text = re.sub(r"let color = 'rgba\(0,0,0,0\)';[\s\S]*?}\);[\s\S]*?}", loop_update.strip(), text, count=1)

# Modify useEffect to also update the heatmap color ramp dynamically if CTP is selected
color_update = """
    // Update heatmap color ramp dynamically based on layer
    if (map.current.getLayer('nowcast-layer')) {
      let colorRamp;
      if (activeLayer === 'ctp_component') {
        colorRamp = [
          'interpolate', ['linear'], ['heatmap-density'],
          0, 'rgba(0,0,0,0)',
          0.2, 'rgba(148, 163, 184, 0.7)',
          0.5, 'rgba(96, 165, 250, 0.8)',
          0.8, 'rgba(192, 132, 252, 0.9)'
        ];
      } else {
        colorRamp = [
          'interpolate', ['linear'], ['heatmap-density'],
          0, 'rgba(0,0,0,0)',
          0.2, 'rgba(59, 130, 246, 0.7)',
          0.5, 'rgba(245, 158, 11, 0.8)',
          0.8, 'rgba(239, 68, 68, 0.9)'
        ];
      }
      map.current.setPaintProperty('nowcast-layer', 'heatmap-color', colorRamp);
    }

    const rows = grid.length;
"""

text = text.replace("const rows = grid.length;", color_update.strip())

with open('frontend/src/MapComponent.tsx', 'w', encoding='utf-8') as f:
    f.write(text)

print("MapComponent updated to use heatmap.")
