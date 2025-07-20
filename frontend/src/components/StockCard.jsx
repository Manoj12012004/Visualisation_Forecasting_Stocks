import { Card, CardContent, Typography, Button } from '@mui/material';
import { Link, useNavigate } from 'react-router-dom';

export default function StockCard({ stock }) {
  const navigate = useNavigate();

  return (
    <Card>
      <CardContent>
        <Typography variant="h6"><Link to={`/stocks/${stock.symbol}`}>{stock.symbol}</Link></Typography>
        <Typography>{stock.name}</Typography>
        <Typography>Price: ${stock.price.toFixed(2)}</Typography>
        <Typography>Change: {stock.change > 0 ? '+' : ''}{stock.change.toFixed(2)}%</Typography>
        <Button onClick={() => navigate(`/${stock.symbol}`)}>View Details</Button>
      </CardContent>
    </Card>
  );
}
