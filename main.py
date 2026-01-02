#!/usr/bin/env python3

import sys
import pathlib
import importlib.util
import hashlib
from datetime import datetime

from config import COMPETITION
from engine.match import run_match
from engine.logger import (
    init_logging,
    log_match_summary,
    finalize_logging,
    log_metadata,
)
from engine.rng import verify_rng_compliance


# -------------------------------
# Paths
# -------------------------------

ROOT = pathlib.Path(__file__).parent.resolve()
BOTS_DIR = ROOT / "bots"
RESULTS_DIR = ROOT / "results"


# -------------------------------
# Bot Loading
# -------------------------------

def load_bot(bot_path: pathlib.Path):
    """
    Dynamically loads a bot module.
    Enforces presence of a `play(state, rng)` function.
    """
    spec = importlib.util.spec_from_file_location(bot_path.stem, bot_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "play"):
        raise RuntimeError(f"{bot_path.name} missing required play(state, rng)")

    return module


def hash_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


# -------------------------------
# Submission Lock-In
# -------------------------------

def snapshot_bot_hashes(bot_files):
    return {
        bot.name: hash_file(bot)
        for bot in bot_files
    }


# -------------------------------
# Tournament Driver
# -------------------------------

def main():
    print("=== CHAOS LEAGUE TOURNAMENT ENGINE ===")

    # Validate bot directory
    if not BOTS_DIR.exists():
        raise RuntimeError("bots/ directory not found")

    bot_files = sorted(BOTS_DIR.glob("*.py"))
    if len(bot_files) < 2:
        raise RuntimeError("At least two bots are required")

    print(f"Found {len(bot_files)} bots")

    # Load bots
    bots = {}
    for bot_file in bot_files:
        bots[bot_file.stem] = load_bot(bot_file)

    # RNG compliance check (no global random abuse)
    for name, bot in bots.items():
        verify_rng_compliance(bot, name)

    # Competition lock-in
    bot_hashes = snapshot_bot_hashes(bot_files)

    if COMPETITION:
        print("COMPETITION MODE ENABLED")
        RESULTS_DIR.mkdir(exist_ok=True)

        log_metadata({
            "timestamp": datetime.utcnow().isoformat(),
            "bot_hashes": bot_hashes,
            "competition": True,
        })
    else:
        print("SIMULATION MODE (no authoritative logging)")

    # Initialize logger
    init_logging(competition=COMPETITION)

    # Round-robin tournament
    bot_names = list(bots.keys())
    for i in range(len(bot_names)):
        for j in range(i + 1, len(bot_names)):
            a_name = bot_names[i]
            b_name = bot_names[j]

            print(f"Running match: {a_name} vs {b_name}")

            result = run_match(
                bot_a=bots[a_name],
                bot_b=bots[b_name],
                name_a=a_name,
                name_b=b_name,
            )

            if COMPETITION:
                log_match_summary(result)

    finalize_logging()
    print("=== TOURNAMENT COMPLETE ===")


# -------------------------------
# Entry Point
# -------------------------------

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("FATAL ERROR:", e)
        sys.exit(1)
