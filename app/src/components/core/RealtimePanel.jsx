import Header from './Header';
import SymbolSearch from './SymbolSearch';
import RealtimeSmall from './RealtimeSmall';
import { useState } from 'react';
import LivePriceChart from '../charts/LivePriceChart';
import PredictionHistoryChart from '../charts/PredictionHistoryChart';
import ConfidenceGauge from '../charts/ConfidenceGauge';
import { trainStock } from '../../services/apiClient';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import ModelMetrics from './ModelMetrics';


export default function RealtimePanel() {
	const [symbol, setSymbol] = useState('AAPL');
	const [latestPrediction, setLatestPrediction] = useState(null);
	const [trainLoading, setTrainLoading] = useState(false);
	const [toast, setToast] = useState({ open: false, severity: 'success', message: '' });

	async function onTrain() {
		if (!symbol || trainLoading) return;
		setTrainLoading(true);
    
		try {
			await trainStock(symbol);
			setToast({ open: true, severity: 'success', message: `Training completed for ${symbol}` });
		} catch (e) {
			setToast({ open: true, severity: 'error', message: `Training failed: ${e?.response?.data?.detail || e.message}` });
		} finally {
			setTrainLoading(false);
		}
	}
return (
<div>
<Header right={
	<div className="flex items-center gap-2">
		<SymbolSearch value={symbol} onSelect={setSymbol} />
		<button onClick={onTrain} disabled={trainLoading || !symbol} className="bg-emerald-600 text-white px-3 py-1 rounded">
			{trainLoading ? 'Training...' : 'Train'}
		</button>
	</div>
 }>
<h2 className="text-2xl font-semibold">Realtime Predictions</h2>
</Header>


<Snackbar open={toast.open} autoHideDuration={4000} onClose={() => setToast({ ...toast, open: false })} anchorOrigin={{ vertical: 'top', horizontal: 'right' }}>
	<Alert onClose={() => setToast({ ...toast, open: false })} severity={toast.severity} sx={{ width: '100%' }}>
		{toast.message}
	</Alert>
</Snackbar>

<div className="grid md:grid-cols-3 gap-4 mt-4">
	<div className="md:col-span-2 flex flex-col gap-4">
		<LivePriceChart symbol={symbol} />
		<PredictionHistoryChart symbol={symbol} />
	</div>
	<div className="flex flex-col gap-4">
		<RealtimeSmall symbol={symbol} onPrediction={setLatestPrediction} />
		<ConfidenceGauge confidence={latestPrediction?.confidence ?? null} />
		<ModelMetrics symbol={symbol} />
	</div>
</div>
</div>
);
}