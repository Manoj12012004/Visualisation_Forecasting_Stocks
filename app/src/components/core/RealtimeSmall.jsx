import { useState } from 'react';
import axios from 'axios';

export default function RealtimeSmall({ symbol, onPrediction }) {
  // existing state...
  const [prediction, setPrediction] = useState(null);
  const [loadingPred, setLoadingPred] = useState(false);

  async function runPrediction() {
    if (!symbol) return;
    setLoadingPred(true);
    const base = process.env.NEXT_PUBLIC_API_BASE || process.env.REACT_APP_API_BASE || 'http://localhost:8000';
    try {
      // Prefer /realtime/predict (POST) then fallback to /predictions/request-prediction
      let data;
      try {
        const res = await axios.post(`${base}/realtime/predict`, null, { params: { symbol } });
        data = res.data;
      } catch (e) {
        const res2 = await axios.post(`${base}/predictions/request-prediction`, null, { params: { symbol } });
        data = res2.data;
      }
      // Normalize differing field names
      const normalized = {
        prediction_id: data.prediction_id,
        predicted_direction: data.direction != null ? data.direction : data.predicted_direction,
        confidence: data.probability != null ? data.probability : data.confidence,
        predicted_next_price: data.predicted_next_price,
        prediction_time: data.timestamp || data.prediction_time,
        symbol: data.symbol
      };
      setPrediction(normalized);
      if (onPrediction) onPrediction(normalized);
    } catch (err) {
      console.error('Prediction failed', err);
      alert(err?.response?.data?.detail || err.message);
    } finally {
      setLoadingPred(false);
    }
  }

  // render: add button near header
  return (
    <div>
      <div className="flex gap-2 items-center">
        <button onClick={runPrediction} className="bg-blue-600 text-white px-3 py-1 rounded" disabled={loadingPred}>
          {loadingPred ? 'Running...' : 'Run Prediction'}
        </button>
        {prediction && (
          <div className="ml-4 p-2 bg-white rounded shadow text-xs">
            <div><strong>#{prediction.prediction_id}</strong> {prediction.symbol}</div>
            <div>Signal: {prediction.predicted_direction===1 ? 'BUY' : 'SELL'}</div>
            {prediction.confidence != null && (
              <div>Confidence: {(prediction.confidence*100).toFixed(1)}%</div>
            )}
            {prediction.predicted_next_price != null && (
              <div>Next: ₹{prediction.predicted_next_price.toFixed(2)}</div>
            )}
            <div>{new Date(prediction.prediction_time).toLocaleTimeString()}</div>
          </div>
        )}
      </div>
      {/* existing chart which draws live price; overlay prediction if present */}
    </div>
  )
}
