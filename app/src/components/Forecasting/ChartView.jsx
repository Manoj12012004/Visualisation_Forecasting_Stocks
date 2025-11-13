import React, { useEffect, useState } from "react";
import Plot from "react-plotly.js";
import { getVisualization } from "../api/stockService";

export default function ChartView({ symbol }) {
  const [chartData, setChartData] = useState(null);

  useEffect(() => {
    getVisualization(symbol).then(res => setChartData(JSON.parse(res.data)));
  }, [symbol]);

  if (!chartData) return <p>Loading chart...</p>;

  return (
    <div className="chart-container">
      <Plot
        data={chartData.data}
        layout={chartData.layout}
        style={{ width: "100%", height: "500px" }}
      />
    </div>
  );
}
