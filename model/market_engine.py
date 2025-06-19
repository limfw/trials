import random

class MarketEngine:
    def generate_candle(self, signal, last_price):
        base_move = random.uniform(-1.0, 1.0)
        if signal == "fake_breakout":
            move = abs(base_move) * 1.5
        elif signal == "trap":
            move = -abs(base_move) * 1.5
        elif signal == "trend":
            move = random.uniform(0.5, 2.0)
        elif signal == "reversal":
            move = -random.uniform(0.5, 2.0)
        else:
            move = base_move

        open_price = last_price
        close_price = last_price + move
        high_price = max(open_price, close_price) + random.uniform(0, 0.5)
        low_price = min(open_price, close_price) - random.uniform(0, 0.5)

        return {
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
        }

    def calculate_score(self, action, price_change):
        if action == "hold":
            return 0
        elif action == "buy" and price_change > 0:
            return 1
        elif action == "sell" and price_change < 0:
            return 1
        else:
            return -1
