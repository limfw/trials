import streamlit as st
import time
import random
import numpy as np
from model.rnn_model import RNNPredictor
from model.gan_module import GANStrategy

if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'moves' not in st.session_state:
    st.session_state.moves = []
if 'results' not in st.session_state:
    st.session_state.results = []
if 'rnn' not in st.session_state:
    st.session_state.rnn = RNNPredictor()
if 'gan' not in st.session_state:
    st.session_state.gan = GANStrategy()

def ai_decision():
    history = [m['player'] for m in st.session_state.moves[-5:]]
    rnn_predict = st.session_state.rnn.predict_next_move(history)
    gan_predict = st.session_state.gan.generate_move(history)
    return random.choice([rnn_predict, gan_predict])

def result(player, ai):
    if player == ai:
        return "Draw"
    elif (player == "rock" and ai == "scissors") or \
         (player == "scissors" and ai == "paper") or \
         (player == "paper" and ai == "rock"):
        return "Win"
    else:
        return "Lose"

st.title("Can You Defeat the Computer?")
st.markdown("Can You Identify the Algorithms Behind This Game? Try It First, Then Share Your Answer!")

if st.button("Start Game"):
    st.session_state.start_time = time.time()
    st.session_state.moves = []
    st.session_state.results = []

if st.session_state.start_time:
    elapsed = int(time.time() - st.session_state.start_time)
    remaining = max(0, 60 - elapsed)
    st.write(f"Time Left: {remaining} seconds")

    if remaining > 0 and len(st.session_state.moves) < 60:
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Rock"):
                ai = ai_decision()
                res = result("rock", ai)
                st.session_state.moves.append({"player": "rock", "ai": ai})
                st.session_state.results.append(res)
        with col2:
            if st.button("Paper"):
                ai = ai_decision()
                res = result("paper", ai)
                st.session_state.moves.append({"player": "paper", "ai": ai})
                st.session_state.results.append(res)
        with col3:
            if st.button("Scissors"):
                ai = ai_decision()
                res = result("scissors", ai)
                st.session_state.moves.append({"player": "scissors", "ai": ai})
                st.session_state.results.append(res)

        st.write(f"Rounds played: {len(st.session_state.moves)} / 60")
    else:
        st.success("Game Over!")
        win_count = st.session_state.results.count("Win")
        draw_count = st.session_state.results.count("Draw")
        loss_count = st.session_state.results.count("Lose")
        st.write(f"Wins: {win_count} | Losses: {loss_count} | Draws: {draw_count}")
