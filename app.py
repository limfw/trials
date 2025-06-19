import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh  # NEW IMPORT

st.set_page_config(page_title="Live Trading Simulator", layout="wide")

# Auto-refresh every 1000ms (1 second)
st_autorefresh(interval=1000, key="refresh")

# Game settings
INITIAL_BALANCE = 100.00
TRADE_AMOUNT = 1.00
CANDLE_INTERVAL = 1.0  # New candle every second
MAX_GAME_TIME = 90     # 90 seconds game duration

if "game_state" not in st.session_state:
    st.session_state.game_state = {
        "started": False,
        "balance": INITIAL_BALANCE,
        "position": None,  # "long", "short", or None
        "entry_price": None,
        "history": [],
        "start_time": None,
        "last_candle_time": None,
        "message": "",
        "trade_count": 0
    }

def generate_initial_candles(n=20):
    candles = []
    price = 100.00
    for _ in range(n):
        change = np.random.normal(0, 0.5)
        new_price = price + change
        candles.append({
            "time": datetime.now(),
            "open": price,
            "high": max(price, new_price) + abs(np.random.normal(0, 0.2)),
            "low": min(price, new_price) - abs(np.random.normal(0, 0.2)),
            "close": new_price
        })
        price = new_price
    return candles

def generate_new_candle(last_candle):
    last_close = last_candle["close"]
    change = np.random.normal(0, 0.5)
    
    # If player has position, market may move against them
    if st.session_state.game_state["position"]:
        if random.random() > 0.4:  # 60% chance market moves against position
            change = -change if st.session_state.game_state["position"] == "long" else abs(change)
    
    new_close = last_close + change
    return {
        "time": datetime.now(),
        "open": last_close,
        "high": max(last_close, new_close) + abs(np.random.normal(0, 0.2)),
        "low": min(last_close, new_close) - abs(np.random.normal(0, 0.2)),
        "close": new_close
    }

def plot_chart(candles):
    df = pd.DataFrame(candles)
    fig = go.Figure(data=[go.Candlestick(
        x=df['time'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        increasing_line_color='green',
        decreasing_line_color='red'
    )])
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        height=500,
        title="Live Market Price",
        yaxis_title="Price"
    )
    st.plotly_chart(fig, use_container_width=True)

def enter_position(position_type):
    if st.session_state.game_state["position"] is not None:
        st.session_state.game_state["message"] = "You already have an open position!"
        return
    
    last_candle = st.session_state.game_state["history"][-1]
    st.session_state.game_state.update({
        "position": position_type,
        "entry_price": last_candle["close"],
        "trade_count": st.session_state.game_state["trade_count"] + 1
    })
    st.session_state.game_state["message"] = f"Opened {position_type} position at {last_candle['close']:.2f}"

def close_position():
    if st.session_state.game_state["position"] is None:
        st.session_state.game_state["message"] = "No position to close!"
        return
    
    last_candle = st.session_state.game_state["history"][-1]
    exit_price = last_candle["close"]
    entry = st.session_state.game_state["entry_price"]
    position_type = st.session_state.game_state["position"]
    
    if position_type == "long":
        profit = (exit_price - entry) * TRADE_AMOUNT
    else:  # short
        profit = (entry - exit_price) * TRADE_AMOUNT
    
    st.session_state.game_state["balance"] += profit
    st.session_state.game_state.update({
        "position": None,
        "entry_price": None
    })
    st.session_state.game_state["message"] = f"Closed {position_type} position. {'Gained' if profit >=0 else 'Lost'} ${abs(profit):.2f}"

# Main game interface
st.title("Live Trading Simulator")

if not st.session_state.game_state["started"]:
    st.markdown("""
    ### Trading Rules:
    - Market updates every second automatically
    - Click BUY to bet price will rise (go long)
    - Click SELL to bet price will fall (go short)
    - Click CLOSE to close your position
    - Positions auto-close after 10 seconds
    - Starting balance: $100.00
    - Trade amount: $1.00 per position
    """)
    
    if st.button("Start Trading"):
        st.session_state.game_state.update({
            "started": True,
            "balance": INITIAL_BALANCE,
            "history": generate_initial_candles(),
            "start_time": time.time(),
            "last_candle_time": time.time(),
            "message": "Game started! Place your first trade.",
            "trade_count": 0
        })
        st.experimental_rerun()
else:
    # Game active section
    now = time.time()
    elapsed = now - st.session_state.game_state["start_time"]
    time_left = max(0, MAX_GAME_TIME - elapsed)
    
    # Display game info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Time Left", f"{int(time_left)}s")
    with col2:
        st.metric("Balance", f"${st.session_state.game_state['balance']:.2f}")
    with col3:
        st.metric("Trades", st.session_state.game_state["trade_count"])
    
    # Generate new candles automatically
    if now - st.session_state.game_state["last_candle_time"] >= CANDLE_INTERVAL:
        new_candle = generate_new_candle(st.session_state.game_state["history"][-1])
        st.session_state.game_state["history"].append(new_candle)
        st.session_state.game_state["last_candle_time"] = now
        
        # Auto-close position after 10 seconds
        if st.session_state.game_state["position"] and len(st.session_state.game_state["history"]) > 10:
            last_10_candles = st.session_state.game_state["history"][-10:]
            if all(c["time"] > last_10_candles[0]["time"] for c in last_10_candles[1:]):
                close_position()
        
        st.experimental_rerun()
    
    # Display chart
    plot_chart(st.session_state.game_state["history"][-20:])  # Show last 20 candles
    
    # Display current position info
    if st.session_state.game_state["position"]:
        current_price = st.session_state.game_state["history"][-1]["close"]
        entry = st.session_state.game_state["entry_price"]
        pnl = (current_price - entry) if st.session_state.game_state["position"] == "long" else (entry - current_price)
        st.info(f"Open {st.session_state.game_state['position']} position | Entry: ${entry:.2f} | Current: ${current_price:.2f} | P&L: ${pnl:.2f}")
    
    # Display messages
    if st.session_state.game_state["message"]:
        st.success(st.session_state.game_state["message"])
    
    # Trading buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("BUY (Go Long)") and st.session_state.game_state["position"] is None:
            enter_position("long")
            st.experimental_rerun()
    with col2:
        if st.button("SELL (Go Short)") and st.session_state.game_state["position"] is None:
            enter_position("short")
            st.experimental_rerun()
    with col3:
        if st.button("CLOSE Position") and st.session_state.game_state["position"] is not None:
            close_position()
            st.experimental_rerun()
    
    # End game conditions
    if time_left <= 0:
        st.session_state.game_state["started"] = False
        st.balloons()
        st.success(f"Trading session ended! Final balance: ${st.session_state.game_state['balance']:.2f}")
        st.stop()
