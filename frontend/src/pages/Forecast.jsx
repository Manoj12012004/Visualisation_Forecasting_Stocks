  import { useParams } from 'react-router-dom';
  import { useEffect, useState } from 'react';
  import api from '../services/api';
  import { Typography, CircularProgress } from '@mui/material';
  import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
  } from 'recharts';

  export default function Forecast() {
    const { symbol } = useParams();
    const [forecast, setForecast] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
      const res=api.get(`/stocks/${symbol}/train`).catch(() => {});
      setLoading(true);
      console.log(res.data);
      setLoading(false);
  // api.get(`/stocks/${symbol}/predict`).then(res => {
  //   setForecast(res.data);
  //   setLoading(false);
  // });
}, [symbol]);

    return (
      <div style={{ padding: 20 }}>
        <Typography variant="h5">{symbol} - Forecast</Typography>
        {loading ? (
          <CircularProgress />
        ) : (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={forecast}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="forecast" stroke="#82ca9d" />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    );
  }
