import random

class MarketGAN:
    def __init__(self):
        self.fake_signals = ["fake_breakout", "trap", "noise", "trend", "reversal"]

    def generate_signal(self):
        return random.choice(self.fake_signals)
