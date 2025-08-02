import { useParams } from 'react-router-dom';
import ExplainableAI from '../components/Forecasting/ExplainAI';
import ActualvsPred from '../components/Forecasting/PredvsAct';
import { useState } from 'react';

export default function Forecast() {
  const sym=useParams().symbol;
  const [explainAI,setExplainAI]=useState(null);
  return (
    <div style={{ padding: 20 }}>
      <ActualvsPred Symbol={sym} setExplainAI={setExplainAI}/>
      {explainAI ? (
        <ExplainableAI modelExplain={JSON.parse(explainAI)} />
      ) : <></>}
    </div>
  )
}