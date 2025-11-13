import React, { useEffect, useState } from "react";
import { getMetrics } from "../api/stockService";
import { Card, CardContent, Typography } from "@mui/material";

export default function MetricsCard({ symbol }) {
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    getMetrics(symbol).then(res => setMetrics(res.data));
  }, [symbol]);

  if (!metrics) return <p>Loading metrics...</p>;

  return (
    <Card sx={{ m: 2, p: 2 }}>
      <CardContent>
        <Typography variant="h6">{symbol} Model Metrics</Typography>
        <Typography>RMSE: {metrics.RMSE}</Typography>
        <Typography>R²: {metrics.R2}</Typography>
        <Typography>MAPE: {metrics.MAPE}%</Typography>
        <Typography>Directional Accuracy: {metrics.Directional_Accuracy}%</Typography>
      </CardContent>
    </Card>
  );
}
