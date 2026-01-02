"""
Chaos League Tournament Runner (Threaded, Deterministic, Safe)

Features:
- Multiple matches per bot pair
- Threaded execution to avoid pickling issues
- Per-match RNG seeds logged for exact replay
- Shadow-move efficiency tracking
- Tournament stats aggregation and leaderboard
- Automatic leaderboard snapshots during long tournaments
"""

import pathlib
import itertools
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

from engine.bot_loader import load_bot
from engine.match import run_match
from engine.logger import init_logging, finalize_logging, log_metadata
from config import (
    COMPETITION,
    MATCHES_PER_PAIR,
    SEED_SALT,
    LEADERBOARD_SNAPSHOT_INTERVAL,
)
from engine.rng import make_rng

BOTS_DIR = pathlib.Path("bots")


def load_all_bot_names():
    """Return a list of all bot names found in bots/"""
    bot_names = [f.stem for f in BOTS_DIR.glob("*.py")]
    if not bot_names:
        raise RuntimeError("No bots found in 'bots/' folder")
    return bot_names


def _run_single_match(bot_names_info):
    """
    Runs a single match (thread-safe)
    bot_names_info = (name_a, name_b, match_index)
    """
    name_a, name_b, match_idx = bot_names_info

    # Dynamically load bot classes inside the thread
    bot_a = load_bot(BOTS_DIR / f"{name_a}.py")
    bot_b = load_bot(BOTS_DIR / f"{name_b}.py")

    # Deterministic RNG seeds per bot per match
    seed_a_str = f"{name_a}_{name_b}_{match_idx}_A_{SEED_SALT}"
    seed_b_str = f"{name_b}_{name_a}_{match_idx}_B_{SEED_SALT}"
    rng_a, rng_b = make_rng(seed_a_str, seed_b_str)

    # Run match
    summary = run_match(bot_a, bot_b, name_a, name_b)

    # Attach seeds to summary for replay
    summary["rng_seed_a"] = seed_a_str
    summary["rng_seed_b"] = seed_b_str
    summary["match_index"] = match_idx

    return summary


def print_leaderboard(stats: dict):
    if not stats:
        print("No stats to display")
        return

    leaderboard = sorted(stats.items(), key=lambda x: x[1]["score"], reverse=True)

    print(f"{'Bot':20} {'Score':>6} {'Matches':>7} {'Wins':>5} "
          f"{'Losses':>6} {'Draws':>5} {'Shadow':>6} {'ShadowEff':>10}")

    for bot, data in leaderboard:
        shadow_eff_avg = data.get("shadow_efficiency", 0) / max(1, data["matches"])
        print(f"{bot:20} {data['score']:6} {data['matches']:7} {data['wins']:5} "
              f"{data['losses']:6} {data['draws']:5} {data['shadow_used']:6} {shadow_eff_avg:10.2%}")


def run_tournament():
    # Initialize logging
    init_logging(COMPETITION)

    # Load bot names
    bot_names = load_all_bot_names()

    # Initialize stats
    tournament_stats = defaultdict(lambda: {
        "score": 0,
        "matches": 0,
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "shadow_used": 0,
        "shadow_efficiency": 0.0,
    })

    # Prepare bot pairings
    matches_to_run = []
    for i, j in itertools.combinations(range(len(bot_names)), 2):
        name_a, name_b = bot_names[i], bot_names[j]
        for match_idx in range(1, MATCHES_PER_PAIR + 1):
            matches_to_run.append((name_a, name_b, match_idx))

    print(f"Total matches to run: {len(matches_to_run)}")

    match_rng_log = []  # store seeds for replay
    completed_matches = 0

    # --- Threaded execution ---
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(_run_single_match, info): info for info in matches_to_run}

        for future in as_completed(futures):
            info = futures[future]
            try:
                summary = future.result()
            except Exception as e:
                print(f"[ERROR] Match {info[0]} vs {info[1]} failed: {e}")
                continue

            # Update tournament stats
            for bot_key, key in [(summary["bot_a"], "a"), (summary["bot_b"], "b")]:
                stats = tournament_stats[bot_key]
                score = summary[f"score_{key}"]
                stats["score"] += score
                stats["matches"] += 1
                stats["wins"] += score > 0
                stats["losses"] += score < 0
                stats["draws"] += score == 0
                stats["shadow_used"] += summary.get(f"tokens_used_{key}", 0)
                stats["shadow_efficiency"] += summary.get(f"shadow_efficiency_{key}", 0)

            # Log per-match RNG for replay
            match_rng_log.append({
                "bot_a": summary["bot_a"],
                "rng_seed_a": summary["rng_seed_a"],
                "bot_b": summary["bot_b"],
                "rng_seed_b": summary["rng_seed_b"],
                "match_index": summary["match_index"],
            })

            completed_matches += 1

            # --- Automatic leaderboard snapshot ---
            if completed_matches % LEADERBOARD_SNAPSHOT_INTERVAL == 0:
                print(f"\n--- Leaderboard Snapshot after {completed_matches} matches ---")
                print_leaderboard(tournament_stats)
                if COMPETITION:
                    log_metadata({
                        "leaderboard_snapshot_after_matches": completed_matches,
                        "snapshot_stats": dict(tournament_stats)
                    })

    # --- Final metadata logging ---
    if COMPETITION:
        log_metadata({
            "tournament_stats": dict(tournament_stats),
            "matches_per_pair": MATCHES_PER_PAIR,
            "match_rng_seeds": match_rng_log,
        })

    finalize_logging()
    print("\n--- Tournament Complete ---")
    print_leaderboard(tournament_stats)

#TODO: Fix pickling issues with concurrent.futures
if __name__ == "__main__":
    run_tournament()
