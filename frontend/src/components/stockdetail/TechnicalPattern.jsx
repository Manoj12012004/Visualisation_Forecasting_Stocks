import React, { useEffect, useState } from 'react';
import axios from 'axios';
import api from '../../services/api';

function TechnicalPatterns({ symbol }) {
  const [patterns, setPatterns] = useState([]);

  useEffect(() => {
    api.get(`/stocks/${symbol}/technical`)
      .then(res => setPatterns(res.data))
      .catch(() => setPatterns([]));
  }, [symbol]);

  return (
    <div style={{ margin: "12px 0" }}>
      <h4>Detected Patterns</h4>
      {/* {patterns.length ? (
        <ul>
          {patterns.map((p, i) => (
            <li key={i}>
              {p.type} detected at {p.date}
            </li>
          ))}
        </ul>
      ) : <p>No recent patterns detected.</p>} */}
      {patterns}
    </div>
  );
}

export default TechnicalPatterns;
