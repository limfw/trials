# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
import random

st.set_page_config(page_title="Beat the Market AI", layout="wide")

# ---- CONFIG ----
CANDLE_INTERVAL = 1.0  # seconds
TOTAL_TIME = 60  # seconds
WINDOW = 20  # number of candles to show

# ---- SESSION STATE INIT ----
if "started" not in st.session_state:
    st.session_state.started = False
    st.session_state.history = []  # List of dicts: {open, high, low, close}
    st.session_state.actions = []  # List of player actions
    st.session_state.score = 0
    st.session_state.start_time = 0
    st.session_state.last_action_time = 0

# ---- INITIAL TREND GENERATOR ----
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

# ---- AI TRAP GENERATOR ----
def generate_trap_candle(prev_price, player_pattern):
    direction = random.choice(["up", "down"])
    if "buy" in player_pattern:
        direction = "down"
    elif "sell" in player_pattern:
        direction = "up"
    
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

# ---- CHART PLOTTER ----
def plot_chart(data):
    df = pd.DataFrame(data)
    fig = go.Figure(data=[go.Candlestick(x=list(range(len(df))),
                                         open=df["open"], high=df["high"],
                                         low=df["low"], close=df["close"])] )
    fig.update_layout(xaxis_rangeslider_visible=False, height=500)
    st.plotly_chart(fig, use_container_width=True)

# ---- ACTION HANDLER ----
def handle_action(choice):
    st.session_state.actions.append(choice)
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

# ---- GAME LOOP ----
st.title("Beat the Market AI")

if not st.session_state.started:
    st.write("### Instructions")
    st.markdown("""
    You are a trader in a deceptive AI market. Study the trend and make quick Buy, Hold, or Sell decisions.
    The AI will adapt to your behavior and try to trick you.
    - **Correct move**: +1 point
    - **Wrong move**: –1 point
    - **Hold**: 0 points
    """)
    if st.button("Start Game"):
        st.session_state.history = generate_initial_trend(n=20)
        st.session_state.actions = []
        st.session_state.score = 0
        st.session_state.started = True
        st.session_state.start_time = time.time()
else:
    current_time = time.time()
    elapsed = current_time - st.session_state.start_time

    st.write(f"Time left: {int(TOTAL_TIME - elapsed)}s")
    st.write(f"Score: {st.session_state.score}")

    # Show chart
    plot_chart(st.session_state.history[-WINDOW:])

    # Buttons
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

    # Add new candle every second
    if current_time - st.session_state.last_action_time > CANDLE_INTERVAL:
        last_price = st.session_state.history[-1]["close"]
        pattern = " ".join(st.session_state.actions[-3:])
        new_candle = generate_trap_candle(last_price, pattern)
        st.session_state.history.append(new_candle)
        st.session_state.last_action_time = current_time

    # End Game
    if elapsed >= TOTAL_TIME:
        st.session_state.started = False
        st.success(f"Game Over. Final Score: {st.session_state.score}")
