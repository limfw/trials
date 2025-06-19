import streamlit as st
from streamlit_autorefresh import st_autorefresh
from collections import deque
from datetime import datetime
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import random
import time
import streamlit.components.v1 as components # Import components

# Auto-refresh every 1 second
st.set_page_config(page_title="Beat the Market AI", layout="wide")
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st_autorefresh(interval=1000, key="ai_trading_refresh")

# Game Config
INITIAL_BALANCE = 100.00
TRADE_AMOUNT = 1.00
CANDLE_INTERVAL = 1.0
MAX_GAME_TIME = 90
MEMORY_SIZE = 10

# === Utility Functions ===

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

    if st.session_state.game_state["position"]:
        if st.session_state.game_state["position"] == "long":
            bias = min(-0.5, bias - 0.3)
        else: # position == "short"
            bias = max(0.5, bias + 0.3)

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

    # Determine dominant pattern and set market bias
    dominant = max(weights.items(), key=lambda x: x[1])[0]
    if dominant == "buy_sequence":
        st.session_state.game_state["market_bias"] = -0.7 # Punish buying
    elif dominant == "sell_sequence":
        st.session_state.game_state["market_bias"] = 0.7  # Punish selling
    else: # alternating or no clear pattern
        st.session_state.game_state["market_bias"] = np.random.uniform(-0.3, 0.3) # More neutral/random

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
        trap = bias < 0 # Market biased downwards when you are long
    else: # position_type == "short"
        profit = (entry - exit_price) * TRADE_AMOUNT
        trap = bias > 0 # Market biased upwards when you are short

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

# === Game State Init ===
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
        "is_game_over": False
    }

# Initialize scroll key counter if not present
if "scroll_key_counter" not in st.session_state:
    st.session_state.scroll_key_counter = 0

# Function to keep scroll position
def scroll_position_keeper():
    st.session_state.scroll_key_counter += 1
    js_code = """
    <script>
        var mainDiv = window.parent.document.querySelector('.main');
        if (mainDiv) {
            // Save scroll position
            mainDiv.addEventListener('scroll', function() {
                localStorage.setItem('streamlitScrollPos', mainDiv.scrollTop);
            });

            // Restore scroll position
            var savedScrollPos = localStorage.getItem('streamlitScrollPos');
            if (savedScrollPos) {
                mainDiv.scrollTop = savedScrollPos;
                // Optional: Clear after restoring if you want it reset on full new session
                // localStorage.removeItem('streamlitScrollPos');
            }
        }
    </script>
    """
    # REMOVED the 'key' argument from the line below
    components.html(js_code, height=0, width=0)

# === UI ===
st.markdown("## Biased Market Challenge — Outsmart the AI Manipulator Before It Breaks You!")

if not st.session_state.game_state["started"]:
    st.markdown("""
    ### Instruction

    **Your Mission:**  
    Defeat the **biased market AI**. It watches your trades, learns your patterns, and manipulates prices to trap you. Your goal is to **profit while staying unpredictable**.

    **How the AI Thinks:**
    - Detects your move: **Buy / Sell / Alternating**
    - Adjusts the market bias to move **against your current position**
    
    **How to Win:**  
    Escape more traps than you fall into.
    """)
    if st.button("Start Game"):
        st.session_state.game_state.update({
            "started": True,
            "start_time": time.time(),
            "last_candle_time": time.time()
        })
        st.rerun()
else:
    now = time.time()
    time_left = max(0, MAX_GAME_TIME - (now - st.session_state.game_state["start_time"]))
    if not st.session_state.game_state.get("is_game_over", False):
        if now - st.session_state.game_state["last_candle_time"] >= CANDLE_INTERVAL:
            new_candle = generate_adversarial_candle(st.session_state.game_state["history"][-1])
            st.session_state.game_state["history"].append(new_candle)
            st.session_state.game_state["last_candle_time"] = now

    colA, colB, colC = st.columns(3)
    with colA:
        st.metric("Time Left", f"{int(time_left)}s")
        if st.button("BUY LONG") and not st.session_state.game_state["position"]:
            enter_position("long")
    with colB:
        initial = INITIAL_BALANCE
        current = st.session_state.game_state["balance"]
        wallet_delta = current - initial
        wallet_text = f"${current:.2f} ({'+' if wallet_delta >= 0 else ''}{wallet_delta:.2f})"
        st.metric("Wallet", wallet_text)
        if st.button("SELL SHORT") and not st.session_state.game_state["position"]:
            enter_position("short")
    with colC:
        st.metric("Trades", st.session_state.game_state["trade_count"])
        if st.button("CLOSE") and st.session_state.game_state["position"]:
            close_position()

    # === Game Message ===
    if st.session_state.game_state["message"]:
        st.info(st.session_state.game_state["message"])
        
    # === Candlestick Chart ===
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
    fig.update_layout(
        height=350,
        autosize=True,
        margin=dict(l=10, r=10, t=5, b=20),
        xaxis_rangeslider_visible=False
    )
    st.plotly_chart(fig, use_container_width=True)

    # === Sidebar AI Feedback ===
    st.sidebar.subheader("AI Intelligence")
    for k, v in st.session_state.game_state["pattern_weights"].items():
        st.sidebar.progress(min(100, v * 10), text=k.replace("_", " ").title())
    st.sidebar.write(f"Traps Triggered: {st.session_state.game_state['ai_traps_triggered']}")
    st.sidebar.write(f"Escapes: {st.session_state.game_state['player_success_escapes']}")

    if time_left <= 0 or st.session_state.game_state["balance"] <= 0:
        st.session_state.game_state["is_game_over"] = True
        if st.session_state.game_state["is_game_over"]:
            st.warning("Game Over!")
            final_balance = st.session_state.game_state["balance"]
            traps = st.session_state.game_state["ai_traps_triggered"]
            escapes = st.session_state.game_state["player_success_escapes"]
            st.metric("Final Balance", f"${final_balance:.2f}")
            st.metric("AI Traps Triggered", traps)
            st.metric("Player Escapes", escapes)

            if escapes > traps:
                st.balloons()
                st.success("🎉 You outsmarted the AI!")
            elif escapes < traps:
                st.error("💀 The AI manipulated the market against you!")
            else:
                st.info("🤝 A stalemate with the AI.")
            if st.button("Restart Game"):
                st.session_state.clear()
                st.rerun()

# Call the scroll position keeper function at the end
scroll_position_keeper()
