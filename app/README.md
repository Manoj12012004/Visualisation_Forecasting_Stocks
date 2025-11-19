# Simple Stock Prediction UI

Minimal frontend connected to FastAPI backend for realtime and historical model outputs.

## Quick Start

```bash
npm install
npm start
```

Backend should run at `http://localhost:8000` (default). Override with:

```bash
set REACT_APP_API_BASE=http://localhost:8000
```

## Pages

| Page | Purpose | Key Endpoint |
|------|---------|--------------|
| Dashboard | Live stream predictions | `ws:/ws/stream/{symbol}` |
| Predictions | Recent stored predictions | `GET /predictions/recent` |
| Backtest | Simple strategy simulation | `GET /backtest/simple` |
| Learn | Indicator descriptions | `GET /indicators` |

## Core Endpoints

- HTTP predict: `GET /realtime/predict?symbol=AAPL`
- WS stream: `ws://localhost:8000/ws/stream/AAPL`
- Recent predictions: `GET /predictions/recent?symbol=AAPL&limit=50`
- Backtest: `GET /backtest/simple?symbol=AAPL&threshold=0.6&initial=10000`

## Symbol Input

Unified simple auto-complete (no heavy dependencies). Type prefix, click select.

## Simplifications

- Removed advanced registry/metadata layers for now.
- Single symbol picker component.
- Minimal Tailwind classes for layout & cards.
- No training button on dashboard (can re-add later).

## Customize

Edit `src/services/apiClient.js` for new endpoints; cards in `src/components/cards` for UI tweaks.

## Testing

```bash
npm test
```

## License

Internal / educational use only.
