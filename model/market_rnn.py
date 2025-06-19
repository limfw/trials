import random
from collections import deque

class MarketRNN:
    def __init__(self):
        self.memory = deque(maxlen=5)

    def update(self, action):
        self.memory.append(action)

    def predict_next_move(self, history):
        if not self.memory:
            return random.choice(["buy", "hold", "sell"])
        freq = {"buy": 0, "hold": 0, "sell": 0}
        for a in self.memory:
            freq[a] += 1
        return max(freq, key=freq.get)
