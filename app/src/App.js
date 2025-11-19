import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import DashboardPage from './pages/Dashboard';
import BacktestPage from './pages/Backtest';
import StockDetail from './pages/StockDetail';
import Portfolio from './pages/Portfolio';
import { LearningProvider } from './context/LearningContext';

function App() {
  return (
    <LearningProvider>
      <Router>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/stocks/:symbol" element={<StockDetail />} />
          <Route path="/stocks" element={<Navigate to="/stocks/AAPL" replace />} />
          <Route path="/portfolio" element={<Portfolio />} />
          <Route path="/backtest" element={<BacktestPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </LearningProvider>
  );
}

export default App;