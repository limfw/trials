import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import random
import time
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Dense
from tensorflow.keras.utils import to_categorical

# --- CONFIG ---
TOTAL_TIME = 120  # seconds
action_interval = 2  # player can act every 2 seconds
candle_interval = 1  # chart updates every second
MAX_TRIALS = 60
INIT_TREND = 20

# --- SESSION STATE INIT ---
if "started" not in st.session_state:
    st.session_state.started = False
    st.session_state.history = []
    st.session_state.actions = []
    st.session_state.trial = 0
    st.session_state.score = 0
    st.session_state.start_time = 0
    st.session_state.last_action_time = 0
    st.session_state.last_candle_time = 0
    st.session_state.model_trained = False
    st.session_state.model = None

# --- INITIAL TREND GENERATOR ---
def generate_initial_trend(n):
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

# --- CANDLE FUNCTIONS ---
def generate_random_candle(prev_price):
    delta = np.random.uniform(-1.0, 1.0)
    o = prev_price
    c = prev_price + delta
    h = max(o, c) + np.random.uniform(0.1, 0.5)
    l = min(o, c) - np.random.uniform(0.1, 0.5)
    return {"open": o, "high": h, "low": l, "close": c}

def generate_trap_candle(prev_price, predicted_action):
    delta = np.random.uniform(0.5, 1.5)
    if predicted_action == 0:  # Buy
        o, c = prev_price, prev_price - delta
    elif predicted_action == 2:  # Sell
        o, c = prev_price, prev_price + delta
    else:
        o, c = prev_price, prev_price + np.random.normal(0, 0.3)
    h = max(o, c) + np.random.uniform(0.1, 0.5)
    l = min(o, c) - np.random.uniform(0.1, 0.5)
    return {"open": o, "high": h, "low": l, "close": c}

# --- MODEL FUNCTIONS ---
action_map = {"Buy": 0, "Hold": 1, "Sell": 2}
def train_lstm_model(action_seq):
    X, y = [], []
    for i in range(len(action_seq) - 5):
        X.append([action_map[a] for a in action_seq[i:i + 5]])
        y.append(action_map[action_seq[i + 5]])
    X, y = np.array(X), to_categorical(np.array(y), num_classes=3)
    model = Sequential([
        Embedding(3, 8, input_length=5),
        LSTM(16),
        Dense(3, activation='softmax')
    ])
    model.compile(optimizer='adam', loss='categorical_crossentropy')
    model.fit(X, y, epochs=10, verbose=0)
    return model

def predict_next_action(model, recent_actions):
    if len(recent_actions) < 5:
        return random.randint(0, 2)
    seq = [action_map[a] for a in recent_actions[-5:]]
    seq = np.array(seq).reshape(1, -1)
    pred = model.predict(seq, verbose=0)[0]
    return int(np.argmax(pred))

# --- DISPLAY CHART ---
def plot_chart(data):
    df = pd.DataFrame(data)
    fig = go.Figure(data=[go.Candlestick(x=list(range(len(df))),
                                         open=df['open'],
                                         high=df['high'],
                                         low=df['low'],
                                         close=df['close'])])
    fig.update_layout(xaxis_rangeslider_visible=False, height=500)
    st.plotly_chart(fig, use_container_width=True)

# --- ACTION HANDLER ---
def handle_action(choice):
    st.session_state.actions.append(choice)
    latest = st.session_state.history[-1]
    prev = st.session_state.history[-2]
    correct = (latest['close'] > prev['close'] and choice == "Buy") or \
              (latest['close'] < prev['close'] and choice == "Sell")
    if choice == "Hold":
        pass
    elif correct:
        st.session_state.score += 1
    else:
        st.session_state.score -= 1
    st.session_state.trial += 1

# --- GAME LOGIC ---
st.title("Beat the Market AI")
if not st.session_state.started:
    st.write("### Welcome to the Challenge")
    st.markdown("""
    - You are a trader in a deceptive AI market.
    - Game lasts 120 seconds, and you must make 60 moves.
    - First 30 moves: AI learns your pattern.
    - Last 30 moves: AI predicts and deceives you!
    """)
    if st.button("Start Game"):
        st.session_state.history = generate_initial_trend(INIT_TREND)
        st.session_state.actions = []
        st.session_state.score = 0
        st.session_state.trial = 0
        st.session_state.started = True
        st.session_state.start_time = time.time()
        st.session_state.last_action_time = 0
        st.session_state.last_candle_time = 0
else:
    now = time.time()
    elapsed = now - st.session_state.start_time
    time_left = max(0, int(TOTAL_TIME - elapsed))
    st.write(f"Time left: {time_left}s")
    st.write(f"Trial: {st.session_state.trial}/60")
    st.write(f"Score: {st.session_state.score}")

    # Chart update every second
    if now - st.session_state.last_candle_time >= candle_interval:
        last_price = st.session_state.history[-1]['close']
        if st.session_state.trial < 30:
            new_candle = generate_random_candle(last_price)
        else:
            if not st.session_state.model_trained:
                st.session_state.model = train_lstm_model(st.session_state.actions)
                st.session_state.model_trained = True
            predicted = predict_next_action(st.session_state.model, st.session_state.actions)
            new_candle = generate_trap_candle(last_price, predicted)
        st.session_state.history.append(new_candle)
        st.session_state.last_candle_time = now

    plot_chart(st.session_state.history[-40:])

    # Player can act every 2 seconds
    if st.session_state.trial < MAX_TRIALS and now - st.session_state.last_action_time >= action_interval:
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Buy"):
                handle_action("Buy")
                st.session_state.last_action_time = now
        with col2:
            if st.button("Hold"):
                handle_action("Hold")
                st.session_state.last_action_time = now
        with col3:
            if st.button("Sell"):
                handle_action("Sell")
                st.session_state.last_action_time = now

    # End condition
    if elapsed >= TOTAL_TIME or st.session_state.trial >= MAX_TRIALS:
        st.success(f"Game Over. Final Score: {st.session_state.score}")
        st.session_state.started = False
