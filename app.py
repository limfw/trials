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
MEMORY_SIZE = 10

# Initialize all game state keys properly
if "game_state" not in st.session_state:
    st.session_state.game_state = {
        "started": False,
        "balance": INITIAL_BALANCE,
        "position": None,
        "entry_price": None,
        "history": generate_initial_candles(),  # Initialize with candles
        "start_time": time.time(),
        "last_candle_time": time.time(),
        "message": "",
        "trade_count": 0,
        "action_memory": deque(maxlen=MEMORY_SIZE),
        "market_bias": 0.0,  # Initialize with neutral bias
        "pattern_weights": {
            "buy_sequence": 0,
            "sell_sequence": 0,
            "alternating": 0
        },
        "prev_action": None
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
    
    # Initialize market bias if not exists
    if "market_bias" not in st.session_state.game_state:
        st.session_state.game_state["market_bias"] = 0.0
    
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
    
    if st.session_state.game_state["position"]:
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

# [Rest of your functions (enter_position, close_position) remain unchanged]

# Main UI
st.title("🚀 AI Market Manipulator Challenge")

if not st.session_state.game_state["started"]:
    if st.button("Start Challenge"):
        st.session_state.game_state.update({
            "started": True,
            "start_time": time.time(),
            "last_candle_time": time.time()
        })
        st.rerun()
else:
    now = time.time()
    time_left = max(0, MAX_GAME_TIME - (now - st.session_state.game_state["start_time"]))
    
    # Generate new candle
    if now - st.session_state.game_state["last_candle_time"] >= CANDLE_INTERVAL:
        if len(st.session_state.game_state["history"]) > 0:  # Ensure history exists
            new_candle = generate_adversarial_candle(st.session_state.game_state["history"][-1])
            st.session_state.game_state["history"].append(new_candle)
            st.session_state.game_state["last_candle_time"] = now
    
    # [Rest of your UI code remains unchanged]
