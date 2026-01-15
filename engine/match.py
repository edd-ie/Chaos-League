"""
Chaos League Match Engine

Features:
- Runs a single match between two bots
- Enforces per-move timeouts to prevent infinite loops
- Handles deception tokens and shadow moves
- Tracks scores and updates tournament leaderboard
- Fully compatible with Move enums and logging system
"""

import pathlib
import json

from collections import Counter
from engine.judge import resolve_round, Move, MOVES
from engine.rng import make_rng
from engine.logger import log_round, log_match_summary, _RESULTS_ROOT
from config import ROUNDS, DECEPTION_TOKENS, COMPETITION, SHADOW_REJECT_PROB

from engine.bot_runner import safe_play, safe_shadow

# Buckets for deception tokens (individual pools)
BUCKETS = [
    ("HIGH", 40),
    ("MEDIUM", 20),
    ("LOW", 1),
    ("EMPTY", 0),
]


def deception_bucket(tokens_left: int) -> str:
    """Return a string representing the token "level" for display/logging."""
    for name, threshold in BUCKETS:
        if tokens_left >= threshold:
            return name
    return "EMPTY"


def validate_move(move):
    """Ensure a move is a valid Move enum."""
    if not isinstance(move, Move):
        raise RuntimeError(f"Invalid move type: {move}")
    if move not in MOVES:
        raise RuntimeError(f"Invalid move value: {move}")


def run_match(bot_a, bot_b, name_a: str, name_b: str, tournament_stats: dict = None):
    """Run a single Chaos League match between two bots."""
    rng_a, rng_b = make_rng(name_a, name_b)

    score_a = score_b = 0
    tokens_a = tokens_b = DECEPTION_TOKENS
    last_real_a = last_real_b = None
    last_visible_a = last_visible_b = None
    tokens_used_a = tokens_used_b = 0

    move_counts_a = Counter()
    move_counts_b = Counter()

    for round_idx in range(1, ROUNDS + 1):
        state_a = {
            "round": round_idx,
            "opponent_last_visible": last_visible_b.name if last_visible_b else None,
            "self_last_real": last_real_a.name if last_real_a else None,
            "opponent_deception_bucket": deception_bucket(tokens_b),
        }
        state_b = {
            "round": round_idx,
            "opponent_last_visible": last_visible_a.name if last_visible_a else None,
            "self_last_real": last_real_b.name if last_real_b else None,
            "opponent_deception_bucket": deception_bucket(tokens_a),
        }

        out_a = safe_play(bot_a, state_a, rng_a)
        out_b = safe_play(bot_b, state_b, rng_b)

        real_a = out_a.get("real_move", MOVES[0])
        real_b = out_b.get("real_move", MOVES[0])

        validate_move(real_a)
        validate_move(real_b)

        shadow_a = shadow_b = False
        visible_a, visible_b = real_a, real_b

        shadow_req_a, shadow_move_a = safe_shadow(bot_a, state_a)
        shadow_req_b, shadow_move_b = safe_shadow(bot_b, state_b)

        if shadow_req_a and tokens_a > 0 and shadow_move_a is not None:
            if rng_a.random() > SHADOW_REJECT_PROB:
                validate_move(shadow_move_a)
                visible_a = shadow_move_a
                tokens_a -= 1
                tokens_used_a += 1
                shadow_a = True

        if shadow_req_b and tokens_b > 0 and shadow_move_b is not None:
            if rng_b.random() > SHADOW_REJECT_PROB:
                validate_move(shadow_move_b)
                visible_b = shadow_move_b
                tokens_b -= 1
                tokens_used_b += 1
                shadow_b = True

        delta_a, delta_b = resolve_round(real_a, real_b)
        score_a += delta_a
        score_b += delta_b

        move_counts_a[real_a] += 1
        move_counts_b[real_b] += 1

        if COMPETITION:
            log_round({
                "round": round_idx,
                "bot_a": name_a,
                "bot_b": name_b,
                "a_real": real_a.name,
                "b_real": real_b.name,
                "a_visible": visible_a.name,
                "b_visible": visible_b.name,
                "a_shadow": shadow_a,
                "b_shadow": shadow_b,
                "a_bucket": deception_bucket(tokens_a),
                "b_bucket": deception_bucket(tokens_b),
            })

        last_real_a, last_real_b = real_a, real_b
        last_visible_a, last_visible_b = visible_a, visible_b

    # --- Match summary ---
    summary = {
        "bot_a": name_a,
        "bot_b": name_b,
        "score_a": score_a,
        "score_b": score_b,
        "tokens_used_a": tokens_used_a,
        "tokens_used_b": tokens_used_b,
        "shadow_efficiency_a": (tokens_used_a / max(1, DECEPTION_TOKENS)),
        "shadow_efficiency_b": (tokens_used_b / max(1, DECEPTION_TOKENS)),
        "moves_a": {m.name: c for m, c in move_counts_a.items()},
        "moves_b": {m.name: c for m, c in move_counts_b.items()},
    }

    if COMPETITION:
        log_match_summary(summary)

    if tournament_stats is not None:
        for bot_name, score, tokens in [
            (name_a, score_a, tokens_used_a),
            (name_b, score_b, tokens_used_b),
        ]:
            s = tournament_stats.setdefault(bot_name, {
                "score": 0, "matches": 0, "wins": 0,
                "losses": 0, "draws": 0, "shadow_used": 0
            })
            s["score"] += score
            s["matches"] += 1
            s["shadow_used"] += tokens

        if score_a > score_b:
            tournament_stats[name_a]["wins"] += 1
            tournament_stats[name_b]["losses"] += 1
        elif score_b > score_a:
            tournament_stats[name_b]["wins"] += 1
            tournament_stats[name_a]["losses"] += 1
        else:
            tournament_stats[name_a]["draws"] += 1
            tournament_stats[name_b]["draws"] += 1

    if _RESULTS_ROOT:
        replay_meta_path = _RESULTS_ROOT / "metadata" / f"replay_{name_a}_vs_{name_b}.json"
        replay_meta = {
            "bot_a": name_a,
            "bot_b": name_b,
            "score_a": score_a,
            "score_b": score_b,
            "tokens_used_a": tokens_used_a,
            "tokens_used_b": tokens_used_b,
            "rounds_log": str(_RESULTS_ROOT / "raw" / "rounds.jsonl"),
        }
        with open(replay_meta_path, "w", encoding="utf-8") as f:
            json.dump(replay_meta, f, indent=2)

    return summary
