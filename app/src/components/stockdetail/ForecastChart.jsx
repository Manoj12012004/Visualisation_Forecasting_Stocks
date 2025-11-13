import React from 'react';
import { Line } from 'react-chartjs-2';

export default function ForecastChart({ data }) {
  const chartData = {
    labels: data.dates,
    datasets: [
      {
        label: 'Forecasted Price',
        data: data.values,
        borderColor: 'rgba(75,192,192,1)',
        fill: false,
      },
    ],
  };

  return <Line data={chartData} />;
}