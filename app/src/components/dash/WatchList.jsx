import React from 'react';

const WATCHLIST = [
  { symbol: 'AAPL', price: 175.43, change: '+0.5%' },
  { symbol: 'MSFT', price: 415.15, change: '-1.2%' },
];

function WatchlistTable() {
  return (
    <table>
      <thead>
        <tr>
          <th>Symbol</th>
          <th>Price</th>
          <th>Change</th>
        </tr>
      </thead>
      <tbody>
        {WATCHLIST.map(row => (
          <tr key={row.symbol}>
            <td>{row.symbol}</td>
            <td>{row.price}</td>
            <td>{row.change}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
export default WatchlistTable;
