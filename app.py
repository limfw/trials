from streamlit_autorefresh import st_autorefresh
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
import random
from datetime import datetime
from collections import deque

# Set up auto-refresh every 1000ms (1 second)
st_autorefresh(interval=1000, key="market_refresh")

st.set_page_config(page_title="AI Market Manipulator", layout="wide")

# Game settings
INITIAL_BALANCE = 100.00
TRADE_AMOUNT = 1.00
CANDLE_INTERVAL = 1.0
MAX_GAME_TIME = 90
MEMORY_SIZE = 10  # How many past moves the AI remembers

# Define all functions first before using them
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
    if "action_memory" not in st.session_state.game_state:
        st.session_state.game_state["action_memory"] = deque(maxlen=MEMORY_SIZE)
    
    st.session_state.game_state["action_memory"].append(action)
    
    # Initialize pattern weights if not exists
    if "pattern_weights" not in st.session_state.game_state:
        st.session_state.game_state["pattern_weights"] = {
            "buy_sequence": 0,
            "sell_sequence": 0,
            "alternating": 0
        }
    
    # LSTM-like pattern detection
    memory = st.session_state.game_state["action_memory"]
    if len(memory) >= 2:
        if all(a == "buy" for a in memory):
            st.session_state.game_state["pattern_weights"]["buy_sequence"] += 1
        elif all(a == "sell" for a in memory):
            st.session_state.game_state["pattern_weights"]["sell_sequence"] += 1
        elif all(memory[i] != memory[i+1] for i in range(len(memory)-1)):
            st.session_state.game_state["pattern_weights"]["alternating"] += 1
    
    # Calculate market bias
    dominant_pattern = max(
        st.session_state.game_state["pattern_weights"].items(),
        key=lambda x: x[1]
    )[0]
    
    if dominant_pattern == "buy_sequence":
        st.session_state.game_state["market_bias"] = -0.7
    elif dominant_pattern == "sell_sequence":
        st.session_state.game_state["market_bias"] = 0.7
    else:
        st.session_state.game_state["market_bias"] = np.random.uniform(-0.3, 0.3)

def generate_adversarial_candle(last_candle):
    """Generate candle with AI manipulation"""
    # Ensure market_bias exists
    if "market_bias" not in st.session_state.game_state:
        st.session_state.game_state["market_bias"] = 0.0
    
    last_close = last_candle["close"]
    base_change = np.random.normal(0, 0.3)
    ai_bias = st.session_state.game_state["market_bias"]
    
    if st.session_state.game_state.get("position"):
        position_type = st.session_state.game_state["position"]
        if position_type == "long":
            ai_bias = min(-0.5, ai_bias - 0.3)
        else:
            ai_bias = max(0.5, ai_bias + 0.3)
    
    change = base_change + ai_bias
    new_close = max(0.01, last_close + change)  # Prevent negative prices
    
    return {
        "time": datetime.now(),
        "open": last_close,
        "high": max(last_close, new_close) + abs(np.random.normal(0, 0.1)),
        "low": min(last_close, new_close) - abs(np.random.normal(0, 0.1)),
        "close": new_close
    }

def enter_position(position_type):
    """Handle player entering a trade"""
    if st.session_state.game_state.get("position"):
        st.session_state.game_state["message"] = "Close current position first!"
        return
    
    last_candle = st.session_state.game_state["history"][-1]
    st.session_state.game_state.update({
        "position": position_type,
        "entry_price": last_candle["close"],
        "trade_count": st.session_state.game_state.get("trade_count", 0) + 1
    })
    
    # Update AI memory
    update_ai_memory(position_type.lower())
    
    st.session_state.game_state["message"] = (
        f"Entered {position_type} at {last_candle['close']:.2f}. "
        f"AI bias: {'Bullish' if st.session_state.game_state['market_bias'] > 0 else 'Bearish'}"
    )

def close_position():
    """Handle closing a trade"""
    if not st.session_state.game_state.get("position"):
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
    
    st.session_state.game_state["balance"] = st.session_state.game_state.get("balance", INITIAL_BALANCE) + profit
    st.session_state.game_state.update({
        "position": None,
        "entry_price": None
    })
    
    st.session_state.game_state["message"] = (
        f"Closed {position_type} position. "
        f"{'Gained' if profit >= 0 else 'Lost'} ${abs(profit):.2f}. "
        f"New balance: ${st.session_state.game_state['balance']:.2f}"
    )

# Initialize game state (after all functions are defined)
if "game_state" not in st.session_state:
    st.session_state.game_state = {
        "started": False,
        "balance": INITIAL_BALANCE,
        "position": None,
        "entry_price": None,
        "history": generate_initial_candles(),  # Now this function is defined
        "start_time": time.time(),
        "last_candle_time": time.time(),
        "message": "",
        "trade_count": 0,
        "action_memory": deque(maxlen=MEMORY_SIZE),
        "market_bias": 0.0,
        "pattern_weights": {
            "buy_sequence": 0,
            "sell_sequence": 0,
            "alternating": 0
        },
        "prev_action": None
    }

# Main UI
st.title("🚀 AI Market Manipulator Challenge")

if not st.session_state.game_state["started"]:
    st.markdown("""
    ## Can You Outsmart the AI?
    - **The AI learns** your trading patterns in real-time
    - **Market manipulates** prices against predictable behavior
    - **Survive 90 seconds** without being exploited
    - Starting balance: $100.00
    """)
    
    if st.button("Start Challenge"):
        st.session_state.game_state.update({
            "started": True,
            "start_time": time.time(),
            "last_candle_time": time.time()
        })
        st.rerun()
else:
    # Game loop
    now = time.time()
    time_left = max(0, MAX_GAME_TIME - (now - st.session_state.game_state["start_time"]))
    
    # Generate new candle
    if now - st.session_state.game_state["last_candle_time"] >= CANDLE_INTERVAL:
        if len(st.session_state.game_state["history"]) > 0:
            new_candle = generate_adversarial_candle(st.session_state.game_state["history"][-1])
            st.session_state.game_state["history"].append(new_candle)
            st.session_state.game_state["last_candle_time"] = now
    
    # Display
    st.write(f"⏳ Time left: {int(time_left)}s | 💰 Balance: ${st.session_state.game_state['balance']:.2f}")
    
    # Plot chart
    if len(st.session_state.game_state["history"]) > 0:
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
        if st.button("BUY LONG") and not st.session_state.game_state.get("position"):
            enter_position("long")
    with col2:
        if st.button("SELL SHORT") and not st.session_state.game_state.get("position"):
            enter_position("short")
    with col3:
        if st.button("CLOSE") and st.session_state.game_state.get("position"):
            close_position()
    
    # Display messages
    if st.session_state.game_state.get("message"):
        st.info(st.session_state.game_state["message"])
    
    # AI status
    st.sidebar.subheader("🧠 AI Mind")
    if "pattern_weights" in st.session_state.game_state:
        st.sidebar.write("Detected pattern strength:")
        for pattern, weight in st.session_state.game_state["pattern_weights"].items():
            st.sidebar.progress(min(100, weight*10), text=pattern.replace("_", " ").title())
    
    # Game over check
    if time_left <= 0 or st.session_state.game_state.get("balance", 100) <= 0:
        st.session_state.game_state["started"] = False
        final_balance = st.session_state.game_state.get("balance", 100)
        if final_balance > 100:
            st.balloons()
            st.success(f"Congratulations! Final balance: ${final_balance:.2f}")
        else:
            st.error(f"Game over! Final balance: ${final_balance:.2f}")
