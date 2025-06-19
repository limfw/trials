import random
class RNNPredictor:
    def __init__(self):
        self.mapping = {"rock": 0, "paper": 1, "scissors": 2}
        self.reverse = {0: "rock", 1: "paper", 2: "scissors"}

    def predict_next_move(self, history):
        if not history:
            return random.choice(["rock", "paper", "scissors"])
        counts = {"rock": 0, "paper": 0, "scissors": 0}
        for move in history:
            counts[move] += 1
        predicted = max(counts, key=counts.get)
        if predicted == "rock":
            return "paper"
        elif predicted == "paper":
            return "scissors"
        else:
            return "rock"
