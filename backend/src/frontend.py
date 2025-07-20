import streamlit as st
from src.pipeline.train_pipeline import Train

train=Train()

st.set_page_config(
    page_title="Stock forecast App",)

st.title("Stock Forecast App")


ticker=st.text_input("Enter Stock Ticker", "AAPL")
if ticker:
    st.write(f"Fetching data for {ticker}...")
    train.run_training_pipeline(ticker, '2015-01-01', '2025-01-01')
    st.write(f"Training model for {ticker}...")
    
