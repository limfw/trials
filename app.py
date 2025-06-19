import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
import random

st.set_page_config(page_title="Beat the Market AI", layout="wide")

# ---- CONFIG ----
CANDLE_INTERVAL = 1.0  # seconds
TOTAL_TIME = 120       # seconds
TOTAL_TRIALS = 60      # 1 action every 2 seconds
WINDOW = 20            # number of candles to show

# ---- SESSION STATE INIT ----
if "started" not in st.session_state:
    st.session_state.started = False
    st.session_state.history = []         # candle history
    st.session_state.actions = []         # Buy, Hold, Sell
    st.session_state.score = 0
    st.session_state.start_time = 0
    st.session_state.last_action_time = 0
    st.session_state.predicted_move = None
    st.session_state.trial_count = 0
    st.session_state.transition_table = {}  # memory for RNN-style prediction

# ---- INIT CHART ----
def generate_initial_trend(n=20):
    prices = [100]
    for _ in range(n):
        delta = np.random.normal(loc=0.3, scale=1.0)
        prices.append(prices[-1] + delta)
    candles = []
    for i in range(1, len(prices)):
        o = prices[i - 1]
        c = prices[i]
        h = max(o, c) + random.uniform(0.1, 0.5)
        l = min(o, c) - random.uniform(0.1, 0.5)
        candles.append({"open": o, "high": h, "low": l, "close": c})
    return candles

# ---- AI CANDLE GENERATOR ----
def generate_candle(prev_price, predicted_action):
    direction = "up" if predicted_action == "sell" else "down"
    delta = np.random.uniform(0.5, 1.5)
    if direction == "up":
        open_p = prev_price
        close_p = prev_price + delta
    else:
        open_p = prev_price
        close_p = prev_price - delta
    high_p = max(open_p, close_p) + np.random.uniform(0.2, 0.5)
    low_p = min(open_p, close_p) - np.random.uniform(0.2, 0.5)
    return {"open": open_p, "high": high_p, "low": low_p, "close": close_p}

# ---- CHART ----
def plot_chart(data):
    df = pd.DataFrame(data)
    fig = go.Figure(data=[go.Candlestick(x=list(range(len(df))),
                                         open=df["open"], high=df["high"],
                                         low=df["low"], close=df["close"])])
    fig.update_layout(xaxis_rangeslider_visible=False, height=500)
    st.plotly_chart(fig, use_container_width=True)

# ---- TRANSITION MEMORY ----
def update_transition_memory(actions):
    if len(actions) < 2:
        return
    prev, curr = actions[-2], actions[-1]
    if prev not in st.session_state.transition_table:
        st.session_state.transition_table[prev] = {}
    st.session_state.transition_table[prev][curr] = st.session_state.transition_table[prev].get(curr, 0) + 1

def predict_next_action():
    if len(st.session_state.actions) < 1:
        return random.choice(["buy", "sell"])
    last_action = st.session_state.actions[-1].lower()
    if last_action in st.session_state.transition_table:
        next_moves = st.session_state.transition_table[last_action]
        if next_moves:
            return max(next_moves, key=next_moves.get)
    return random.choice(["buy", "sell"])

# ---- SCORE HANDLER ----
def handle_action(choice):
    st.session_state.actions.append(choice)
    st.session_state.trial_count += 1
    update_transition_memory(st.session_state.actions)
    latest = st.session_state.history[-1]
    prev = st.session_state.history[-2]
    correct = (latest["close"] > prev["close"] and choice == "Buy") or \
              (latest["close"] < prev["close"] and choice == "Sell")
    if choice == "Hold":
        pass
    elif correct:
        st.session_state.score += 1
    else:
        st.session_state.score -= 1

# ---- GAME UI ----
st.title("Beat the Market AI")

if not st.session_state.started:
    st.markdown("""
    ### Instructions
    - Game time: 120 seconds
    - You must take **exactly 60 actions** (one every 2 seconds)
    - Study the chart, then **Buy / Hold / Sell**
    - After 30 moves, the AI will try to predict and deceive you!
    """)
    if st.button("Start Game"):
        st.session_state.history = generate_initial_trend(n=20)
        st.session_state.actions = []
        st.session_state.score = 0
        st.session_state.started = True
        st.session_state.start_time = time.time()
        st.session_state.trial_count = 0
        st.session_state.transition_table = {}
        st.session_state.last_action_time = time.time()
else:
    now = time.time()
    elapsed = now - st.session_state.start_time
    st.write(f"Time left: {int(TOTAL_TIME - elapsed)}s")
    st.write(f"Score: {st.session_state.score}  |  Trials: {st.session_state.trial_count}/60")
    plot_chart(st.session_state.history[-WINDOW:])

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Buy"):
            handle_action("Buy")
    with col2:
        if st.button("Hold"):
            handle_action("Hold")
    with col3:
        if st.button("Sell"):
            handle_action("Sell")

    if now - st.session_state.last_action_time >= CANDLE_INTERVAL:
        last_price = st.session_state.history[-1]["close"]
        if st.session_state.trial_count < 30:
            new_candle = generate_candle(last_price, random.choice(["buy", "sell"]))
        else:
            predicted = predict_next_action()
            new_candle = generate_candle(last_price, predicted)
        st.session_state.history.append(new_candle)
        st.session_state.last_action_time = now

    if elapsed >= TOTAL_TIME or st.session_state.trial_count >= TOTAL_TRIALS:
        st.session_state.started = False
        st.success(f"Game Over. Final Score: {st.session_state.score}")
