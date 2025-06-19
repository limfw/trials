import streamlit as st
import time
import random
import pandas as pd
import plotly.graph_objects as go
from model.market_rnn import MarketRNN
from model.market_gan import MarketGAN
from model.market_engine import MarketEngine

# Initialize session state
if "start_time" not in st.session_state:
    st.session_state.start_time = None
    st.session_state.history = []
    st.session_state.score = 60
    st.session_state.ohlc = []
    st.session_state.current_price = 100.0
    st.session_state.rnn = MarketRNN()
    st.session_state.gan = MarketGAN()
    st.session_state.engine = MarketEngine()

# Start Game
st.title("Beat the Market AI (Candlestick Edition)")

if st.button("Start Game"):
    st.session_state.start_time = time.time()
    st.session_state.history = []
    st.session_state.score = 60
    st.session_state.current_price = 100.0
    st.session_state.ohlc = []

# Timer & Interface
if st.session_state.start_time:
    elapsed = int(time.time() - st.session_state.start_time)
    remaining = max(0, 60 - elapsed)
    st.write(f"Time Left: {remaining} seconds")

    # Display Chart
    if st.session_state.ohlc:
        df = pd.DataFrame(st.session_state.ohlc)
        fig = go.Figure(data=[go.Candlestick(x=df.index,
                        open=df['open'], high=df['high'],
                        low=df['low'], close=df['close'])])
        st.plotly_chart(fig, use_container_width=True)

    # Player Input
    col1, col2, col3 = st.columns(3)
    action = None
    with col1:
        if st.button("Buy"):
            action = "buy"
    with col2:
        if st.button("Hold"):
            action = "hold"
    with col3:
        if st.button("Sell"):
            action = "sell"

    if action and remaining > 0:
        # Predict and Generate
        predicted = st.session_state.rnn.predict_next_move(st.session_state.history)
        signal_type = st.session_state.gan.generate_signal(predicted)

        # Generate OHLC candle
        candle = st.session_state.engine.generate_candle(signal_type, st.session_state.current_price)
        st.session_state.current_price = candle['close']
        st.session_state.ohlc.append(candle)

        # Score
        price_change = candle['close'] - candle['open']
        score_delta = st.session_state.engine.calculate_score(action, price_change)
        st.session_state.score += score_delta

        # Update Memory
        st.session_state.history.append(action)
        st.session_state.rnn.update(action)

        st.write(f"Signal: {signal_type}, Price Change: {round(price_change, 2)}, Score: {st.session_state.score}")

    if remaining <= 0:
        st.success("Time's Up!")
        st.write(f"Final Score: {st.session_state.score}")
