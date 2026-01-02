"""
Replay Validator for Chaos League

Validates that any completed match can be fully reproduced
from logs, RNG seeds, and submitted bot files.
"""

import json
import pathlib
from engine.match import run_match
from engine.logger import init_logging
from engine.rng import make_rng
from engine.bot_loader import load_bot
from engine.judge import Move
from config import DECEPTION_TOKENS, ROUNDS

def _move_from_name(name: str) -> Move:
    """
    Converts a move name string back into a Move enum.
    """
    try:
        return Move[name]
    except KeyError:
        raise RuntimeError(f"Invalid move name in log: {name}")


def validate_match_replay(match_metadata_path: pathlib.Path, bots_dir: pathlib.Path):
    """
    Replays a match from log metadata and validates round outcomes.

    match_metadata_path: path to JSON file containing:
        {
            "bot_a": "name",
            "bot_b": "name",
            "score_a": ...,
            "score_b": ...,
            "tokens_used_a": ...,
            "tokens_used_b": ...,
            "rounds_log": "path/to/rounds.jsonl"
        }
    bots_dir: path to directory containing submitted bot files
    """

    # --- Load metadata ---
    with open(match_metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    bot_a_name = metadata["bot_a"]
    bot_b_name = metadata["bot_b"]
    rounds_log_path = pathlib.Path(metadata["rounds_log"])

    # --- Load bots ---
    bot_a_file = bots_dir / f"{bot_a_name}.py"
    bot_b_file = bots_dir / f"{bot_b_name}.py"
    bot_a = load_bot(bot_a_file)
    bot_b = load_bot(bot_b_file)

    # --- Read logged rounds ---
    with open(rounds_log_path, "r", encoding="utf-8") as f:
        logged_rounds = [json.loads(line) for line in f]

    # --- Replay match round by round ---
    rng_a, rng_b = make_rng(bot_a_name, bot_b_name)
    last_real_a = last_real_b = None
    last_visible_a = last_visible_b = None
    tokens_a = tokens_b = DECEPTION_TOKENS

    for round_idx, log_entry in enumerate(logged_rounds, start=1):
        # Build bot states
        state_a = {
            "round": round_idx,
            "opponent_last_visible": last_visible_b,
            "self_last_real": last_real_a,
            "opponent_deception_bucket": log_entry["b_bucket"],
        }
        state_b = {
            "round": round_idx,
            "opponent_last_visible": last_visible_a,
            "self_last_real": last_real_b,
            "opponent_deception_bucket": log_entry["a_bucket"],
        }

        # Replay bot decisions
        out_a = bot_a.play(state_a, rng_a)
        out_b = bot_b.play(state_b, rng_b)

        real_a = out_a["real_move"]
        real_b = out_b["real_move"]

        # Validate type
        if not isinstance(real_a, Move) or not isinstance(real_b, Move):
            raise RuntimeError(f"Bot returned invalid move type at round {round_idx}")

        # Convert logged moves to Move enum
        logged_real_a = _move_from_name(log_entry["a_real"])
        logged_real_b = _move_from_name(log_entry["b_real"])

        # Compare
        if real_a != logged_real_a:
            raise RuntimeError(f"Replay mismatch round {round_idx} for {bot_a_name}: {real_a} != {logged_real_a}")
        if real_b != logged_real_b:
            raise RuntimeError(f"Replay mismatch round {round_idx} for {bot_b_name}: {real_b} != {logged_real_b}")

        # --- Shadow logic (for bucket tracking) ---
        shadow_a = out_a.get("shadow", False)
        shadow_b = out_b.get("shadow", False)
        if shadow_a and tokens_a > 0:
            tokens_a -= 1
        if shadow_b and tokens_b > 0:
            tokens_b -= 1

        # Update history
        last_real_a = real_a
        last_real_b = real_b
        last_visible_a = _move_from_name(log_entry["a_visible"])
        last_visible_b = _move_from_name(log_entry["b_visible"])

    print(f"Replay successful: {bot_a_name} vs {bot_b_name}")
    return True
