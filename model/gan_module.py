import random

class GANStrategy:
    def __init__(self):
        pass

    def generate_move(self, history):
        # Simple deception: randomly switch to confuse player pattern tracking
        # Can be replaced later by a true GAN training loop
        return random.choice(["rock", "paper", "scissors"])
