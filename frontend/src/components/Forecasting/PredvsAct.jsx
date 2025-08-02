import React, { useEffect, useState } from "react";
import {
  Legend, Line, LineChart, ResponsiveContainer, XAxis, YAxis, Tooltip
} from "recharts";
import { Button, Typography, CircularProgress, Card } from "@mui/material";
import api from "../../services/api";
import Plot from 'react-plotly.js';


export default function ActualvsPred({ Symbol, setExplainAI }) {
  const [chartData, setChartData] = useState([]);
  const [trainedData, setTrainedData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  const fetchData = async () => {
    setLoading(true); setErr(null);
    try {
      const res = await api.get(`/stocks/${Symbol}/train_cnn`);
      setTrainedData(res.data.model_data);
      setExplainAI(res.data.model_data.model_explain); // Pass to parent/XAI panel

      // Build chartData with date or index
      const actuals = res.data.model_data.model_actuals || [];
      const preds = res.data.model_data.model_preds || [];
      const dates = res.data.dates || [];
      setChartData(actuals.map((a, i) => ({
        date: dates[i] || (i+1),
        actual: a,
        pred: preds[i]
      })));
    } catch (e) {
      setErr("Fetch failed");
    } finally {
      setLoading(false);
    }
  };


  return (
    <Card style={{ margin: 24, padding: 24, maxWidth: 950 }}>
      <Typography variant="h6">{Symbol} - Actual vs Predicted</Typography>
      <Button variant="contained" color="primary" onClick={fetchData} style={{margin:"12px 0"}}>
        {loading ? <CircularProgress size={20} /> : "Forecast"}
      </Button>
      {trainedData && (
        <div style={{paddingBottom:4, fontWeight:600}}>
          RMSE: {trainedData.rmse?.toFixed(4)} | R²: {trainedData.r2?.toFixed(4)}
        </div>
      )}
      {err && <Typography color="error">{err}</Typography>}
      {!err && (
        <ResponsiveContainer width="100%" height={400}>
          <Plot
            data={[
              {
                x: chartData.map(d => d.date),
                y: chartData.map(d => d.actual),
                type: 'scatter',
                mode: 'lines',
                name: 'Actual',
                line: { color: '#1976d2' }
              },
              {
                x: chartData.map(d => d.date),
                y: chartData.map(d => d.pred),
                type: 'scatter',
                mode: 'lines',
                name: 'Predicted',
                line: { dash: 'dash', color: '#43a047' }
              }
            ]}
            layout={{
              title: `${Symbol} - Actual vs Predicted`,
              height: 400,
              margin: { l: 50, r: 30, b: 50, t: 40 },
              xaxis: { title: 'Time', rangeslider: { visible: true } },
              yaxis: { title: 'Price' },
            }}
            style={{ width: '100%' }}
          />
        </ResponsiveContainer>
      )}
      <Typography variant="body2" style={{marginTop:8, color:'#777'}}>
        {chartData.length ?
          "Blue = actual prices, green dashed = predicted. Hover for details and errors." : "No data yet."}
      </Typography>
      

    </Card>
  );
}
