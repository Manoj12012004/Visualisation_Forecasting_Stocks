import { useParams, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import api from '../../services/api';
import { Typography, Button, CircularProgress, Box } from '@mui/material';
import LiveChart from '../Livestock'; // updated filename

export default function StockDetails() {
  const { symbol } = useParams();
  const navigate = useNavigate();
  const [livePrice, setLivePrice] = useState(null);
  const [error, setError] = useState(null);

  // Real-time price (in addition to chart)
  useEffect(() => {
    const interval = setInterval(() => {
      api.get(`/stream/current/${symbol}`)
        .then(res => setLivePrice(res.data.price))
        .catch(() => setError("Failed to fetch live price"));
    }, 5000); // optional live price outside chart

    return () => clearInterval(interval);
  }, [symbol]);

  return (
    <Box sx={{ padding: 3 }}>
      <Typography variant="h5" gutterBottom>
        {symbol} - Real-Time Stock Chart
      </Typography>

      {livePrice && (
        <Typography variant="h6" color="green" sx={{ mt: 2 }}>
          Live Price: <b>${parseFloat(livePrice).toFixed(2)}</b>
        </Typography>
      )}

      {error && (
        <Typography color="error" sx={{ mt: 2 }}>
          {error}
        </Typography>
      )}

      <Box sx={{ mt: 4 }}>
        <LiveChart symbol={symbol} />
      </Box>

      <Button
        variant="contained"
        color="primary"
        sx={{ marginTop: 3 }}
        onClick={() => navigate(`/${symbol}/forecast`)}
      >
        View Forecast
      </Button>
      <Button
  variant="outlined"
  color="secondary"
  sx={{ marginRight: 2, marginTop: 3 }}
  onClick={async () => {
    try {
      await api.post(`/stocks/${symbol}/train`);
      alert('Model retrained.');
    } catch {
      alert('Training failed.');
    }
  }}
>
  Retrain Model
</Button>
    </Box>
  );
}
