import streamlit as st
import time
import random
import pandas as pd
import plotly.graph_objects as go
from model.market_rnn import MarketRNN
from model.market_gan import MarketGAN
from model.market_engine import MarketEngine

st.set_page_config(page_title="Beat the Market AI", layout="wide")

if "start_time" not in st.session_state:
    st.session_state.start_time = None
    st.session_state.history = []
    st.session_state.score = 60
    st.session_state.ohlc = []
    st.session_state.current_price = 100.0
    st.session_state.rnn = MarketRNN()
    st.session_state.gan = MarketGAN()
    st.session_state.engine = MarketEngine()
    st.session_state.last_candle_time = 0

st.title("Beat the Market AI (Candlestick Edition)")

if st.button("Start Game"):
    st.session_state.start_time = time.time()
    st.session_state.history = []
    st.session_state.score = 60
    st.session_state.current_price = 100.0
    st.session_state.ohlc = []
    st.session_state.last_candle_time = time.time()
    # Generate initial candle
    init_candle = st.session_state.engine.generate_candle("trend", st.session_state.current_price)
    st.session_state.current_price = init_candle['close']
    st.session_state.ohlc.append(init_candle)

if st.session_state.start_time:
    elapsed = int(time.time() - st.session_state.start_time)
    remaining = max(0, 60 - elapsed)
    st.write(f"Time Left: {remaining} seconds")

    # Auto-generate new candle every second
    if time.time() - st.session_state.last_candle_time >= 1:
        predicted = st.session_state.rnn.predict_next_move(st.session_state.history)
        signal_type = st.session_state.gan.generate_signal(predicted)
        candle = st.session_state.engine.generate_candle(signal_type, st.session_state.current_price)
        st.session_state.current_price = candle['close']
        st.session_state.ohlc.append(candle)
        st.session_state.last_candle_time = time.time()

    # Display Chart
    if st.session_state.ohlc:
        df = pd.DataFrame(st.session_state.ohlc)
        fig = go.Figure(data=[go.Candlestick(x=df.index,
                        open=df['open'], high=df['high'],
                        low=df['low'], close=df['close'])])
        fig.update_layout(xaxis_rangeslider_visible=False)
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
        last_candle = st.session_state.ohlc[-1]
        price_change = last_candle['close'] - last_candle['open']
        score_delta = st.session_state.engine.calculate_score(action, price_change)
        st.session_state.score += score_delta
        st.session_state.history.append(action)
        st.session_state.rnn.update(action)
        st.write(f"Action: {action}, Price Change: {round(price_change, 2)}, Score: {st.session_state.score}")

    if remaining <= 0:
        st.success("Time's Up!")
        st.write(f"Final Score: {st.session_state.score}")
