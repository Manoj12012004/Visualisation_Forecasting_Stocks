import { useParams } from 'react-router-dom';
import ChartView from '../components/Forecasting/ChartView';
import MetricsCard from '../components/Forecasting/MetricsCard';
import SignalPanel from '../components/Forecasting/SignalPanel';
import ExplainPanel from '../components/Forecasting/ExplainPanel';

export default function Forecast() {
  const sym=useParams().symbol;
  return (
    <div style={{ padding: 20 }}>
      <ChartView symbol={sym} />
      <MetricsCard symbol={sym} />
      <SignalPanel symbol={sym} />
      <ExplainPanel symbol={sym} />
    </div>
  )
}