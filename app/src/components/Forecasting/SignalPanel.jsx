import React, { useEffect, useState } from "react";
import { getSignals } from "../api/stockService";
import { Alert, Typography } from "@mui/material";

export default function SignalPanel({ symbol }) {
  const [signal, setSignal] = useState(null);

  useEffect(() => {
    getSignals(symbol).then(res => setSignal(res.data));
  }, [symbol]);

  if (!signal) return <p>Loading signal...</p>;

  const color = signal.signal === "BUY" ? "success" : signal.signal === "SELL" ? "error" : "info";

  return (
    <Alert severity={color} sx={{ mt: 2 }}>
      <Typography variant="h6">
        {signal.symbol} Signal: {signal.signal}
      </Typography>
      <Typography>Expected Change: {signal.expected_change_percent}%</Typography>
      <Typography>Confidence: {signal.confidence}</Typography>
    </Alert>
  );
}
