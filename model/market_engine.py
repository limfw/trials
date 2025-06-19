import random

class MarketEngine:
    def __init__(self):
        pass

    def get_price_change(self, signal, predicted_action, player_action):
        base = random.uniform(-1, 1)
        if signal == "fake_breakout":
            return 2 if predicted_action == "buy" else -2
        elif signal == "trap":
            return -2 if predicted_action == "buy" else 2
        elif signal == "trend":
            return 1.5 if player_action == "buy" else -1.5
        elif signal == "reversal":
            return -1.5 if player_action == "buy" else 1.5
        else:
            return base

    def get_profit(self, action, price_change):
        if action == "buy":
            return price_change
        elif action == "sell":
            return -price_change
        else:
            return 0
