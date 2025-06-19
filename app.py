import streamlit as st
import time
import random
import numpy as np
from model.market_rnn import MarketRNN
from model.market_gan import MarketGAN
from model.market_engine import MarketEngine

if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'history' not in st.session_state:
    st.session_state.history = []
if 'profit' not in st.session_state:
    st.session_state.profit = 0
if 'price' not in st.session_state:
    st.session_state.price = 100.0
if 'rnn' not in st.session_state:
    st.session_state.rnn = MarketRNN()
if 'gan' not in st.session_state:
    st.session_state.gan = MarketGAN()
if 'engine' not in st.session_state:
    st.session_state.engine = MarketEngine()

st.title("Beat the Market AI")
st.write("Make Buy / Hold / Sell decisions in 60 seconds and try to profit. The market learns you.")

if st.button("Start Game"):
    st.session_state.start_time = time.time()
    st.session_state.history = []
    st.session_state.profit = 0
    st.session_state.price = 100.0

if st.session_state.start_time:
    elapsed = int(time.time() - st.session_state.start_time)
    remaining = max(0, 60 - elapsed)
    st.write(f"Time Left: {remaining}s")
    
    if remaining > 0 and len(st.session_state.history) < 60:
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Buy"):
                action = "buy"
        with col2:
            if st.button("Hold"):
                action = "hold"
        with col3:
            if st.button("Sell"):
                action = "sell"

        if 'action' in locals():
            rnn = st.session_state.rnn
            gan = st.session_state.gan
            engine = st.session_state.engine
            price = st.session_state.price

            signal = gan.generate_signal()
            pred = rnn.predict_next_move(st.session_state.history)
            price_change = engine.get_price_change(signal, pred, action)
            st.session_state.price += price_change
            st.session_state.profit += engine.get_profit(action, price_change)
            st.session_state.history.append(action)
            rnn.update(action)

            st.write(f"Market Signal: {signal}")
