"""
Reference Bot for Chaos League

Purpose:
- Demonstrate the correct bot interface
- Validate engine → bot communication
- Provide a baseline implementation
- Serve as a regression test for engine changes

This bot:
- Uses weighted randomness
- Tracks opponent's visible move frequencies
- Does NOT use deception tokens

This bot is STRICTLY RNG-compliant.
All randomness is sourced exclusively from the injected RNG.
"""

from collections import Counter
from engine.judge import Move, MOVES


class Bot:
    name = "ReferenceBot"

    def __init__(self):
        # Persistent bot state is allowed
        self.opponent_history = []
        self.move_counts = Counter()

    def play(self, state: dict, rng):
        """
        Required interface:
            play(state: dict, rng) -> dict
        """

        last_visible = state.get("opponent_last_visible")
        if last_visible is not None:
            self.opponent_history.append(last_visible)
            self.move_counts[last_visible] += 1

        # Early game: uniform random
        if len(self.opponent_history) < 10:
            return {"real_move": rng.choice(MOVES)}

        # Exploit most frequent opponent move
        most_common, _ = self.move_counts.most_common(1)[0]
        counters = self._counters_for(most_common)

        return {"real_move": rng.choice(counters)}

    def request_shadow_move(self, state: dict):
        """
        Required interface.
        Reference bot never uses deception.
        """
        return False, None

    @staticmethod
    def _counters_for(move: Move):
        return {
            Move.ROCK:     [Move.PAPER, Move.SPOCK],
            Move.PAPER:    [Move.SCISSORS, Move.LIZARD],
            Move.SCISSORS: [Move.ROCK, Move.SPOCK],
            Move.LIZARD:   [Move.ROCK, Move.SCISSORS],
            Move.SPOCK:    [Move.PAPER, Move.LIZARD],
        }[move]
