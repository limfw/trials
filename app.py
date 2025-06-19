import streamlit as st
from streamlit_autorefresh import st_autorefresh
from collections import deque
from datetime import datetime
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import time
import random


st.set_page_config(page_title="Beat the Market AI", layout="wide")

st.markdown("""
<style>
.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}
.stButton > button {
    width: 100%;
    height: 50px;
    font-size: 16px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# Game Config
INITIAL_BALANCE = 100.00
TRADE_AMOUNT = 1.00
CANDLE_INTERVAL = 1.0
MAX_GAME_TIME = 90
MEMORY_SIZE = 10

# Utility Functions

def decay_weights():
    for k in st.session_state.game_state["pattern_weights"]:
        st.session_state.game_state["pattern_weights"][k] *= 0.95  # 5% decay per candle


def apply_bias(dominant):
    # 20% of the time apply a small random bias
    if random.random() < 0.2:
        return np.random.uniform(-0.2, 0.2)
    # otherwise apply standard capped bias
    return -0.3 if dominant == "buy_sequence" else 0.3


def generate_initial_candles(n=20):
    candles = []
    base_time = datetime.now() - pd.Timedelta(minutes=n)
    price = 100.00
    for i in range(n):
        change = np.random.normal(0, 0.3)
        new_price = price + change
        candles.append({
            "time": base_time + pd.Timedelta(minutes=i),
            "open": price,
            "high": max(price, new_price) + abs(np.random.normal(0, 0.1)),
            "low": min(price, new_price) - abs(np.random.normal(0, 0.1)),
            "close": new_price
        })
        price = new_price
    return candles


def generate_adversarial_candle(last_candle):
    last_close = last_candle["close"]
    base_change = np.random.normal(0, 0.3)
    bias = st.session_state.game_state["market_bias"]

    change = base_change + bias
    new_close = max(0.01, last_close + change)

    return {
        "time": last_candle["time"] + pd.Timedelta(minutes=1),
        "open": last_close,
        "high": max(last_close, new_close) + abs(np.random.normal(0, 0.1)),
        "low": min(last_close, new_close) - abs(np.random.normal(0, 0.1)),
        "close": new_close
    }


def update_ai_memory(action):
    memory = st.session_state.game_state["action_memory"]
    memory.append(action)
    weights = st.session_state.game_state["pattern_weights"]

    if len(memory) >= 2:
        if all(a == "buy" for a in memory):
            weights["buy_sequence"] += 1
        elif all(a == "sell" for a in memory):
            weights["sell_sequence"] += 1
        elif all(memory[i] != memory[i+1] for i in range(len(memory)-1)):
            weights["alternating"] += 1

    dominant = max(weights.items(), key=lambda x: x[1])[0]
    if dominant in ("buy_sequence", "sell_sequence"):
        st.session_state.game_state["market_bias"] = apply_bias(dominant)
    else:
        st.session_state.game_state["market_bias"] = np.random.uniform(-0.3, 0.3)


def enter_position(position_type):
    if st.session_state.game_state["position"]:
        st.session_state.game_state["message"] = "Close current position first!"
        return

    last_candle = st.session_state.game_state["history"][-1]
    st.session_state.game_state.update({
        "position": position_type,
        "entry_price": last_candle["close"],
        "trade_count": st.session_state.game_state["trade_count"] + 1
    })
    update_ai_memory(position_type)
    st.session_state.game_state["message"] = f"Entered {position_type.upper()} at ${last_candle['close']:.2f}"


def close_position():
    if not st.session_state.game_state["position"]:
        st.session_state.game_state["message"] = "No open position!"
        return

    last_candle = st.session_state.game_state["history"][-1]
    entry = st.session_state.game_state["entry_price"]
    position_type = st.session_state.game_state["position"]
    exit_price = last_candle["close"]
    bias = st.session_state.game_state["market_bias"]

    if position_type == "long":
        profit = (exit_price - entry) * TRADE_AMOUNT
        trap = bias < 0
    else:
        profit = (entry - exit_price) * TRADE_AMOUNT
        trap = bias > 0

    st.session_state.game_state["balance"] += profit
    st.session_state.game_state.update({
        "position": None,
        "entry_price": None
    })

    if profit < 0 and trap:
        st.session_state.game_state["ai_traps_triggered"] += 1
        st.session_state.game_state["message"] = f"AI TRAP! You lost ${abs(profit):.2f}"
    elif profit > 0 and trap:
        st.session_state.game_state["player_success_escapes"] += 1
        st.session_state.game_state["message"] = f"YOU ESCAPED AI TRAP! Gained ${profit:.2f}"
    else:
        st.session_state.game_state["message"] = f"Neutral trade result: ${profit:.2f}"

# Game State Init
if "game_state" not in st.session_state:
    st.session_state.game_state = {
        "started": False,
        "balance": INITIAL_BALANCE,
        "position": None,
        "entry_price": None,
        "history": generate_initial_candles(),
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
        "ai_traps_triggered": 0,
        "player_success_escapes": 0,
        "is_game_over": False,
        "last_update_count": 0
    }

# Initialize empty containers for different sections
if "containers" not in st.session_state:
    st.session_state.containers = {}

# Main title (static - doesn't need updates)
st.markdown("## Beat the Market AI — Outsmart the Manipulator!")

# Auto-refresh with counter
refresh_count = st_autorefresh(interval=1000, key="ai_trading_refresh")

# Only update game state when refresh count changes
if refresh_count != st.session_state.game_state["last_update_count"]:
    st.session_state.game_state["last_update_count"] = refresh_count
    
    # Update market data
    if st.session_state.game_state["started"] and not st.session_state.game_state.get("is_game_over", False):
        now = time.time()
        if now - st.session_state.game_state["last_candle_time"] >= CANDLE_INTERVAL:
            decay_weights()  # decay pattern weights each tick
            new_candle = generate_adversarial_candle(st.session_state.game_state["history"][-1])
            st.session_state.game_state["history"].append(new_candle)
            st.session_state.game_state["last_candle_time"] = now

# Game start section
if not st.session_state.game_state["started"]:
    st.markdown("""
    ### Instructions

    **Your Mission:**  
    Defeat the **biased market AI**. It watches your trades, learns your patterns, and manipulates prices to trap you. Your goal is to **profit while staying unpredictable**.

    **How the AI Thinks:**
    - Detects your patterns: **Buy / Sell / Alternating**
    - Adjusts market bias to move **against your current position**
    
    **How to Win:**  
    Escape more traps than you fall into.
    """)
    
    if st.button("🚀 Start Game", type="primary"):
        st.session_state.game_state.update({
            "started": True,
            "start_time": time.time(),
            "last_candle_time": time.time()
        })
        st.rerun()

else:
    # Game active - use containers for selective updates
    
    # Top metrics container (updates frequently)
    metrics_container = st.container()
    with metrics_container:
        now = time.time()
        time_left = max(0, MAX_GAME_TIME - (now - st.session_state.game_state["start_time"]))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("⏰ Time Left", f"{int(time_left)}s")
        with col2:
            current = st.session_state.game_state["balance"]
            initial = INITIAL_BALANCE
            delta = current - initial
            st.metric("💰 Balance", f"${current:.2f}", f"{delta:+.2f}")
        with col3:
            st.metric("📊 Trades", st.session_state.game_state["trade_count"])

    # Trading buttons container (static unless position changes)
    buttons_container = st.container()
    with buttons_container:
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📈 BUY LONG", disabled=bool(st.session_state.game_state["position"])):
                enter_position("long")
                st.rerun()
        with col2:
            if st.button("📉 SELL SHORT", disabled=bool(st.session_state.game_state["position"])):
                enter_position("short")
                st.rerun()
        with col3:
            if st.button("❌ CLOSE", disabled=not bool(st.session_state.game_state["position"])):
                close_position()
                st.rerun()

    # Position info (updates when position exists)
    if st.session_state.game_state["position"]:
        pos_container = st.container()
        with pos_container:
            pos_type = st.session_state.game_state["position"]
            entry_price = st.session_state.game_state["entry_price"]
            current_price = st.session_state.game_state["history"][-1]["close"]
            
            if pos_type == "long":
                pnl = (current_price - entry_price) * TRADE_AMOUNT
            else:
                pnl = (entry_price - current_price) * TRADE_AMOUNT
            
            pnl_color = "🟢" if pnl >= 0 else "🔴"
            st.info(f"{pnl_color} **{pos_type.upper()}** position | Entry: ${entry_price:.2f} | Current: ${current_price:.2f} | P&L: ${pnl:+.2f}")

    # Messages container
    if st.session_state.game_state["message"]:
        msg_container = st.container()
        with msg_container:
            if "TRAP" in st.session_state.game_state["message"]:
                st.error(st.session_state.game_state["message"])
            elif "ESCAPED" in st.session_state.game_state["message"]:
                st.success(st.session_state.game_state["message"])
            else:
                st.info(st.session_state.game_state["message"])

 
    chart_container = st.container()
    with chart_container:
        st.subheader("📊 Live Market Data")
  
        chart_key = f"chart_{len(st.session_state.game_state['history'])}"
        
        df = pd.DataFrame(st.session_state.game_state["history"][-25:])
        fig = go.Figure(go.Candlestick(
            x=df['time'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            increasing_line_color='#00ff00',
            decreasing_line_color='#ff0000',
            name="Price"
        ))
        
        fig.update_layout(
            height=400,
            showlegend=False,
            xaxis_rangeslider_visible=False,
            margin=dict(l=20, r=20, t=20, b=20),
            plot_bgcolor='rgba(0,0,0,0.05)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig, use_container_width=True, key=chart_key)

    # Sidebar (relatively static)
    with st.sidebar:
        st.header("🤖 AI Intelligence")
        
        st.subheader("Pattern Weights")
        for pattern, weight in st.session_state.game_state["pattern_weights"].items():
            progress = min(1.0, weight / 10)
            st.progress(progress, text=pattern.replace("_", " ").title())
        
        st.divider()
        st.subheader("Game Stats")
        st.write(f"🎯 AI Traps: {st.session_state.game_state['ai_traps_triggered']}")
        st.write(f"🏃 Escapes: {st.session_state.game_state['player_success_escapes']}")
        
        bias = st.session_state.game_state["market_bias"]
        if bias > 0.3:
            st.error("📈 Bias: ANTI-SHORT")
        elif bias < -0.3:
            st.error("📉 Bias: ANTI-LONG") 
        else:
            st.success("📊 Bias: NEUTRAL")

    # Game over logic
    if time_left <= 0 or st.session_state.game_state["balance"] <= 0:
        if not st.session_state.game_state["is_game_over"]:
            st.session_state.game_state["is_game_over"] = True
        
        game_over_container = st.container()
        with game_over_container:
            st.header("🎮 Game Over!")
            
            final_balance = st.session_state.game_state["balance"]
            traps = st.session_state.game_state["ai_traps_triggered"]
            escapes = st.session_state.game_state["player_success_escapes"]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Final Balance", f"${final_balance:.2f}")
            with col2:
                st.metric("AI Traps", traps)
            with col3:
                st.metric("Your Escapes", escapes)
            
            if escapes > traps:
                st.balloons()
                st.success("🎉 You outsmarted the AI!")
            elif escapes < traps:
                st.error("💀 The AI got you!")
            else:
                st.info("🤝 Stalemate with the AI!")
            
            if st.button("🔄 Restart Game", type="primary"):
                for key in list(st.session_state.keys()):
                    if 'game_state' in key:
                        del st.session_state[key]
                st.rerun()
