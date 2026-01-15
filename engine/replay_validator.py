"""
Replay Validator for Chaos League

Validates that any completed match can be fully reproduced
from logs, RNG seeds, and submitted bot files.
"""

import json
import pathlib
import random
from engine.bot_loader import load_bot
from engine.judge import Move, MOVES
from config import DECEPTION_TOKENS

def _move_from_name(name: str) -> Move:
    """Converts a move name string back into a Move enum."""
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
            "rounds_log": "path/to/rounds.jsonl"
        }
    bots_dir: path to directory containing submitted bot files
    """

    # --- Load metadata ---
    with open(match_metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    bot_a_name = metadata["bot_a"]
    bot_b_name = metadata["bot_b"]
    
    # Calculate rounds_log_path relative to the metadata file's location
    # instead of trusting the potentially absolute/stale path in the JSON.
    tournament_root = match_metadata_path.parents[1]
    rounds_log_path = tournament_root / "raw" / "rounds.jsonl"

    # --- Load bots ---
    bot_a_file = bots_dir / f"{bot_a_name}.py"
    bot_b_file = bots_dir / f"{bot_b_name}.py"
    bot_a = load_bot(bot_a_file)
    bot_b = load_bot(bot_b_file)

    # --- Read logged rounds ---
    with open(rounds_log_path, "r", encoding="utf-8") as f:
        logged_rounds = [json.loads(line) for line in f]

    # Filter rounds for this bot pair
    match_rounds = [
        r for r in logged_rounds
        if r["bot_a"] == bot_a_name and r["bot_b"] == bot_b_name
    ]

    last_real_a = last_real_b = None
    last_visible_a = last_visible_b = None
    tokens_a = tokens_b = DECEPTION_TOKENS

    # Initialize a deterministic RNG for replay consistency.
    # Ideally, the seed should come from the metadata if available.
    seed = metadata.get("seed", 42)
    rng_a = random.Random(f"{seed}_a")
    rng_b = random.Random(f"{seed}_b")

    for round_idx, log_entry in enumerate(match_rounds, start=1):
        # --- Convert logged moves to Move enums ---
        logged_real_a = _move_from_name(log_entry["a_real"])
        logged_real_b = _move_from_name(log_entry["b_real"])
        logged_visible_a = _move_from_name(log_entry["a_visible"])
        logged_visible_b = _move_from_name(log_entry["b_visible"])

        # --- Build bot states ---
        state_a = {
            "round": round_idx,
            "opponent_last_visible": last_visible_b.name if last_visible_b else None,
            "self_last_real": last_real_a.name if last_real_a else None,
            "opponent_deception_bucket": log_entry["b_bucket"],
        }
        state_b = {
            "round": round_idx,
            "opponent_last_visible": last_visible_a.name if last_visible_a else None,
            "self_last_real": last_real_b.name if last_real_b else None,
            "opponent_deception_bucket": log_entry["a_bucket"],
        }

        # --- Call bot play with valid RNG ---
        out_a = bot_a.play(state_a, rng=rng_a)
        out_b = bot_b.play(state_b, rng=rng_b)

        real_a = out_a.get("real_move", None)
        real_b = out_b.get("real_move", None)

        if not isinstance(real_a, Move) or not isinstance(real_b, Move):
            raise RuntimeError(f"Bot returned invalid move type at round {round_idx}")

        # --- Compare with logged moves ---
        if real_a != logged_real_a:
            raise RuntimeError(
                f"Replay mismatch round {round_idx} for {bot_a_name}: {real_a} != {logged_real_a}"
            )
        if real_b != logged_real_b:
            raise RuntimeError(
                f"Replay mismatch round {round_idx} for {bot_b_name}: {real_b} != {logged_real_b}"
            )

        # --- Shadow token bookkeeping ---
        shadow_a = out_a.get("shadow", False)
        shadow_b = out_b.get("shadow", False)
        if shadow_a and tokens_a > 0:
            tokens_a -= 1
        if shadow_b and tokens_b > 0:
            tokens_b -= 1

        # --- Update history ---
        last_real_a = real_a
        last_real_b = real_b
        last_visible_a = logged_visible_a
        last_visible_b = logged_visible_b

    print(f"Replay successful: {bot_a_name} vs {bot_b_name}")
    return True
