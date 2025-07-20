import asyncio
import json
import websockets
import pandas as pd
from collections import deque
from your_model_module import predict_with_model, train_model, load_model
from your_similarity_module import find_similar_sequence

# Keep last N prices

# Replace with your actual Twelve Data API key
API_KEY = '6a7c4a11380c48c0a644dd1cd06f2702'
SYMBOL = 'AAPL'
PRICE_WINDOW_SIZE = 30

price_window = deque(maxlen=PRICE_WINDOW_SIZE)
stored_sequences = {}  # in real app: load from DB

last_timestamp = None  # To filter out duplicate messages

async def handle_message(message):
    global last_timestamp

    data = json.loads(message)

    # Ignore non-price events
    if data.get('event') != 'price':
        return

    price = float(data['price'])
    timestamp = data['timestamp']

    # Filter duplicates
    if timestamp == last_timestamp:
        return

    last_timestamp = timestamp
    price_window.append(price)
    print(f"[🟢 New Price] {price} at {timestamp}")

    # Once we have enough data points
    if len(price_window) == PRICE_WINDOW_SIZE:
        sequence = list(price_window)

        matched_model_id = find_similar_sequence(sequence, stored_sequences)
        if matched_model_id:
            model = load_model(matched_model_id)
            print(f"[🔁 Using existing model: {matched_model_id}]")
        else:
            model = train_model(sequence)
            stored_sequences['model_' + str(timestamp)] = sequence
            print("[🧠 Trained new model]")

        prediction = predict_with_model(model, sequence)
        print(f"[🔮 Prediction] Next price: {prediction:.4f}")

async def connect():
    uri = "wss://ws.twelvedata.com/v1/quotes/price?apikey=" + API_KEY
    async with websockets.connect(uri) as ws:
        payload = {
            "action": "subscribe",
            "params": {
                "symbols": SYMBOL,
            }
        }
        await ws.send(json.dumps(payload))

        while True:
            message = await ws.recv()
            await handle_message(message)

if __name__ == "__main__":
    asyncio.run(connect())
