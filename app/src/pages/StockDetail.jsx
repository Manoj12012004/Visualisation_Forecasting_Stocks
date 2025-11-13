import React, { useState } from 'react';
import StockHeader from '../components/stockdetail/StockHeader';
import StockInfoCards from '../components/stockdetail/StockInfoCard';
import IndicatorsPanel from '../components/stockdetail/IndicatorsPanel';
import TechnicalPatterns from '../components/stockdetail/TechnicalPattern';
import CorrelationPanel from '../components/stockdetail/CorrelationPanel';
import { Link, useParams } from 'react-router-dom';
import LivePriceChart from '../components/stockdetail/LivePriceChart';
import StockHeatmap from '../components/stockdetail/StockHeatMap';
import { Button } from '@mui/material';


function StockDetailPage() {
  // const [symbol, setSymbol] = useState("AAPL");
  const symbol=useParams().symbol;

  return (
    <div>
      {symbol && <h1>Stock Detail for: {symbol}</h1>}
      <StockHeader symbol={symbol} />
      <StockInfoCards symbol={symbol} />
      <IndicatorsPanel symbol={symbol} />
      {/* <LivePriceChart symbol={symbol}/> */}
      {/* <TechnicalPatterns symbol={symbol} /> */}
      <CorrelationPanel symbol={symbol} />
      <StockHeatmap symbol={symbol}/>
      <Button><Link to={`/${symbol}/forecast`}>Forecast</Link></Button>
    </div>
  );
}

export default StockDetailPage;
