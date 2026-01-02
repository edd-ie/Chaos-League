"""
Authoritative RPSLS payoff logic for Chaos League.
This module must remain deterministic and stateless.
"""

# Outcome matrix:
# +1 = win
# -1 = loss
#  0 = draw


from enum import Enum, auto

class Move(Enum):
    ROCK = auto()
    PAPER = auto()
    SCISSORS = auto()
    LIZARD = auto()
    SPOCK = auto()

# List of all moves
MOVES = list(Move)

# Outcome matrix
WIN_MAP = {
    Move.ROCK:     {Move.SCISSORS, Move.LIZARD},
    Move.PAPER:    {Move.ROCK, Move.SPOCK},
    Move.SCISSORS: {Move.PAPER, Move.LIZARD},
    Move.LIZARD:   {Move.PAPER, Move.SPOCK},
    Move.SPOCK:    {Move.ROCK, Move.SCISSORS},
}



def resolve_round(move_a: Move, move_b: Move):
    """
    Resolves a single round of RPSLS.
    Returns:
        (delta_a, delta_b)
        where each delta ∈ {+1, 0, -1}
    """

    if move_a == move_b:
        return 0, 0

    if move_b in WIN_MAP[move_a]:
        return +1, -1

    if move_a in WIN_MAP[move_b]:
        return -1, +1

    # This should never happen if moves are validated upstream
    raise RuntimeError(f"Unresolvable move pair: {move_a} vs {move_b}")
