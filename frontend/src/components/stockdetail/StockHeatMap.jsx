import React, { useState } from 'react';
import Plot from 'react-plotly.js';
import api from '../../services/api';
import { Button, CircularProgress, Typography } from '@mui/material';

export default function StockHeatmap({ symbol }) {
  const [stockData, setStockData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showMap, setShowMap] = useState(false);
  const [error, setError] = useState(null);

  const show = () => {
    setLoading(true);
    api.get(`/stock/${symbol}/heatmap`)
      .then((response) => {
        const data = response.data;
        const cleaned = data.filter(d => d.percent_change !== null && !isNaN(d.percent_change));
        setStockData(cleaned);
        setShowMap(true);
        setError(null);
      })
      .catch((err) => {
        setError('Error loading heatmap data.');
        console.error(err);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const x = stockData.map(item => item.date);
  const y = [symbol];
  const z = [stockData.map(item => item.percent_change)];
  const text = [stockData.map(item =>
    `Date: ${item.date}<br/>Change: ${item.percent_change?.toFixed(2)}%<br/>Close: $${item.close}<br/>Volume: ${item.volume}`
  )];

  return (
    <div style={{ marginTop: '20px' }}>
      <Button variant="contained" onClick={show} disabled={loading}>
        {loading ? <CircularProgress size={20} /> : 'Show Heatmap'}
      </Button>

      {error && <Typography color="error">{error}</Typography>}

      {showMap && stockData.length > 0 && (
        <Plot
          data={[
            {
              z,
              x,
              y,
              type: 'heatmap',
              colorscale: [
                [0, 'red'],
                [0.5, 'white'],
                [1, 'green']
              ],
              zmin: Math.min(...z[0]),
              zmax: Math.max(...z[0]),
              text,
              hovertemplate: '%{text}<extra></extra>',
              colorbar: { title: '% Change' }
            }
          ]}
          layout={{
            title: `${symbol} Daily % Change Heatmap`,
            autosize: true,
            height: 350,
            margin: { t: 50, l: 50, r: 50, b: 50 },
            xaxis: { title: 'Date', automargin: true },
            yaxis: { showticklabels: false }  // optional: remove label for single row
          }}
          config={{
            scrollZoom: true  // ✅ Enable zoom with scroll
          }}
          style={{ width: '100%' }}
          useResizeHandler={true}
        />
      )}
    </div>
  );
}
