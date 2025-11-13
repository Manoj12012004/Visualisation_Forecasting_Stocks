import React, { useEffect, useState } from 'react';
import axios from 'axios';

function CorrelationPanel({ symbol }) {
  const [correlations, setCorrelations] = useState([]);

  useEffect(() => {
    axios.get(`/api/v1/stocks/${symbol}/correlations`)
      .then(res => setCorrelations(res.data.correlations))
      .catch(() => setCorrelations([]));
  }, [symbol]);

  if (!correlations.length) return null;

  return (
    <div style={{marginBottom: 18}}>
      <h4>Peer Correlations</h4>
      <table>
        <thead><tr><th>Peer</th><th>Correlation</th></tr></thead>
        <tbody>
          {correlations.map(c => (
            <tr key={c.peer}>
              <td>{c.peer}</td>
              <td>{c.value.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default CorrelationPanel;
