import random
from collections import defaultdict

class GANStrategy:
    def __init__(self):
        self.pattern_count = defaultdict(int)
        self.last_player_move = None
        self.repeat_streak = 0
        self.lose_switch_tracker = []

    def update_patterns(self, player_move, result):
        if player_move == self.last_player_move:
            self.repeat_streak += 1
        else:
            self.repeat_streak = 0

        self.last_player_move = player_move

        if result == "Lose":
            self.lose_switch_tracker.append(True)
        elif result == "Win":
            self.lose_switch_tracker.append(False)
        if len(self.lose_switch_tracker) > 5:
            self.lose_switch_tracker.pop(0)

        self.pattern_count[player_move] += 1

    def counter(self, move):
        if move == "rock":
            return "paper"
        elif move == "paper":
            return "scissors"
        else:
            return "rock"

    def generate_move(self, history, last_result):
        if self.repeat_streak >= 2:
            move = self.counter(self.last_player_move)
            return move

        if len(self.lose_switch_tracker) >= 3 and all(self.lose_switch_tracker):
            # Player keeps switching after losing
            # Predict what they will try next
            predicted = self.counter(self.last_player_move)
            return self.counter(predicted)

        if history:
            most_common = max(set(history), key=history.count)
            move = self.counter(most_common)
            return move

        return random.choice(["rock", "paper", "scissors"])

