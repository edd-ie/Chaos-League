"""
Chaos League Tournament Runner (Sequential, Deterministic, Safe)

Features:
- Multiple matches per bot pair
- Fully compatible with safe_play multiprocessing timeouts
- Deterministic RNG seeding per match
- Shadow-move efficiency tracking
- Tournament leaderboard
- Automatic leaderboard snapshots
"""
import json
import pathlib
import itertools
from collections import defaultdict

from engine import logger
from engine.bot_loader import load_bot
from engine.match import run_match
from engine.rng import make_rng
from config import (
    COMPETITION,
    MATCHES_PER_PAIR,
    SEED_SALT,
    LEADERBOARD_SNAPSHOT_INTERVAL,
)

BOTS_DIR = pathlib.Path("bots")


def load_all_bot_names():
    bots = [f.stem for f in BOTS_DIR.glob("*.py")]
    if not bots:
        raise RuntimeError("No bots found in 'bots/'")
    return bots


def print_leaderboard(stats: dict):
    if not stats:
        print("No stats to display")
        return

    leaderboard = sorted(stats.items(), key=lambda x: x[1]["score"], reverse=True)

    print(
        f"{'Bot':20} {'Score':>6} {'Matches':>7} "
        f"{'Wins':>5} {'Losses':>6} {'Draws':>5} "
        f"{'Shadow':>6} {'ShadowEff':>10}"
    )

    for bot, d in leaderboard:
        # Shadow efficiency as percentage of shadow tokens used per match
        eff = d["shadow_efficiency"] / max(1, d["matches"])
        print(
            f"{bot:20} {d['score']:6} {d['matches']:7} "
            f"{d['wins']:5} {d['losses']:6} {d['draws']:5} "
            f"{d['shadow_used']:6} {eff:10.2%}"
        )


def run_tournament():
    logger.init_logging(COMPETITION)

    bot_names = load_all_bot_names()

    stats = defaultdict(lambda: {
        "score": 0,
        "matches": 0,
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "shadow_used": 0,
        "shadow_efficiency": 0.0,
    })

    matches = []
    for a, b in itertools.combinations(bot_names, 2):
        for match_idx in range(1, MATCHES_PER_PAIR + 1):
            matches.append((a, b, match_idx))

    print(f"Total matches to run: {len(matches)}")

    completed = 0
    rng_log = []

    for name_a, name_b, match_idx in matches:
        try:
            bot_a = load_bot(BOTS_DIR / f"{name_a}.py")
            bot_b = load_bot(BOTS_DIR / f"{name_b}.py")

            seed_a = f"{name_a}_{name_b}_{match_idx}_A_{SEED_SALT}"
            seed_b = f"{name_b}_{name_a}_{match_idx}_B_{SEED_SALT}"
            make_rng(seed_a, seed_b)

            summary = run_match(bot_a, bot_b, name_a, name_b)

            # --- Write per-match replay metadata ---
            if COMPETITION:
                results_root = logger._RESULTS_ROOT
                if results_root is None:
                    raise RuntimeError("Logging not initialized")
                metadata_path = results_root / "metadata" / f"replay_{name_a}_vs_{name_b}.json"
                replay_meta = {
                    "bot_a": name_a,
                    "bot_b": name_b,
                    "score_a": summary["score_a"],
                    "score_b": summary["score_b"],
                    "tokens_used_a": summary["tokens_used_a"],
                    "tokens_used_b": summary["tokens_used_b"],
                    "shadow_efficiency_a": summary.get("shadow_efficiency_a", 0.0),
                    "shadow_efficiency_b": summary.get("shadow_efficiency_b", 0.0),
                    "rounds_log": str(results_root / "raw" / "rounds.jsonl")
                }
                with open(metadata_path, "w", encoding="utf-8") as f:
                    json.dump(replay_meta, f, indent=2)

        except Exception as e:
            print(f"[ERROR] Match {name_a} vs {name_b} failed: {e}")
            continue

        # --- Update tournament stats ---
        for bot_key, side in [(summary["bot_a"], "a"), (summary["bot_b"], "b")]:
            s = stats[bot_key]
            score = summary[f"score_{side}"]
            tokens_used = summary.get(f"tokens_used_{side}", 0)
            shadow_eff = summary.get(f"shadow_efficiency_{side}", 0.0)

            s["score"] += score
            s["matches"] += 1
            s["wins"] += score > 0
            s["losses"] += score < 0
            s["draws"] += score == 0
            s["shadow_used"] += tokens_used
            # Update cumulative shadow efficiency as total shadow tokens per match
            s["shadow_efficiency"] = (s["shadow_efficiency"] * (s["matches"] - 1) + shadow_eff) / s["matches"]

        rng_log.append({
            "bot_a": name_a,
            "bot_b": name_b,
            "rng_seed_a": seed_a,
            "rng_seed_b": seed_b,
            "match_index": match_idx,
        })

        completed += 1

        if completed % LEADERBOARD_SNAPSHOT_INTERVAL == 0:
            print(f"\n--- Leaderboard Snapshot after {completed} matches ---")
            print_leaderboard(stats)

            if COMPETITION:
                logger.log_metadata({
                    "snapshot_after_matches": completed,
                    "snapshot_stats": dict(stats),
                })

    if COMPETITION:
        logger.log_metadata({
            "final_tournament_stats": dict(stats),
            "rng_seeds": rng_log,
            "matches_per_pair": MATCHES_PER_PAIR,
        })

    logger.finalize_logging()

    print("\n--- Tournament Complete ---")
    print_leaderboard(stats)


if __name__ == "__main__":
    run_tournament()
