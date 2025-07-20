import React from 'react';
import Header from '../components/dash/Header';
import StockSelector from '../components/dash/StockSelector';
import GlobalTrendsPanel from '../components/dash/GlobalTrends';
import WatchlistTable from '../components/dash/WatchList';
import LiveTicker from '../components/dash/LiveTicker';
import TopStocks from '../components/dash/TopStocks';


function DashboardPage() {
  return (
    <div>
      <Header />
      <div style={{ display: 'flex', gap: '1rem' }}>
        <StockSelector />
        <LiveTicker />
      </div>
      <TopStocks />
      <GlobalTrendsPanel />
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
        <div style={{ flex: '2' }}>
          {/* <MainChartPanel /> */}
        </div>
        <div style={{ flex: '1' }}>
          <WatchlistTable />
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;
