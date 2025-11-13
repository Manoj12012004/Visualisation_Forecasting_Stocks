import React, { useEffect, useState } from "react";
import { getExplain } from "../api/stockService";
import { Card, CardContent, Typography, List, ListItem } from "@mui/material";

export default function ExplainPanel({ symbol }) {
  const [explain, setExplain] = useState(null);

  useEffect(() => {
    getExplain(symbol).then(res => setExplain(res.data));
  }, [symbol]);

  if (!explain) return <p>Loading explainability...</p>;

  return (
    <Card sx={{ m: 2 }}>
      <CardContent>
        <Typography variant="h6">Top Influential Features</Typography>
        <List>
          {explain.top_influential_features.map((f, i) => (
            <ListItem key={i}>
              {f.feature} – {f.importance.toFixed(4)}
            </ListItem>
          ))}
        </List>
        <Typography variant="body2">{explain.interpretation}</Typography>
      </CardContent>
    </Card>
  );
}
