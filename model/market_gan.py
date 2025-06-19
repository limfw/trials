import random

class MarketGAN:
    def __init__(self):
        self.fake_signals = ["fake_breakout", "trap", "trend", "reversal", "noise"]

    def generate_signal(self, prediction):
        if prediction == "buy":
            return random.choice(["trap", "reversal"])
        elif prediction == "sell":
            return random.choice(["fake_breakout", "trend"])
        else:
            return random.choice(self.fake_signals)
