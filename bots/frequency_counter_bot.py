"""
Frequency Counter Bot.
Counters opponent's most frequent visible move.
"""

from collections import Counter
from engine.judge import Move, WIN_MAP

class Bot:
    name = "FrequencyCounterBot"

    def __init__(self):
        self.opponent_history = []

    def play(self, state, rng):
        last = state["opponent_last_visible"]
        if last is not None:
            self.opponent_history.append(last)

        if not self.opponent_history:
            return {
                "real_move": Move.ROCK,
                "shadow": False,
            }

        counts = Counter(self.opponent_history)
        most_common, _ = counts.most_common(1)[0]

        # Pick a move that beats the most common
        counters = [
            m for m, beats in WIN_MAP.items()
            if most_common in beats
        ]

        if not counters:
            # Fallback to a default move if no counter is found
            return {
                "real_move": Move.ROCK,
                "shadow": False,
            }

        chosen = counters[0]  # deterministic choice

        return {
            "real_move": chosen,
            "shadow": False,
        }
