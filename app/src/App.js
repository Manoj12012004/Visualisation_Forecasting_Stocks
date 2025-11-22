import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import DashboardPage from './pages/Dashboard';
import BacktestPage from './pages/Backtest';
import StockDetail from './pages/StockDetail';
import Portfolio from './pages/Portfolio';
import ForecastPage from './pages/Forecast';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/stocks/:symbol" element={<StockDetail />} />
        <Route path="/stocks" element={<Navigate to="/stocks/AAPL" replace />} />
        <Route path="/forecast/:symbol" element={<ForecastPage />} />
        <Route path="/forecast" element={<Navigate to="/forecast/AAPL" replace />} />
        <Route path="/portfolio" element={<Portfolio />} />
        <Route path="/backtest" element={<BacktestPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;