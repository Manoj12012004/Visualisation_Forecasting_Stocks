import React, { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';

const PredictionVsActualChart = ({ data, height = 400 }) => {
  const chartContainerRef = useRef();
  const chartRef = useRef();

  useEffect(() => {
    if (!data || !data.dates || !data.prices) return;

    const { dates, prices, actual_returns, predicted_returns } = data;
    
    // Reconstruct prices
    // Price[t] is the price at time t.
    // Return[t] is the return from t to t+horizon.
    // So Target Price is Price[t] * (1 + Return[t])
    // We will plot the Target Prices (Actual vs Predicted) aligned to the Date of the Target?
    // Or aligned to the Date of the Prediction (t)?
    // Usually aligned to Date t, showing "What we predict for t+horizon".
    // Or aligned to Date t+horizon, showing "What happened at t+horizon".
    // Let's align to Date t for now, as that's the index we have.
    
    const actualSeriesData = [];
    const predSeriesData = [];

    for (let i = 0; i < dates.length; i++) {
      let date = dates[i]; // String or timestamp
      
      // Fix for ISO date strings with time (e.g. 2024-12-06T00:00:00)
      if (typeof date === 'string' && date.includes('T')) {
        date = date.split('T')[0];
      }

      const basePrice = prices[i];
      const actRet = actual_returns[i];
      const predRet = predicted_returns[i];

      // Calculate target prices
      // Note: This assumes simple return. If log return, use exp.
      // The backend uses: df['target_return'] = df['close'].pct_change(horizon).shift(-horizon)
      // So it is simple return.
      
      const actPrice = basePrice * (1 + actRet);
      const predPrice = basePrice * (1 + predRet);

      // Lightweight charts expects date as string 'YYYY-MM-DD' or timestamp
      // If date is full ISO string, we might need to format it.
      // Assuming date is 'YYYY-MM-DD' or similar from backend.
      
      // We use the date 't'. 
      // Ideally we should shift the date by horizon, but we don't have the future dates easily available 
      // without calendar logic. 
      // So we plot "Target Price" at "Prediction Date".
      
      actualSeriesData.push({ time: date, value: actPrice });
      predSeriesData.push({ time: date, value: predPrice });
    }

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: height,
      layout: {
        backgroundColor: '#ffffff',
        textColor: '#333',
      },
      grid: {
        vertLines: { color: '#f0f0f0' },
        horzLines: { color: '#f0f0f0' },
      },
      rightPriceScale: {
        borderColor: '#d1d4dc',
      },
      timeScale: {
        borderColor: '#d1d4dc',
      },
    });

    const actualSeries = chart.addLineSeries({
      color: '#2962FF',
      lineWidth: 2,
      title: 'Actual Target Price',
    });

    const predSeries = chart.addLineSeries({
      color: '#FF6D00',
      lineWidth: 2,
      title: 'Predicted Target Price',
    });

    actualSeries.setData(actualSeriesData);
    predSeries.setData(predSeriesData);

    chart.timeScale().fitContent();

    chartRef.current = chart;

    const handleResize = () => {
      chart.applyOptions({ width: chartContainerRef.current.clientWidth });
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [data, height]);

  return <div ref={chartContainerRef} className="w-full" />;
};

export default PredictionVsActualChart;
