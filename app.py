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

if "started" not in st.session_state:
    st.session_state.started = False
    st.session_state.history = []
    st.session_state.actions = []
    st.session_state.score = 100  # Wallet value
    st.session_state.start_time = 0
    st.session_state.last_update_time = 0
    st.session_state.trial_count = 0
    st.session_state.transition_table = {}
    st.session_state.message = ""
    st.session_state.last_action_time = 0
    st.session_state.force_update = False

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

def generate_candle(prev_price, predicted_action, player_action=None):
    # Make the market react strongly to player actions
    if player_action:
        if player_action == "Buy":
            # Market will likely go down after player buys (to make them lose)
            base_delta = np.random.uniform(-1.5, -0.5)
        elif player_action == "Sell":
            # Market will likely go up after player sells
            base_delta = np.random.uniform(0.5, 1.5)
        else:  # Hold
            base_delta = np.random.uniform(-0.5, 0.5)
    else:
        # Normal market movement when no player action
        if predicted_action == "sell":
            base_delta = np.random.uniform(0.5, 1.5)  # Market goes up to punish sellers
        else:
            base_delta = np.random.uniform(-1.5, -0.5)  # Market goes down to punish buyers
    
    open_p = prev_price
    close_p = prev_price + base_delta
    high_p = max(open_p, close_p) + np.random.uniform(0.2, 0.5)
    low_p = min(open_p, close_p) - np.random.uniform(0.2, 0.5)
    return {"open": open_p, "high": high_p, "low": low_p, "close": close_p}

def plot_chart(data):
    df = pd.DataFrame(data)
    fig = go.Figure(data=[go.Candlestick(x=list(range(len(df))),
                         open=df["open"], high=df["high"],
                         low=df["low"], close=df["close"],
                         increasing_line_color='red', decreasing_line_color='green')])
    fig.update_layout(xaxis_rangeslider_visible=False, height=500)
    st.plotly_chart(fig, use_container_width=True)

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

def handle_action(choice):
    if st.session_state.trial_count >= TOTAL_TRIALS:
        return
    
    st.session_state.actions.append(choice)
    st.session_state.trial_count += 1
    update_transition_memory(st.session_state.actions)
    
    # Generate immediate market reaction to player's action
    last_price = st.session_state.history[-1]["close"]
    new_candle = generate_candle(last_price, None, player_action=choice)
    st.session_state.history.append(new_candle)
    
    # Update score based on the immediate reaction
    latest = st.session_state.history[-1]
    prev = st.session_state.history[-2]
    price_change = latest["close"] - prev["close"]
    
    if choice == "Hold":
        st.session_state.message = "You held. No gain/loss."
    elif choice == "Buy":
        if price_change > 0:
            st.session_state.score += abs(price_change)
            st.session_state.message = f"Correct! You bought and market went up (+${abs(price_change):.2f})"
        else:
            st.session_state.score -= abs(price_change)
            st.session_state.message = f"Wrong! You bought but market went down (-${abs(price_change):.2f})"
    elif choice == "Sell":
        if price_change < 0:
            st.session_state.score += abs(price_change)
            st.session_state.message = f"Correct! You sold and market went down (+${abs(price_change):.2f})"
        else:
            st.session_state.score -= abs(price_change)
            st.session_state.message = f"Wrong! You sold but market went up (-${abs(price_change):.2f})"
    
    st.session_state.last_action_time = time.time()
    st.session_state.force_update = True

st.title("Beat the Market AI")
if not st.session_state.started:
    st.markdown("""
### Instructions
You face a manipulative AI market.
- The AI watches your behavior and learns to deceive.
- Make profit by Buy, Hold, or Sell.
- Market candles change **every second** or immediately after your action.
- You must act **60 times within 90 seconds**.
- Wallet starts at $100. Lose it all and you're out!
    """)
    if st.button("Start Game"):
        st.session_state.history = generate_initial_trend()
        st.session_state.actions = []
        st.session_state.score = 100
        st.session_state.started = True
        st.session_state.start_time = time.time()
        st.session_state.last_update_time = time.time()
        st.session_state.trial_count = 0
        st.session_state.transition_table = {}
        st.session_state.message = ""
        st.session_state.last_action_time = 0
        st.session_state.force_update = False
else:
    now = time.time()
    elapsed = now - st.session_state.start_time
    st.write(f"Time Left: {int(TOTAL_TIME - elapsed)}s | Trials: {st.session_state.trial_count}/60 | Wallet: ${st.session_state.score:.2f}")

    plot_chart(st.session_state.history[-WINDOW:])
    if st.session_state.message:
        st.info(st.session_state.message)

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

    # Add new candle every second or when forced by player action
    if (now - st.session_state.last_update_time >= CANDLE_INTERVAL and not st.session_state.force_update) or st.session_state.force_update:
        if not st.session_state.force_update:  # Normal interval update
            last_price = st.session_state.history[-1]["close"]
            predicted = predict_next_action() if st.session_state.trial_count >= 10 else random.choice(["buy", "sell"])
            st.session_state.history.append(generate_candle(last_price, predicted))
        
        st.session_state.last_update_time = now
        st.session_state.force_update = False
        st.experimental_rerun()  # Force immediate update of the chart

    # Game over check
    if elapsed >= TOTAL_TIME or st.session_state.trial_count >= TOTAL_TRIALS or st.session_state.score <= 0:
        st.session_state.started = False
        st.success(f"Game Over! Final Wallet: ${st.session_state.score:.2f}")
        st.stop()
