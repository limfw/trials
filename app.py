from streamlit_autorefresh import st_autorefresh
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
from datetime import datetime
from collections import deque

# Auto-refresh every second
st_autorefresh(interval=1000, key="market_refresh")

st.set_page_config(page_title="AI Market Manipulator", layout="wide")

# Game settings
INITIAL_BALANCE = 100.00
TRADE_AMOUNT = 1.00
CANDLE_INTERVAL = 1.0
MAX_GAME_TIME = 90
MEMORY_SIZE = 10  # How many past moves the AI remembers

if "game_state" not in st.session_state:
    st.session_state.game_state = {
        "started": False,
        "balance": INITIAL_BALANCE,
        "position": None,
        "entry_price": None,
        "history": [],
        "start_time": None,
        "last_candle_time": None,
        "message": "",
        "trade_count": 0,
        # AI Memory (simulates RNN hidden state)
        "action_memory": deque(maxlen=MEMORY_SIZE),
        "market_bias": 0.0,
        # LSTM-like pattern tracking
        "pattern_weights": {
            "buy_sequence": 0,
            "sell_sequence": 0,
            "alternating": 0
        }
    }

def generate_initial_candles(n=20):
    """Generate initial random candles"""
    candles = []
    price = 100.00
    for _ in range(n):
        change = np.random.normal(0, 0.3)
        new_price = price + change
        candles.append({
            "time": datetime.now(),
            "open": price,
            "high": max(price, new_price) + abs(np.random.normal(0, 0.1)),
            "low": min(price, new_price) - abs(np.random.normal(0, 0.1)),
            "close": new_price
        })
        price = new_price
    return candles

def update_ai_memory(action):
    """RNN-style memory update"""
    memory = st.session_state.game_state["action_memory"]
    memory.append(action)
    
    # LSTM-like pattern detection
    if len(memory) >= 2:
        # Detect sequences
        if all(a == "buy" for a in memory):
            st.session_state.game_state["pattern_weights"]["buy_sequence"] += 1
        elif all(a == "sell" for a in memory):
            st.session_state.game_state["pattern_weights"]["sell_sequence"] += 1
        elif all(memory[i] != memory[i+1] for i in range(len(memory)-1)):
            st.session_state.game_state["pattern_weights"]["alternating"] += 1
    
    # Calculate market bias (GAN-style adversarial response)
    dominant_pattern = max(
        st.session_state.game_state["pattern_weights"].items(),
        key=lambda x: x[1]
    )[0]
    
    if dominant_pattern == "buy_sequence":
        st.session_state.game_state["market_bias"] = -0.7  # Strong bearish bias
    elif dominant_pattern == "sell_sequence":
        st.session_state.game_state["market_bias"] = 0.7   # Strong bullish bias
    else:
        st.session_state.game_state["market_bias"] = np.random.uniform(-0.3, 0.3)

def generate_adversarial_candle(last_candle):
    """Generate candle with AI manipulation"""
    last_close = last_candle["close"]
    
    # Base market movement
    base_change = np.random.normal(0, 0.3)
    
    # AI adversarial component
    ai_bias = st.session_state.game_state["market_bias"]
    
    # If player has position, amplify against them
    if st.session_state.game_state["position"]:
        position_type = st.session_state.game_state["position"]
        if position_type == "long":
            ai_bias = min(-0.5, ai_bias - 0.3)  # Stronger downward pressure
        else:
            ai_bias = max(0.5, ai_bias + 0.3)   # Stronger upward pressure
    
    # Apply AI manipulation
    change = base_change + ai_bias
    new_close = last_close + change
    
    return {
        "time": datetime.now(),
        "open": last_close,
        "high": max(last_close, new_close) + abs(np.random.normal(0, 0.1)),
        "low": min(last_close, new_close) - abs(np.random.normal(0, 0.1)),
        "close": new_close
    }

def enter_position(position_type):
    """Handle player entering a trade"""
    if st.session_state.game_state["position"]:
        st.session_state.game_state["message"] = "Close current position first!"
        return
    
    last_candle = st.session_state.game_state["history"][-1]
    st.session_state.game_state.update({
        "position": position_type,
        "entry_price": last_candle["close"],
        "trade_count": st.session_state.game_state["trade_count"] + 1
    })
    
    # Update AI memory
    update_ai_memory(position_type.lower())
    
    st.session_state.game_state["message"] = (
        f"Entered {position_type} at {last_candle['close']:.2f}. "
        f"AI bias: {'Bullish' if st.session_state.game_state['market_bias'] > 0 else 'Bearish'}"
    )

def close_position():
    """Handle closing a trade"""
    if not st.session_state.game_state["position"]:
        st.session_state.game_state["message"] = "No open position!"
        return
    
    last_candle = st.session_state.game_state["history"][-1]
    entry = st.session_state.game_state["entry_price"]
    position_type = st.session_state.game_state["position"]
    exit_price = last_candle["close"]
    
    # Calculate P&L
    if position_type == "long":
        profit = (exit_price - entry) * TRADE_AMOUNT
    else:
        profit = (entry - exit_price) * TRADE_AMOUNT
    
    st.session_state.game_state["balance"] += profit
    st.session_state.game_state.update({
        "position": None,
        "entry_price": None
    })
    
    st.session_state.game_state["message"] = (
        f"Closed {position_type} position. "
        f"{'Gained' if profit >= 0 else 'Lost'} ${abs(profit):.2f}. "
        f"New balance: ${st.session_state.game_state['balance']:.2f}"
    )

# UI Rendering
st.title("🚀 AI Market Manipulator Challenge")

if not st.session_state.game_state["started"]:
    st.markdown("""
    ## Can You Outsmart the AI?
    - **The AI learns** your trading patterns like an RNN
    - **Market manipulates** prices against predictable behavior
    - **Survive 90 seconds** without being exploited
    - Starting balance: $100.00
    """)
    
    if st.button("Start Challenge"):
        st.session_state.game_state.update({
            "started": True,
            "history": generate_initial_candles(),
            "start_time": time.time(),
            "last_candle_time": time.time()
        })

else:
    # Game loop
    now = time.time()
    time_left = max(0, MAX_GAME_TIME - (now - st.session_state.game_state["start_time"]))
    
    # Generate new candle
    if now - st.session_state.game_state["last_candle_time"] >= CANDLE_INTERVAL:
        new_candle = generate_adversarial_candle(st.session_state.game_state["history"][-1])
        st.session_state.game_state["history"].append(new_candle)
        st.session_state.game_state["last_candle_time"] = now
    
    # Display
    st.write(f"⏳ Time left: {int(time_left)}s | 💰 Balance: ${st.session_state.game_state['balance']:.2f}")
    
    # Plot chart
    df = pd.DataFrame(st.session_state.game_state["history"][-20:])
    fig = go.Figure(go.Candlestick(
        x=df['time'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        increasing_line_color='green',
        decreasing_line_color='red'
    ))
    fig.update_layout(height=500, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # Trading buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("BUY LONG") and not st.session_state.game_state["position"]:
            enter_position("long")
    with col2:
        if st.button("SELL SHORT") and not st.session_state.game_state["position"]:
            enter_position("short")
    with col3:
        if st.button("CLOSE") and st.session_state.game_state["position"]:
            close_position()
    
    # AI status
    st.sidebar.subheader("🧠 AI Mind")
    st.sidebar.write(f"Detected pattern strength:")
    for pattern, weight in st.session_state.game_state["pattern_weights"].items():
        st.sidebar.progress(min(100, weight*10), text=pattern.replace("_", " ").title())
    
    # Game over check
    if time_left <= 0 or st.session_state.game_state["balance"] <= 0:
        st.session_state.game_state["started"] = False
        st.balloons() if st.session_state.game_state["balance"] > 100 else st.snow()
        st.success(f"Game over! Final balance: ${st.session_state.game_state['balance']:.2f}")
