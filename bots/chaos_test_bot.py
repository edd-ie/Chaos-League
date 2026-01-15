"""
Chaos Test Bot.
Uses deception sparingly and deterministically via engine RNG.
"""

from engine.judge import Move

class Bot:
    name = "ChaosTestBot"

    def play(self, state, rng):
        # Random real move (legal RNG)
        real_move = rng.choice(list(Move))

        # Attempt shadow only when the opponent is "LOW" or worse
        use_shadow = (
            state["opponent_deception_bucket"] in {"LOW", "EMPTY"}
            and rng.random() < 0.3
        )

        if use_shadow:
            shadow_move = rng.choice(list(Move))
            return {
                "real_move": real_move,
                "shadow": True,
                "shadow_move": shadow_move,
            }

        return {
            "real_move": real_move,
            "shadow": False,
        }
