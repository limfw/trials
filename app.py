import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
import random

st.set_page_config(page_title="Beat the Market AI", layout="wide")

CANDLE_INTERVAL = 1.0
TOTAL_TIME = 90
TOTAL_TRIALS = 60
WINDOW = 20
STARTING_BALANCE = 100

if "started" not in st.session_state:
    st.session_state.started = False
    st.session_state.history = []
    st.session_state.actions = []
    st.session_state.score = STARTING_BALANCE
    st.session_state.start_time = 0
    st.session_state.last_update_time = 0
    st.session_state.trial_count = 0
    st.session_state.transition_table = {}
    st.session_state.game_over = False
    st.session_state.last_action_result = ""

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

def plot_chart(data):
    df = pd.DataFrame(data)
    colors = ['red' if row['close'] >= row['open'] else 'green' for _, row in df.iterrows()]
    fig = go.Figure(data=[go.Candlestick(x=list(range(len(df))),
                                         open=df["open"], high=df["high"],
                                         low=df["low"], close=df["close"])] )
    fig.update_layout(xaxis_rangeslider_visible=False, height=500)
    st.plotly_chart(fig, use_container_width=True)

def update_transition_memory():
    if len(st.session_state.actions) < 2:
        return
    prev, curr = st.session_state.actions[-2], st.session_state.actions[-1]
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

def handle_action(choice):
    if st.session_state.trial_count >= TOTAL_TRIALS:
        return
    st.session_state.actions.append(choice)
    st.session_state.trial_count += 1
    update_transition_memory()
    last_price = st.session_state.history[-1]["close"]
    if st.session_state.trial_count < 30:
        new_candle = generate_candle(last_price, random.choice(["buy", "sell"]))
    else:
        predicted = predict_next_action()
        new_candle = generate_candle(last_price, predicted)
    st.session_state.history.append(new_candle)
    direction = "UP" if new_candle["close"] > new_candle["open"] else "DOWN"
    correct = (direction == "UP" and choice == "Buy") or (direction == "DOWN" and choice == "Sell")
    if choice == "Hold":
        result = "You held. Market moved {}. No change.".format(direction)
    elif correct:
        st.session_state.score += 1
        result = f"Correct move! Market went {direction}. +1"
    else:
        st.session_state.score -= 1
        result = f"Wrong move! Market went {direction}. -1"
    st.session_state.last_action_result = result
    if st.session_state.score <= 0:
        st.session_state.game_over = True

def auto_generate_candle():
    if time.time() - st.session_state.last_update_time >= CANDLE_INTERVAL:
        last_price = st.session_state.history[-1]["close"]
        if st.session_state.trial_count < 30:
            new_candle = generate_candle(last_price, random.choice(["buy", "sell"]))
        else:
            predicted = predict_next_action()
            new_candle = generate_candle(last_price, predicted)
        st.session_state.history.append(new_candle)
        st.session_state.last_update_time = time.time()

st.title("Beat the Market AI")
if not st.session_state.started:
    st.markdown("""
### Instructions
**Beat the Market AI** is a 90-second trading challenge.
- The AI is a **market manipulator**, watching and learning from your actions.
- Your job is to **defeat the AI** by staying unpredictable.
- The AI will attempt to deceive you after 30 moves.

#### Rules:
- **Duration**: 90 seconds
- **Actions**: 60 trials (Buy, Hold, Sell)
- **Wallet**: Start with $100. Gain or lose $1 each move.
- If wallet hits $0 → **Game Over**.
""")
    if st.button("Start Game"):
        st.session_state.history = generate_initial_trend(n=20)
        st.session_state.actions = []
        st.session_state.score = STARTING_BALANCE
        st.session_state.started = True
        st.session_state.start_time = time.time()
        st.session_state.last_update_time = time.time()
        st.session_state.trial_count = 0
        st.session_state.transition_table = {}
        st.session_state.last_action_result = ""
        st.session_state.game_over = False
else:
    now = time.time()
    elapsed = now - st.session_state.start_time
    if not st.session_state.game_over:
        auto_generate_candle()
    st.write(f"Time left: {int(TOTAL_TIME - elapsed)}s")
    st.write(f"Wallet: ${st.session_state.score}  |  Actions: {st.session_state.trial_count}/60")
    plot_chart(st.session_state.history[-WINDOW:])
    if st.session_state.last_action_result:
        st.info(st.session_state.last_action_result)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Buy") and not st.session_state.game_over:
            handle_action("Buy")
    with col2:
        if st.button("Hold") and not st.session_state.game_over:
            handle_action("Hold")
    with col3:
        if st.button("Sell") and not st.session_state.game_over:
            handle_action("Sell")

    if elapsed >= TOTAL_TIME or st.session_state.trial_count >= TOTAL_TRIALS or st.session_state.game_over:
        st.session_state.started = False
        if st.session_state.score <= 0:
            st.error("Game Over. You blasted your wallet!")
        else:
            st.success(f"Game Over. Final Wallet Balance: ${st.session_state.score}")
