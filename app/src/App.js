// App.js
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Forecast from './pages/Forecast';
import DashboardPage from './pages/Dashboard';
import StockDetailPage from './pages/StockDetail';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/:symbol" element={<StockDetailPage />} />
        <Route path="/:symbol/forecast" element={<Forecast />} />
      </Routes>
    </Router>
  );
}

export default App;