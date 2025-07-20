import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';

function LiveTicker({ symbol = "AAPL", intervalMs = 3000 }) {
  const [priceData, setPriceData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const startStream = async () => {
      try {
        await axios.get(`http://localhost:8000/stream/start/${symbol}`);
        console.log(`Streaming for ${symbol} started`);
      } catch (err) {
        console.error("Failed to start streaming:", err);
        setError("Unable to start stream");
      }
    };

    const fetchLatestPrice = async () => {
      try {
        const res = await axios.get(`http://localhost:8000/stream/current/${symbol}`);
        if (!res.data || res.data.error) {
          setError("No latest price found");
        } else {
          setPriceData(res.data);
          setError(null);
        }
      } catch (err) {
        console.error("Error fetching price:", err);
        setError("Error getting price");
      }
    };

    startStream();

    const interval = setInterval(() => {
      fetchLatestPrice();
    }, intervalMs);

    return () => {
      clearInterval(interval);
    };
  }, [symbol, intervalMs]);

  return (
    <div style={styles.container}>
      <h3><Link to={`/${symbol}`}>📈 Live Ticker: {symbol}</Link></h3>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {priceData ? (
        <div>
          <strong>Price: ${priceData.price}</strong> <br />
          <small>{new Date(priceData.timestamp).toLocaleTimeString()}</small>
        </div>
      ) : (
        <p>Loading price...</p>
      )}
    </div>
  );
}

const styles = {
  container: {
    border: "1px solid #ddd",
    padding: "12px",
    borderRadius: "6px",
    backgroundColor: "#e8f5e9",
    marginTop: "10px",
    minWidth: "220px"
  }
};

export default LiveTicker;


// import React, { useEffect, useState } from 'react';

// function LiveTicker({ symbol = "AAPL" }) {
//   const [price, setPrice] = useState(null);

//   useEffect(() => {
//     const ws = new WebSocket("ws://localhost:8000/ws/ticker");
//     ws.onopen = () => {
//       ws.send(JSON.stringify({ action: "subscribe", symbol }));
//     };
//     ws.onmessage = (event) => {
//       const data = JSON.parse(event.data);
//       if (data.symbol === symbol && data.price !== undefined) {
//         setPrice(data.price);
//       }
//     };
//     return () => ws.close();
//   }, [symbol]);

//   return (
//     <div>
//       <strong>{symbol} Real-Time:</strong> {price ? `$${price}` : "Waiting..."}
//     </div>
//   );
// }

// export default LiveTicker;

