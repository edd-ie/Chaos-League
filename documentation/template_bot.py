"""
Chaos League Template Bot

Copy this file, rename it, and modify the logic inside play().

Key rules:
- You MUST use the injected RNG for ALL randomness
- Do NOT import random or numpy.random
- You may keep internal state on the Bot instance
- Always return a valid Move enum
"""

from engine.judge import Move, MOVES


class Bot:
    # This name is shown on the leaderboard
    name = "TemplateBot"

    def __init__(self):
        # Persistent state across rounds in a match
        self.round_count = 0

    def play(self, state: dict, rng):
        """
        Required interface:
            play(state: dict, rng) -> dict

        state may include:
            - opponent_last_visible: Move | None
            - round: int
            - score: int

        rng:
            - Deterministic random number generator
            - Supports .choice(), .randint(), .random(), etc.
        """

        self.round_count += 1

        # --- Example: uniform random move ---
        move = rng.choice(MOVES)

        return {
            "real_move": move
        }

    def request_shadow_move(self, state: dict):
        """
        Optional interface.
        Return (use_shadow: bool, shadow_move: Move | None)

        If you don't use deception, always return:
            (False, None)
        """
        return False, None
